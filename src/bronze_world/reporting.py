from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .db import WorldDB, canonical_json

DERIVED_MARKER = "derived_from_canonical_sqlite"


def status_snapshot(db: WorldDB, run_id: str) -> dict:
    run=dict(db.one("SELECT * FROM runs WHERE run_id=?",(run_id,)))
    return {
        "derived_state": True,
        "derived_from": DERIVED_MARKER,
        "run_id": run_id,
        "day": run["current_day"],
        "state_hash": db.state_hash(run_id),
        "households": db.scalar("SELECT COUNT(*) FROM households"),
        "persons": db.scalar("SELECT COUNT(*) FROM persons"),
        "events": db.scalar("SELECT COUNT(*) FROM events WHERE run_id=?",(run_id,)),
        "pending_cognition_jobs": db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='pending'",(run_id,)),
        "rejected_cognition_jobs": db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='rejected'",(run_id,)),
        "accepted_cognition_jobs": db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='accepted'",(run_id,)),
        "open_scenes": db.scalar("SELECT COUNT(*) FROM scenes WHERE run_id=? AND status='open'",(run_id,)),
        "rng_seed": run["rng_seed"],
        "scenario_version": run["scenario_version"],
        "schema_version": run["schema_version"],
        "cognition_protocol_version": run["cognition_protocol_version"],
    }


def write_status_file(db: WorldDB, run_id: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status_snapshot(db,run_id),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
