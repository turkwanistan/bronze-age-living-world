import json

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.engine import WorldEngine


def _pending_for(db, rid, actor, trigger):
    return db.one(
        "SELECT j.job_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.run_id=? AND j.actor_person_id=? AND j.status='pending' AND s.trigger_type=? "
        "ORDER BY j.created_day,j.job_id LIMIT 1",
        (rid, actor, trigger),
    )


def test_household_outside_work_requires_request_and_delayed_completion(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(14, allow_unresolved=True) == 14

    worker_job = _pending_for(db, rid, "P16", "outside_work_opportunity")
    assert worker_job is not None
    packet = compile_packet(db, worker_job["job_id"])
    assert packet["scene"]["stakes"]["situation_id"] == "SIT-006"
    assert packet["scene"]["stakes"]["household_senior_person_id"] == "P15"
    assert packet["scene"]["stakes"]["household_receipt"] == {
        "amount": 1.0,
        "resource": "grain",
        "unit": "abstract_fixture_unit",
    }
    assert "request_household_work_agreement" in packet["allowed_actions"]
    assert "traits" not in packet["scene"]["stakes"]

    request = {
        "decision_id": "DEC-P16-WORK-REQUEST",
        "actor_id": "P16",
        "selected_intent": "ask the household senior before taking outside work",
        "proposed_actions": [
            {
                "type": "request_household_work_agreement",
                "target_person_id": "P15",
                "reason": "the fixture receipt could help the household while the absence is brief",
            }
        ],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P16"],
        "decision_basis_tags": ["household_obligation", "worker_agency"],
        "declared_uncertainty": "The work terms and compensation are fixture abstractions, not historical rates.",
    }
    result = eng.submit_decision(worker_job["job_id"], request)
    assert result.ok, result.errors

    senior_job = _pending_for(db, rid, "P15", "household_work_request")
    assert senior_job is not None
    senior_packet = compile_packet(db, senior_job["job_id"])
    assert senior_packet["scene"]["stakes"]["requester_person_id"] == "P16"
    assert any("asked to take outside work" in m["summary"] for m in senior_packet["relevant_memories"])

    before = db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='grain'")
    accept = {
        "decision_id": "DEC-P15-WORK-ACCEPT",
        "actor_id": "P15",
        "selected_intent": "allow the brief outside work because the household benefit outweighs the short absence",
        "proposed_actions": [{"type": "accept_fixture_work", "work_id": "WORK-P16-PORTER-001"}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P15"],
        "decision_basis_tags": ["household_continuity", "kin_support"],
        "declared_uncertainty": "The one-day work and receipt are engineering fixtures only.",
    }
    result = eng.submit_decision(senior_job["job_id"], accept)
    assert result.ok, result.errors
    scheduled = db.one(
        "SELECT * FROM obligations WHERE obligation_type='fixture_outside_work' AND status='scheduled'"
    )
    assert scheduled is not None
    assert scheduled["due_day"] == 15
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='fixture_outside_work_completed'") == 0

    assert eng.advance(1, allow_unresolved=True) == 1
    after = db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='grain'")
    assert after == pytest.approx(before - 0.48 + 1.0)
    assert db.scalar(
        "SELECT status FROM obligations WHERE obligation_id=?", (scheduled["obligation_id"],)
    ) == "fulfilled"
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='fixture_outside_work_completed'") == 1


def test_water_access_request_uses_unequal_access_and_expires(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(18, allow_unresolved=True) == 18

    request_job = _pending_for(db, rid, "P2", "water_access_pressure")
    assert request_job is not None
    packet = compile_packet(db, request_job["job_id"])
    assert packet["household"]["status"]["water_access"] == "shared"
    assert packet["scene"]["stakes"]["access_holder_person_id"] == "P6"
    assert packet["scene"]["stakes"]["access_holder_household_id"] == "H-SCRIBE"
    assert "I-WATER" in {i["institution_id"] for i in packet["available_institutions"]}

    bad = {
        "decision_id": "DEC-P2-WATER-BAD-TARGET",
        "actor_id": "P2",
        "selected_intent": "request temporary access",
        "proposed_actions": [
            {"type": "request_water_access", "target_person_id": "P3", "requested_days": 2}
        ],
        "decisive_knowledge_or_belief_ids": [],
        "decision_basis_tags": [],
        "declared_uncertainty": "fixture circumstance",
    }
    validation = eng.validate_decision(request_job["job_id"], bad)
    assert not validation.ok
    assert any("invalid_water_access_holder" in e for e in validation.errors)

    request = {
        "decision_id": "DEC-P2-WATER-REQUEST",
        "actor_id": "P2",
        "selected_intent": "ask a known private-access neighbor for short temporary access",
        "proposed_actions": [
            {
                "type": "request_water_access",
                "target_person_id": "P6",
                "requested_days": 2,
                "reason": "the shared access point is temporarily disrupted in this fixture",
            }
        ],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P2"],
        "decision_basis_tags": ["neighbor_reputation", "temporary_need"],
        "declared_uncertainty": "Exact Ugaritic access procedure is intentionally unspecified.",
    }
    result = eng.submit_decision(request_job["job_id"], request)
    assert result.ok, result.errors

    holder_job = _pending_for(db, rid, "P6", "water_access_request")
    assert holder_job is not None
    holder_packet = compile_packet(db, holder_job["job_id"])
    assert holder_packet["household"]["status"]["water_access"] == "private"
    assert holder_packet["scene"]["stakes"]["requester_person_id"] == "P2"
    assert any("temporary water access" in m["summary"] for m in holder_packet["relevant_memories"])

    prior_trust = db.scalar("SELECT trust FROM relationships WHERE from_person_id='P2' AND to_person_id='P6'")
    grant = {
        "decision_id": "DEC-P6-WATER-GRANT",
        "actor_id": "P6",
        "selected_intent": "grant bounded temporary access without asserting a broader legal right",
        "proposed_actions": [{"type": "grant_water_access", "requested_days": 2}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P6"],
        "decision_basis_tags": ["neighbor_cooperation", "bounded_access"],
        "declared_uncertainty": "The grant is a fixture negotiation, not a reconstruction of Ugaritic water law.",
    }
    result = eng.submit_decision(holder_job["job_id"], grant)
    assert result.ok, result.errors

    permission = db.one(
        "SELECT * FROM obligations WHERE obligation_type='temporary_water_access' AND status='granted'"
    )
    assert permission is not None
    assert permission["beneficiary_person_id"] == "P2"
    assert permission["due_day"] == 19
    assert db.scalar("SELECT trust FROM relationships WHERE from_person_id='P2' AND to_person_id='P6'") > prior_trust
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='water_access_granted'") == 1

    assert eng.advance(2, allow_unresolved=True) == 2
    assert db.scalar(
        "SELECT status FROM obligations WHERE obligation_id=?", (permission["obligation_id"],)
    ) == "expired"
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='water_access_permission_expired'") == 1
