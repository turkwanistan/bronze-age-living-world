from __future__ import annotations

import json
from pathlib import Path

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.provisioning import effective_household_provisioning
from bronze_world.replay import replay_recorded_decisions

ROOT = Path(__file__).resolve().parents[1]
V006_HASH = "d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb"


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
            "declared_uncertainty": "Fixture timing/quantities/procedure are not historical rates or universal rules.",
        },
    )
    assert result.ok, result.errors


def _set_day(db, rid: str, day: int):
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=? WHERE run_id=?", (day, rid))


def test_recorded_replay_uses_source_scenario_not_latest_repo_scenario(tmp_path):
    source = ROOT / "state" / "ugarit_living_v006.sqlite"
    if not source.exists():
        pytest.skip("host-local accepted v006 database is not present")
    output = tmp_path / "v006_replay.sqlite"
    result = replay_recorded_decisions(ROOT, source, output, target_day=180)
    assert result["recorded_decisions_applied"] == 59
    assert result["new_cognition_calls"] == 0
    assert result["source_hash"] == V006_HASH
    assert result["rebuilt_hash"] == V006_HASH
    assert result["exact_match"] is True


def test_composition_neutral_provisioning_moves_with_residence_and_conserves_total(world):
    db, rid = world
    baseline_total = sum(
        float(r["fixture_daily_food_need"])
        for r in db.all("SELECT fixture_daily_food_need FROM households ORDER BY household_id")
    )
    effective_before = sum(
        float(effective_household_provisioning(db, rid, r["household_id"])["daily_need"])
        for r in db.all("SELECT household_id FROM households ORDER BY household_id")
    )
    assert abs(effective_before - baseline_total) < 1e-9

    with db.transaction() as con:
        con.execute("UPDATE household_memberships SET until_day=150 WHERE person_id='P10' AND until_day IS NULL")
        con.execute("INSERT INTO household_memberships VALUES (?,?,?,?,?)", ("H-WIDOW", "P10", "married_in_adult", 150, None))
    widow = effective_household_provisioning(db, rid, "H-WIDOW")
    ritual = effective_household_provisioning(db, rid, "H-RITUAL")
    assert widow["mode"] == "composition_neutral_per_person_share"
    assert abs(float(widow["daily_need"]) - 0.73) < 1e-9
    assert abs(float(widow["weekly_receipt"]) - 5.11) < 1e-9
    assert abs(float(ritual["daily_need"]) - 0.25) < 1e-9
    effective_after = sum(
        float(effective_household_provisioning(db, rid, r["household_id"])["daily_need"])
        for r in db.all("SELECT household_id FROM households ORDER BY household_id")
    )
    assert abs(effective_after - baseline_total) < 1e-9

    _set_day(db, rid, 150)
    scene_id = "SCENE-V007-PROVISIONING-PACKET"
    with db.transaction() as con:
        con.execute(
            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (scene_id, rid, 150, "P-NORTH-NEIGH", "household", "provisioning_inspection", "{}", "{}", "{}", "[]", "open"),
        )
        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (scene_id, "P10", "decision_actor"))
    jid = WorldEngine(db, rid).enqueue_job(scene_id, "P10", ["wait"])
    packet = compile_packet(db, jid)
    assert abs(float(packet["household"]["routine_expectations"]["daily_grain_need"]) - 0.73) < 1e-9
    assert packet["household"]["routine_expectations"]["provisioning_mode"] == "composition_neutral_per_person_share"


def test_repeated_continuing_care_can_create_nonbinding_property_preference(world):
    db, rid = world
    care_id = "O-TEST-CONTINUING-CARE"
    with db.transaction() as con:
        con.execute(
            "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (care_id, "P16", "H-WIDOW", "P15", "H-WIDOW", "continuing_kin_care",
             "Fixture continuing support obligation.", None, "active",
             json.dumps({"assumption_id": "ASM-FIXTURE-023"}, sort_keys=True, separators=(",", ":"))),
        )
    eng = WorldEngine(db, rid)

    for n, day in enumerate((184, 214), start=1):
        _set_day(db, rid, day)
        eng.detect_situations(day)
        job = _job(db, "continuing_kin_care_need", "P16")
        assert job is not None
        packet = compile_packet(db, job["job_id"])
        assert packet["scene"]["stakes"]["care_obligation_id"] == care_id
        _submit(
            eng, job, f"DEC-CARE-{n}", "P16",
            {"type": "fulfill_kin_care", "care_obligation_id": care_id,
             "support_kind": "household_property_support_day", "reason": "honor the continuing support term"},
            knowledge=["K-LOCAL-CARE-001-P16"],
        )

    review = _job(db, "property_preference_review", "P15")
    assert review is not None
    review_packet = compile_packet(db, review["job_id"])
    assert review_packet["scene"]["stakes"]["fulfilled_care_episodes"] == 2
    _submit(
        eng, review, "DEC-PROPERTY-PREF", "P15",
        {"type": "record_property_preference", "beneficiary_person_id": "P16",
         "preference_type": "care_informed_priority", "scope": "household_property_if_later_negotiated",
         "reason": "Kothar has repeatedly fulfilled the negotiated care term"},
        knowledge=["K-LOCAL-CARE-001-P15"],
    )
    pref = db.one("SELECT * FROM property_preferences WHERE run_id=? AND household_id='H-WIDOW' AND status='active'", (rid,))
    assert pref is not None
    assert pref["holder_person_id"] == "P15"
    assert pref["beneficiary_person_id"] == "P16"
    assert pref["preference_type"] == "care_informed_priority"
    assert db.scalar("SELECT status FROM obligations WHERE obligation_id=?", (care_id,)) == "active"
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='kin_care_fulfilled'", (rid,)) == 2


def test_draft_access_grant_creates_delayed_sowing_progress_and_social_favor(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _set_day(db, rid, 182)
    with db.transaction() as con:
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES (?,?,?,?,?)",
                    ("H-FARM","sowing_progress",0.20,"abstract_fixture_unit","ASM-FIXTURE-024"))
    eng.detect_situations(182)
    request_job = _job(db, "sowing_draft_access_pressure", "P13")
    assert request_job is not None
    _submit(
        eng, request_job, "DEC-DRAFT-REQ", "P13",
        {"type": "request_draft_access", "target_person_id": "P1", "service_days": 1,
         "reason": "secure one bounded service while the sowing window is intense"},
        knowledge=["K-LOCAL-SOWING-001-P13"],
    )
    grant_job = _job(db, "draft_access_request", "P1")
    assert grant_job is not None
    _submit(
        eng, grant_job, "DEC-DRAFT-GRANT", "P1",
        {"type": "grant_draft_access", "requester_person_id": "P13", "service_days": 1,
         "reason": "bounded neighbor help is feasible"},
        knowledge=["K-LOCAL-SOWING-001-P1"],
    )
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_draft_team_service'") == 1
    before = float(db.scalar("SELECT COALESCE(amount,0) FROM resource_stocks WHERE household_id='H-DEPEND' AND resource_type='sowing_progress'") or 0)
    holder_before = float(db.scalar("SELECT COALESCE(amount,0) FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='sowing_progress'") or 0)
    assert eng.advance(1, allow_unresolved=True) == 1
    after = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-DEPEND' AND resource_type='sowing_progress'"))
    holder_after = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='sowing_progress'"))
    assert abs(after - before - 0.10) < 1e-9
    assert abs(holder_after - holder_before + 0.05) < 1e-9
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='fulfilled' AND obligation_type='fixture_draft_team_service'") == 1
    rel = db.one("SELECT favors_owed,trust FROM relationships WHERE from_person_id='P13' AND to_person_id='P1'")
    assert float(rel["favors_owed"]) == 1.0
    assert float(rel["trust"]) > 0.61


def test_refused_draft_access_can_be_reopened_by_bounded_mediation(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _set_day(db, rid, 182)
    eng.detect_situations(182)
    _submit(
        eng, _job(db, "sowing_draft_access_pressure", "P13"), "DEC-DRAFT-REQ-M", "P13",
        {"type": "request_draft_access", "target_person_id": "P1", "service_days": 1, "reason": "request sowing help"},
        knowledge=["K-LOCAL-SOWING-001-P13"],
    )
    _submit(
        eng, _job(db, "draft_access_request", "P1"), "DEC-DRAFT-NO", "P1",
        {"type": "refuse_proposal", "reason": "my household cannot spare the team without review"},
    )
    follow = _job(db, "proposal_refusal_followup", "P13")
    assert follow is not None
    _submit(
        eng, follow, "DEC-DRAFT-MED", "P13",
        {"type": "seek_mediation", "institution_id": "I-MEDIATION", "issue": "one bounded draft-team service during sowing"},
    )
    review = _job(db, "informal_mediation_review", "P1")
    assert review is not None
    assert "grant_draft_access" in json.loads(review["allowed_actions_json"])
    _submit(
        eng, review, "DEC-DRAFT-MED-GRANT", "P1",
        {"type": "grant_draft_access", "requester_person_id": "P13", "service_days": 1,
         "reason": "after review, one bounded service is acceptable"},
        knowledge=["K-LOCAL-SOWING-001-P1"],
    )
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_draft_team_service'") == 1
