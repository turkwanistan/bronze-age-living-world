from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .db import WorldDB
from .engine import WorldEngine
from .fixture import init_fixture


class RecordedReplayError(RuntimeError):
    """Raised when a recorded strict run cannot be reconstructed without new cognition."""


def deterministic_fixture_hash(root: Path, seed: int, days: int) -> str:
    """Diagnostic deterministic-subsystem replay that intentionally ignores cognition gates."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "world.sqlite"
        with WorldDB(path) as db:
            run_id = init_fixture(db, root, seed)
            WorldEngine(db, run_id).advance(days, allow_unresolved=True)
            return db.state_hash(run_id)


def replay_recorded_decisions(
    root: Path,
    source_db_path: str | Path,
    output_db_path: str | Path,
    *,
    target_day: int | None = None,
) -> dict[str, Any]:
    """Rebuild a strict run using only seed + already-recorded accepted decisions.

    This function never asks for new cognition. If the deterministic rebuild creates a
    cognition job for which the source history has no accepted decision, replay fails
    closed rather than inventing an action or advancing past the boundary.
    """
    source_path = Path(source_db_path)
    output_path = Path(output_db_path)
    if source_path.resolve() == output_path.resolve():
        raise RecordedReplayError("source_and_output_db_must_differ")
    if output_path.exists():
        raise RecordedReplayError(f"output_db_exists:{output_path}")

    with WorldDB(source_path) as source:
        source_run = source.one("SELECT * FROM runs ORDER BY created_at,run_id LIMIT 1")
        if not source_run:
            raise RecordedReplayError("source_has_no_run")
        run_id = str(source_run["run_id"])
        source_day = int(source_run["current_day"])
        replay_day = source_day if target_day is None else int(target_day)
        if replay_day < 0 or replay_day > source_day:
            raise RecordedReplayError(f"target_day_out_of_range:0..{source_day}:{replay_day}")

        rejected = int(source.scalar(
            "SELECT COUNT(*) FROM decisions d JOIN cognition_jobs j USING(job_id) "
            "WHERE j.run_id=? AND d.validation_status!='accepted'",
            (run_id,),
        ) or 0)
        if rejected:
            raise RecordedReplayError(f"source_contains_nonaccepted_decisions:{rejected}")

        decision_rows = source.all(
            "SELECT d.job_id,d.envelope_json,d.applied_day,d.rowid AS decision_rowid "
            "FROM decisions d JOIN cognition_jobs j USING(job_id) "
            "WHERE j.run_id=? AND d.validation_status='accepted' AND d.applied_day<=? "
            "ORDER BY d.applied_day,d.rowid",
            (run_id, replay_day),
        )
        recorded = {str(r["job_id"]): json.loads(r["envelope_json"]) for r in decision_rows}
        # Decision rowid is the canonical application sequence in the source history.
        # Multiple cognition jobs can be pending on the same simulated day, and action
        # application order can affect event/memory IDs even when material outcomes are
        # otherwise commutative. Replay must therefore reproduce source application order,
        # not destination cognition-job creation order.
        recorded_order = {str(r["job_id"]): int(r["decision_rowid"]) for r in decision_rows}
        source_hash = source.state_hash(run_id) if replay_day == source_day else None
        seed = int(source_run["rng_seed"])
        scenario_row = source.one(
            "SELECT config_json FROM scenarios WHERE scenario_id=? AND scenario_version=?",
            (source_run["scenario_id"], source_run["scenario_version"]),
        )
        if not scenario_row:
            raise RecordedReplayError("source_scenario_config_missing")
        source_scenario_config = json.loads(scenario_row["config_json"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    applied: list[str] = []
    with WorldDB(output_path) as dest:
        rebuilt_run_id = init_fixture(dest, root, seed, scenario_override=source_scenario_config)
        if rebuilt_run_id != run_id:
            raise RecordedReplayError(f"run_id_mismatch:{rebuilt_run_id}:{run_id}")
        eng = WorldEngine(dest, rebuilt_run_id)

        while True:
            pending = dest.all(
                "SELECT job_id,created_day,rowid AS job_rowid FROM cognition_jobs "
                "WHERE run_id=? AND status IN ('pending','rejected')",
                (rebuilt_run_id,),
            )
            eligible = [j for j in pending if int(j["created_day"]) <= replay_day]
            if eligible:
                # Fail closed before applying anything if the rebuilt history exposes a
                # cognition boundary absent from the recorded source history.
                for job in eligible:
                    job_id = str(job["job_id"])
                    if job_id not in recorded:
                        raise RecordedReplayError(f"missing_recorded_decision:{job_id}:day={job['created_day']}")

                # Apply exactly one decision, then re-query. A decision can enqueue a
                # same-day follow-up whose source sequence belongs before another already
                # pending sibling, so batch-applying the current pending set is unsafe.
                job = min(
                    eligible,
                    key=lambda j: (recorded_order[str(j["job_id"])], int(j["created_day"]), int(j["job_rowid"])),
                )
                job_id = str(job["job_id"])
                result = eng.submit_decision(job_id, recorded[job_id])
                if not result.ok:
                    raise RecordedReplayError(
                        f"recorded_decision_rejected:{job_id}:{'|'.join(result.errors)}"
                    )
                applied.append(job_id)
                continue

            if eng.day >= replay_day:
                break

            before = eng.day
            eng.advance(replay_day - before)
            if eng.day == before:
                pending_after = dest.scalar(
                    "SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status IN ('pending','rejected')",
                    (rebuilt_run_id,),
                )
                if not pending_after:
                    raise RecordedReplayError(f"replay_made_no_progress:day={before}")

        unused = sorted(set(recorded) - set(applied))
        if unused:
            raise RecordedReplayError(f"recorded_decisions_not_reached:{','.join(unused)}")

        rebuilt_hash = dest.state_hash(rebuilt_run_id)
        result: dict[str, Any] = {
            "run_id": rebuilt_run_id,
            "seed": seed,
            "target_day": replay_day,
            "recorded_decisions_applied": len(applied),
            "new_cognition_calls": 0,
            "rebuilt_hash": rebuilt_hash,
        }
        if source_hash is not None:
            result["source_hash"] = source_hash
            result["exact_match"] = rebuilt_hash == source_hash
            if rebuilt_hash != source_hash:
                raise RecordedReplayError(
                    f"state_hash_mismatch:source={source_hash}:rebuilt={rebuilt_hash}"
                )
        return result
