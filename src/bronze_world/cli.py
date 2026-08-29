from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cognition import compile_packet
from .db import WorldDB
from .engine import WorldEngine
from .fixture import init_fixture
from .reporting import status_snapshot, write_status_file
from .replay import deterministic_fixture_hash, replay_recorded_decisions


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_run(db: WorldDB, run_id: str | None) -> str:
    if run_id: return run_id
    row=db.one("SELECT run_id FROM runs ORDER BY created_at,run_id LIMIT 1")
    if not row: raise SystemExit("no run found")
    return row[0]


def main(argv: list[str] | None = None) -> None:
    p=argparse.ArgumentParser(prog="bronze-world")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("init-fixture"); a.add_argument("--db",required=True); a.add_argument("--seed",type=int,default=1350)
    a=sub.add_parser("advance"); a.add_argument("--db",required=True); a.add_argument("--run-id"); a.add_argument("--days",type=int,required=True)
    a=sub.add_parser("status"); a.add_argument("--db",required=True); a.add_argument("--run-id")
    a=sub.add_parser("pending-jobs"); a.add_argument("--db",required=True); a.add_argument("--run-id")
    a=sub.add_parser("show-job"); a.add_argument("--db",required=True); a.add_argument("job_id")
    a=sub.add_parser("submit-decision"); a.add_argument("--db",required=True); a.add_argument("job_id"); a.add_argument("decision_json")
    a=sub.add_parser("replay-check"); a.add_argument("--seed",type=int,default=1350); a.add_argument("--days",type=int,default=30)
    a=sub.add_parser("replay-recorded"); a.add_argument("--source-db",required=True); a.add_argument("--output-db",required=True); a.add_argument("--target-day",type=int)
    ns=p.parse_args(argv); root=project_root()
    if ns.cmd=="init-fixture":
        with WorldDB(ns.db) as db:
            rid=init_fixture(db,root,ns.seed); write_status_file(db,rid,root/"state/current.json"); print(rid)
    elif ns.cmd=="advance":
        with WorldDB(ns.db) as db:
            rid=resolve_run(db,ns.run_id); WorldEngine(db,rid).advance(ns.days); write_status_file(db,rid,root/"state/current.json"); print(json.dumps(status_snapshot(db,rid),indent=2))
    elif ns.cmd=="status":
        with WorldDB(ns.db) as db: print(json.dumps(status_snapshot(db,resolve_run(db,ns.run_id)),indent=2))
    elif ns.cmd=="pending-jobs":
        with WorldDB(ns.db) as db:
            rid=resolve_run(db,ns.run_id); rows=[dict(r) for r in db.all("SELECT job_id,scene_id,actor_person_id,status,created_day,packet_hash FROM cognition_jobs WHERE run_id=? AND status IN ('pending','rejected') ORDER BY created_day,job_id",(rid,))]; print(json.dumps(rows,indent=2))
    elif ns.cmd=="show-job":
        with WorldDB(ns.db) as db: print(json.dumps(compile_packet(db,ns.job_id),indent=2,ensure_ascii=False))
    elif ns.cmd=="submit-decision":
        envelope=json.loads(Path(ns.decision_json).read_text(encoding="utf-8"))
        with WorldDB(ns.db) as db:
            job=db.one("SELECT run_id FROM cognition_jobs WHERE job_id=?",(ns.job_id,)); eng=WorldEngine(db,job[0]); result=eng.submit_decision(ns.job_id,envelope); write_status_file(db,job[0],root/"state/current.json"); print(json.dumps({"ok":result.ok,"errors":result.errors},indent=2))
    elif ns.cmd=="replay-check":
        h1=deterministic_fixture_hash(root,ns.seed,ns.days); h2=deterministic_fixture_hash(root,ns.seed,ns.days); print(json.dumps({"seed":ns.seed,"days":ns.days,"hash_a":h1,"hash_b":h2,"exact_match":h1==h2},indent=2))
    elif ns.cmd=="replay-recorded":
        result=replay_recorded_decisions(root,ns.source_db,ns.output_db,target_day=ns.target_day); print(json.dumps(result,indent=2))

if __name__ == "__main__": main()
