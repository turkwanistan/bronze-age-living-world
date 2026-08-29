#!/usr/bin/env python3
"""Validate repeated fresh cognition against byte-identical sealed packets.

Validation-only. Disposable branches are rebuilt from accepted state and never become
canonical history. Frequencies are model diagnostics, never historical probabilities.
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from build_fresh_cognition_pairs import build as build_pairs


def clean_sqlite(path: Path) -> None:
    for p in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if p.exists():
            p.unlink()


def copy_sqlite(source: Path, dest: Path) -> None:
    clean_sqlite(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def action_family(envelope: dict) -> str:
    actions = envelope.get("proposed_actions", [])
    if not actions:
        return "none"
    kinds = [a.get("type", "unknown") for a in actions]
    return kinds[0] if len(set(kinds)) == 1 else "+".join(kinds)


def actor_household_resources(db: WorldDB, actor_id: str) -> dict[str, float]:
    hid = db.scalar(
        "SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL",
        (actor_id,),
    )
    return {
        r["resource_type"]: float(r["amount"])
        for r in db.all(
            "SELECT resource_type,amount FROM resource_stocks WHERE household_id=? ORDER BY resource_type",
            (hid,),
        )
    }


def run_validation(source: Path, property_source: Path, attempts_path: Path, root: Path, workdir: Path) -> dict:
    attempts_doc = json.loads(attempts_path.read_text())
    attempts = attempts_doc["packets"]
    bases_dir = workdir / "bases"
    base_manifest = build_pairs(source, property_source, root, bases_dir)

    results: dict[str, list[dict]] = {}
    summaries: dict[str, dict] = {}
    for packet_name, packet_attempts in attempts.items():
        if packet_name not in base_manifest:
            raise KeyError(f"unknown packet {packet_name}")
        meta = base_manifest[packet_name]
        base_db = Path(meta["db"])
        base_job_id = meta["job_id"]
        base_hash = meta["packet"]["job_id"] and None
        packet_results = []
        for idx, raw_env in enumerate(packet_attempts, start=1):
            dest = workdir / "attempts" / f"{packet_name}__attempt{idx}.sqlite"
            copy_sqlite(base_db, dest)
            env = json.loads(json.dumps(raw_env))
            env["decision_id"] = f"VAL-V018-{packet_name}-A{idx}"
            with WorldDB(dest) as db:
                job = db.one("SELECT * FROM cognition_jobs WHERE job_id=?", (base_job_id,))
                assert job and job["status"] == "pending"
                packet = compile_packet(db, base_job_id)
                if base_hash is None:
                    base_hash = job["packet_hash"]
                assert job["packet_hash"] == base_hash
                before = actor_household_resources(db, env["actor_id"])
                eng = WorldEngine(db, job["run_id"])
                vr = eng.submit_decision(base_job_id, env)
                after = actor_household_resources(db, env["actor_id"])
                packet_results.append(
                    {
                        "attempt": idx,
                        "ok": vr.ok,
                        "errors": vr.errors,
                        "decision_id": env["decision_id"],
                        "action_family": action_family(env),
                        "action_types": [a.get("type") for a in env.get("proposed_actions", [])],
                        "selected_intent": env.get("selected_intent"),
                        "declared_uncertainty": env.get("declared_uncertainty"),
                        "packet_hash": job["packet_hash"],
                        "household_resources_before": before,
                        "household_resources_after": after,
                        "ritual_goods_cost": sum(float(a.get("ritual_goods_cost", 0) or 0) for a in env.get("proposed_actions", [])),
                        "accepted_jobs": int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='accepted'", (job["run_id"],)) or 0),
                        "rejected_jobs": int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='rejected'", (job["run_id"],)) or 0),
                        "negative_resources": int(db.scalar("SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9") or 0),
                    }
                )
        results[packet_name] = packet_results
        counts = Counter(r["action_family"] for r in packet_results)
        summaries[packet_name] = {
            "packet_hash": base_hash,
            "attempts": len(packet_results),
            "action_family_counts": dict(sorted(counts.items())),
            "distinct_action_families": len(counts),
            "dominant_action_family": counts.most_common(1)[0][0],
            "all_valid": all(r["ok"] for r in packet_results),
        }

    adequate_costs = [r["ritual_goods_cost"] for r in results["p10_illness_adequate"]]
    depleted_costs = [r["ritual_goods_cost"] for r in results["p10_illness_depleted"]]
    buffered_families = [r["action_family"] for r in results["p7_recycling_buffered"]]
    exhausted_families = [r["action_family"] for r in results["p7_recycling_near_exhausted"]]
    single_families = [r["action_family"] for r in results["p3_shipping_single_report"]]
    discordant_families = [r["action_family"] for r in results["p3_shipping_discordant_reports"]]

    all_attempts = [r for xs in results.values() for r in xs]
    checks = {
        "all_18_decisions_valid": len(all_attempts) == 18 and all(r["ok"] for r in all_attempts),
        "zero_rejected_jobs": all(r["rejected_jobs"] == 0 for r in all_attempts),
        "zero_negative_resources": all(r["negative_resources"] == 0 for r in all_attempts),
        "identical_packet_hash_within_each_packet": all(len({r["packet_hash"] for r in xs}) == 1 for xs in results.values()),
        "p10_stock_constraint_visible_in_all_attempts": min(adequate_costs) > 0.05 and max(depleted_costs) <= 0.05,
        "p7_control_stronger_than_within_packet_noise": set(buffered_families) == {"recycle_finished_metalwork"} and set(exhausted_families) == {"wait"},
        "p3_single_report_consistently_seeks_information": set(single_families) == {"send_message"},
        "p3_discordant_reports_remain_epistemically_conservative": set(discordant_families) <= {"wait", "send_message"},
        "p3_control_changes_dominant_action_family": summaries["p3_shipping_single_report"]["dominant_action_family"] == "send_message" and summaries["p3_shipping_discordant_reports"]["dominant_action_family"] == "wait",
    }
    variable_packets = sorted(k for k, v in summaries.items() if v["distinct_action_families"] > 1)
    out = {
        "mode": "repeated_fresh_cognition_same_packet_validation",
        "attempts_per_packet": attempts_doc["attempts_per_packet"],
        "packet_count": len(results),
        "total_attempts": len(all_attempts),
        "results": results,
        "packet_summaries": summaries,
        "variable_action_family_packets": variable_packets,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_notice": "Repeated-choice frequencies measure this cognition configuration only and are not historical probabilities.",
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-db", required=True)
    ap.add_argument("--property-source-db", required=True)
    ap.add_argument("--attempts", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--json-out", required=True)
    ns = ap.parse_args()
    out = run_validation(Path(ns.source_db), Path(ns.property_source_db), Path(ns.attempts), Path(ns.root), Path(ns.workdir))
    Path(ns.json_out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"total_attempts": out["total_attempts"], "variable_action_family_packets": out["variable_action_family_packets"], "checks": out["checks"], "all_checks_pass": out["all_checks_pass"]}, indent=2))
    raise SystemExit(0 if out["all_checks_pass"] else 2)


if __name__ == "__main__":
    main()
