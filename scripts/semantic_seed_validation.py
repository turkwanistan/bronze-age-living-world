#!/usr/bin/env python3
"""Validation-only semantic policy transfer across deterministic RNG seeds.

This is NOT replay and NOT a substitute for fresh cognition. It holds the accepted
source run's semantic decision policy approximately constant when the destination
seed exposes the same actor + scene trigger, while rebinding packet-local knowledge
and run-derived stake IDs. It fails closed on unmatched scenes or rejected actions.

The sole repeat-template fallback is same-actor ``minor_illness``: if a destination
seed generates more minor-illness episodes for an actor than the source run, the
actor's latest accepted minor-illness response is reused. The normal validator still
has final authority and may reject it if destination resources/context no longer fit.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import json

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture


def _flatten(obj, path=()):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, path + (k,)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, path + (i,)))
    else:
        out[path] = obj
    return out


def _getpath(obj, path):
    cur = obj
    try:
        for p in path:
            cur = cur[p]
        return cur
    except Exception:
        return None


def _rebase_scalar(value, source_stakes, dest_stakes):
    for path, source_value in _flatten(source_stakes).items():
        if value == source_value:
            dest_value = _getpath(dest_stakes, path)
            if dest_value is not None and dest_value != source_value:
                return dest_value
    return value


def _rebase_obj(obj, source_stakes, dest_stakes):
    if isinstance(obj, dict):
        return {k: _rebase_obj(v, source_stakes, dest_stakes) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rebase_obj(v, source_stakes, dest_stakes) for v in obj]
    return _rebase_scalar(obj, source_stakes, dest_stakes)


def _load_library(source: WorldDB):
    rows = source.all(
        "SELECT d.rowid AS decision_rowid,d.envelope_json,j.actor_person_id,j.packet_json,"
        "s.trigger_type,d.applied_day FROM decisions d JOIN cognition_jobs j USING(job_id) "
        "JOIN scenes s USING(scene_id) WHERE d.validation_status='accepted' ORDER BY d.rowid"
    )
    lib = defaultdict(list)
    for r in rows:
        lib[(r["actor_person_id"], r["trigger_type"])].append(
            {
                "env": json.loads(r["envelope_json"]),
                "packet": json.loads(r["packet_json"]),
                "day": int(r["applied_day"]),
                "rowid": int(r["decision_rowid"]),
            }
        )
    return lib


def _rebind_knowledge(source_env, source_packet, dest_packet):
    src_by_id = {k["knowledge_id"]: k for k in source_packet.get("admissible_knowledge", [])}
    dest_by_prop = defaultdict(list)
    dest_by_text = defaultdict(list)
    dest_ids = set()
    for k in dest_packet.get("admissible_knowledge", []):
        dest_by_prop[k["proposition_id"]].append(k["knowledge_id"])
        if k.get("canonical_text"):
            dest_by_text[k["canonical_text"]].append(k["knowledge_id"])
        dest_ids.add(k["knowledge_id"])

    rebound = []
    missing = []
    for kid in source_env.get("decisive_knowledge_or_belief_ids", []):
        source_k = src_by_id.get(kid)
        if source_k is None:
            if kid in dest_ids:
                rebound.append(kid)
            else:
                missing.append(kid)
            continue
        choices = dest_by_prop.get(source_k["proposition_id"], [])
        if not choices and source_k.get("canonical_text"):
            choices = dest_by_text.get(source_k["canonical_text"], [])
        if choices:
            rebound.append(choices[0])
        else:
            missing.append(kid)
    return rebound, missing


def validate_seed(root: Path, source_db: Path, output_db: Path, seed: int, target_day: int, overrides: dict | None = None):
    for p in (output_db, Path(str(output_db) + "-wal"), Path(str(output_db) + "-shm")):
        if p.exists():
            p.unlink()

    with WorldDB(source_db) as source:
        source_run = source.one("SELECT * FROM runs ORDER BY created_at,run_id LIMIT 1")
        scenario_row = source.one(
            "SELECT config_json FROM scenarios WHERE scenario_id=? AND scenario_version=?",
            (source_run["scenario_id"], source_run["scenario_version"]),
        )
        scenario = json.loads(scenario_row["config_json"])
        library = _load_library(source)

    with WorldDB(output_db) as dest:
        run_id = init_fixture(dest, root, seed, scenario_override=scenario)
        eng = WorldEngine(dest, run_id)
        used = defaultdict(int)
        applied = []
        failures = []
        repeated_minor_templates = 0
        explicit_overrides_applied = []
        overrides = overrides or {}

        while True:
            pending = dest.all(
                "SELECT j.job_id,j.actor_person_id,j.created_day,j.rowid AS job_rowid,s.trigger_type "
                "FROM cognition_jobs j JOIN scenes s USING(scene_id) "
                "WHERE j.run_id=? AND j.status IN ('pending','rejected') "
                "ORDER BY j.created_day,j.rowid",
                (run_id,),
            )
            if pending:
                job = pending[0]
                key = (job["actor_person_id"], job["trigger_type"])
                ordinal = used[key]
                templates = library.get(key, [])
                override_key = f"{job['actor_person_id']}|{job['trigger_type']}|{ordinal+1}"
                dest_packet = compile_packet(dest, job["job_id"])
                exact_override = overrides.get(override_key)
                override = None
                applied_override_key = None
                override_reused_repeat = False
                template = None
                reused_repeat = False

                if exact_override is not None:
                    override = exact_override
                    applied_override_key = override_key
                elif ordinal < len(templates):
                    template = templates[ordinal]
                elif job['trigger_type'] == 'minor_illness':
                    prefix = f"{job['actor_person_id']}|minor_illness|"
                    prior = []
                    current_number = ordinal + 1
                    for k, v in overrides.items():
                        if k.startswith(prefix):
                            try:
                                n = int(k.rsplit('|',1)[1])
                                if n < current_number:
                                    prior.append((n, k, v))
                            except ValueError:
                                pass
                    if prior:
                        _, applied_override_key, override = max(prior)
                        override_reused_repeat = True
                    elif templates:
                        template = templates[-1]
                        reused_repeat = True
                        repeated_minor_templates += 1
                    else:
                        failures.append({
                            "kind":"unmatched_semantic_job","day":int(job["created_day"]),
                            "actor":job["actor_person_id"],"trigger":job["trigger_type"],
                            "seen_ordinal":current_number,"source_templates":0,"override_key":override_key})
                        break
                else:
                    failures.append({
                        "kind":"unmatched_semantic_job","day":int(job["created_day"]),
                        "actor":job["actor_person_id"],"trigger":job["trigger_type"],
                        "seen_ordinal":ordinal+1,"source_templates":len(templates),"override_key":override_key})
                    break

                if override is not None:
                    env = deepcopy(override)
                    env["actor_id"] = job["actor_person_id"]
                    env["decision_id"] = f"VAL-{seed}-{len(applied)+1:04d}-{job['job_id']}"
                    explicit_overrides_applied.append({
                        "key": override_key, "template_override_key": applied_override_key,
                        "day": int(job["created_day"]), "job_id": job["job_id"],
                        "reused_prior_override": override_reused_repeat})
                else:
                    source_env = deepcopy(template["env"])
                    source_packet = template["packet"]
                    env = _rebase_obj(
                        source_env, source_packet["scene"].get("stakes", {}),
                        dest_packet["scene"].get("stakes", {}))
                    env["decision_id"] = f"VAL-{seed}-{len(applied)+1:04d}-{job['job_id']}"
                    rebound, missing = _rebind_knowledge(source_env, source_packet, dest_packet)
                    if missing:
                        failures.append({
                            "kind":"knowledge_rebind_failed","day":int(job["created_day"]),
                            "actor":job["actor_person_id"],"trigger":job["trigger_type"],
                            "missing":missing,"source_template_day":template["day"]})
                        break
                    env["decisive_knowledge_or_belief_ids"] = rebound
                used[key] += 1
                result = eng.submit_decision(job["job_id"], env)
                if not result.ok:
                    failures.append(
                        {
                            "kind": "decision_rejected",
                            "day": int(job["created_day"]),
                            "actor": job["actor_person_id"],
                            "trigger": job["trigger_type"],
                            "errors": result.errors,
                            "source_template_day": template["day"] if template is not None else None,
                            "reused_repeat_minor_template": reused_repeat,
                            "actions": env.get("proposed_actions", []),
                        }
                    )
                    break
                applied.append(
                    {
                        "day": int(job["created_day"]),
                        "actor": job["actor_person_id"],
                        "trigger": job["trigger_type"],
                        "source_template_day": template["day"] if template is not None else None,
                        "reused_repeat_minor_template": reused_repeat,
                        "override_key": applied_override_key if override is not None else None,
                    }
                )
                continue

            if eng.day >= target_day:
                break
            before = eng.day
            eng.advance(target_day - before)
            if eng.day == before:
                failures.append({"kind": "no_progress", "day": before})
                break

        negative = int(
            dest.scalar("SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9") or 0
        )
        shortfalls = int(
            dest.scalar(
                "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='resource_shortfall'", (run_id,)
            )
            or 0
        )
        overdue = int(
            dest.scalar(
                "SELECT COUNT(*) FROM obligations WHERE status IN ('active','scheduled') "
                "AND due_day IS NOT NULL AND due_day < ?",
                (eng.day,),
            )
            or 0
        )
        runtime = [
            dict(x)
            for x in dest.all(
                "SELECT day,actor_ids_json,payload_json FROM events WHERE run_id=? "
                "AND event_type='runtime_circumstance' ORDER BY day,event_seq",
                (run_id,),
            )
        ]
        summary = {
            "mode": "semantic_policy_transfer_validation_only",
            "source_db": str(source_db),
            "seed": seed,
            "run_id": run_id,
            "target_day": target_day,
            "reached_day": eng.day,
            "completed_target": eng.day >= target_day and not failures,
            "semantic_decisions_applied": len(applied),
            "repeated_minor_illness_templates": repeated_minor_templates,
            "explicit_overrides_applied": explicit_overrides_applied,
            "failures": failures,
            "accepted_jobs": int(
                dest.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='accepted'", (run_id,)) or 0
            ),
            "rejected_jobs": int(
                dest.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='rejected'", (run_id,)) or 0
            ),
            "pending_jobs": int(
                dest.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='pending'", (run_id,)) or 0
            ),
            "open_scenes": int(
                dest.scalar("SELECT COUNT(*) FROM scenes WHERE run_id=? AND status='open'", (run_id,)) or 0
            ),
            "events": int(dest.scalar("SELECT COUNT(*) FROM events WHERE run_id=?", (run_id,)) or 0),
            "negative_resource_stocks": negative,
            "resource_shortfalls": shortfalls,
            "overdue_obligations": overdue,
            "runtime_circumstances": runtime,
            "state_hash": dest.state_hash(run_id),
            "last_applied": applied[-12:],
        }
        return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--source-db", required=True)
    ap.add_argument("--output-db", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--target-day", type=int, required=True)
    ap.add_argument("--json-out")
    ap.add_argument("--overrides")
    ns = ap.parse_args()
    overrides = json.loads(Path(ns.overrides).read_text()) if ns.overrides else {}
    summary = validate_seed(
        Path(ns.root), Path(ns.source_db), Path(ns.output_db), ns.seed, ns.target_day, overrides=overrides
    )
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    if ns.json_out:
        Path(ns.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    raise SystemExit(0 if summary["completed_target"] else 2)


if __name__ == "__main__":
    main()
