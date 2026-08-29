from __future__ import annotations

import json
from pathlib import Path

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.replay import replay_recorded_decisions

ROOT = Path(__file__).resolve().parents[1]
V007_HASH = "7cd79256a5affcff0b65b8c98f22be5078e46ab0bd2b3e0ce014e778f4363f86"


def _job(db, trigger: str, actor: str):
    return db.one(
        "SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",
        (trigger, actor),
    )


def _submit(eng: WorldEngine, job, decision_id: str, actor: str, action: dict, knowledge: list[str] | None = None):
    result = eng.submit_decision(
        job["job_id"],
        {
            "decision_id": decision_id,
            "actor_id": actor,
            "selected_intent": decision_id,
            "proposed_actions": [action],
            "decisive_knowledge_or_belief_ids": knowledge or [],
            "decision_basis_tags": ["regression"],
            "declared_uncertainty": "Winter condition/timing/labor quantities are fixture calibration, not historical rates or exchange prices.",
        },
    )
    assert result.ok, result.errors


def test_v007_replay_remains_exact_under_v008_repo(tmp_path):
    source = ROOT / "state" / "ugarit_living_v007.sqlite"
    if not source.exists():
        pytest.skip("host-local accepted v007 database is not present")
    result = replay_recorded_decisions(ROOT, source, tmp_path / "v007_replay.sqlite", target_day=240)
    assert result["recorded_decisions_applied"] == 80
    assert result["new_cognition_calls"] == 0
    assert result["source_hash"] == V007_HASH
    assert result["rebuilt_hash"] == V007_HASH
    assert result["exact_match"] is True


def test_winter_reciprocal_labor_can_clear_sowing_favor_after_completed_service(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=252 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.90 WHERE household_id='H-FARM' AND resource_type='draft_team_condition'")
        con.execute("UPDATE relationships SET favors_given=1,trust=0.57,respect=0.46 WHERE from_person_id='P1' AND to_person_id='P13'")
        con.execute("UPDATE relationships SET favors_owed=1,trust=0.64,respect=0.63 WHERE from_person_id='P13' AND to_person_id='P1'")
    eng.detect_situations(252)
    request = _job(db, "winter_draft_maintenance_pressure", "P1")
    assert request is not None
    packet = compile_packet(db, request["job_id"])
    assert packet["scene"]["stakes"]["remembered_favor_available"] is True
    assert abs(packet["scene"]["stakes"]["draft_team_condition"] - 0.90) < 1e-9
    _submit(
        eng, request, "DEC-WINTER-REQ", "P1",
        {"type": "request_reciprocal_labor", "target_person_id": "P13", "service_days": 1,
         "reason": "ask for one bounded winter maintenance service in light of the earlier sowing help"},
        knowledge=["K-LOCAL-WINTER-001-P1"],
    )
    response = _job(db, "reciprocal_labor_request", "P13")
    assert response is not None
    _submit(
        eng, response, "DEC-WINTER-ACCEPT", "P13",
        {"type": "fulfill_reciprocal_labor", "requester_person_id": "P1", "service_days": 1,
         "reason": "answer the remembered sowing favor with practical winter help"},
        knowledge=["K-LOCAL-WINTER-001-P13"],
    )
    # Acceptance schedules work but does not clear social credit before completion.
    assert float(db.scalar("SELECT favors_owed FROM relationships WHERE from_person_id='P13' AND to_person_id='P1'")) == 1.0
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_winter_reciprocal_labor'") == 1
    assert eng.advance(1, allow_unresolved=True) == 1
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='draft_team_condition'")) - 1.0) < 1e-9
    assert float(db.scalar("SELECT favors_owed FROM relationships WHERE from_person_id='P13' AND to_person_id='P1'")) == 0.0
    assert float(db.scalar("SELECT favors_given FROM relationships WHERE from_person_id='P1' AND to_person_id='P13'")) == 0.0
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='fulfilled' AND obligation_type='fixture_winter_reciprocal_labor'") == 1
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='winter_reciprocal_labor_completed'", (rid,)) == 1


def test_internal_winter_maintenance_does_not_consume_social_favor(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=252 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.90 WHERE household_id='H-FARM' AND resource_type='draft_team_condition'")
        con.execute("UPDATE relationships SET favors_given=1 WHERE from_person_id='P1' AND to_person_id='P13'")
        con.execute("UPDATE relationships SET favors_owed=1 WHERE from_person_id='P13' AND to_person_id='P1'")
    eng.detect_situations(252)
    job = _job(db, "winter_draft_maintenance_pressure", "P1")
    _submit(
        eng, job, "DEC-WINTER-INTERNAL", "P1",
        {"type": "handle_winter_maintenance_internally", "reason": "keep this maintenance burden inside my household"},
        knowledge=["K-LOCAL-WINTER-001-P1"],
    )
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='draft_team_condition'")) - 1.0) < 1e-9
    assert float(db.scalar("SELECT favors_given FROM relationships WHERE from_person_id='P1' AND to_person_id='P13'")) == 1.0
    assert float(db.scalar("SELECT favors_owed FROM relationships WHERE from_person_id='P13' AND to_person_id='P1'")) == 1.0


def test_smaller_reciprocal_support_caps_later_return_suggestion(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    origin_scene = "SCENE-V008-SMALL-CREDIT-ORIGIN"
    obligation_id = "O-V008-SMALL-CREDIT"
    with db.transaction() as con:
        con.execute(
            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (origin_scene, rid, 1, "P-NORTH-NEIGH", "economic", "resource_request", "{}", "{}", "{}", "[]", "closed"),
        )
        con.execute(
            "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (obligation_id, "P7", "H-CRAFT", "P3", "H-MERCH", "reciprocal_exchange",
             "Small reciprocal support regression.", None, "active",
             json.dumps({
                 "assumption_id": "ASM-FIXTURE-013",
                 "origin_scene_id": origin_scene,
                 "origin_resource": "metal",
                 "origin_amount": 0.15,
                 "return_cap_assumption_id": "ASM-FIXTURE-026",
             }, sort_keys=True, separators=(",", ":"))),
        )
        con.execute(
            "UPDATE resource_stocks SET amount=0.20 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"
        )
        con.execute("UPDATE runs SET current_day=31 WHERE run_id=?", (rid,))
    eng.detect_situations(31)
    row = db.one(
        "SELECT j.job_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND j.actor_person_id='P7' AND s.trigger_type='reciprocal_return_opportunity' "
        "AND json_extract(s.stakes_json,'$.obligation_id')=?",
        (obligation_id,),
    )
    assert row is not None
    packet = compile_packet(db, row["job_id"])
    assert abs(float(packet["scene"]["stakes"]["suggested_amount"]) - 0.15) < 1e-9
    assert float(packet["scene"]["stakes"]["available_finished_metalwork"]) == 0.20
    assert "ASM-FIXTURE-026" in packet["scene"]["stakes"]["fixture_notice"]


def test_recent_refusal_memory_is_retained_when_relationship_has_conflict(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    with db.transaction() as con:
        # Fill the normal salience window with older memories so a recent refusal would
        # otherwise be crowded out.
        for i in range(12):
            con.execute(
                "INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f"MEM-OLD-{i}", "P7", "work", f"older salient work memory {i}", None, i, 0.5, 0.95, 0.5, 0.5, "{}"),
            )
        con.execute(
            "INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("MEM-RECENT-REFUSAL", "P7", "decision", "P3 refused my latest metal request because his remaining stock was too low.", None, 308, 0.5, 0.70, 0.9, 0.8, "{}"),
        )
        con.execute(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("REL-TEST-P7-P3", "P7", "P3", "exchange_contact", None, 0.5, 0.8, 0.0, 0.6, 0.0, 0.0, 0.0, 1, "{}", 308),
        )
        con.execute(
            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("SCENE-MEMORY-REGRESSION", rid, 322, "P-NORTH-NEIGH", "economic", "memory_regression", "{}", "{}", "{}", "[]", "open"),
        )
        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", ("SCENE-MEMORY-REGRESSION", "P7", "decision_actor"))
    jid = eng.enqueue_job("SCENE-MEMORY-REGRESSION", "P7", ["wait"])
    packet = compile_packet(db, jid)
    ids = {m["memory_id"] for m in packet["relevant_memories"]}
    assert "MEM-RECENT-REFUSAL" in ids
