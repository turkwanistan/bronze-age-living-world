from __future__ import annotations

import json
from pathlib import Path

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine

ROOT = Path(__file__).resolve().parents[1]
V005_HASH = "959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df"


def _job(db, trigger: str, actor: str):
    return db.one(
        "SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",
        (trigger, actor),
    )


def _submit(eng: WorldEngine, job, did: str, actor: str, action: dict, *, knowledge: list[str] | None = None):
    result = eng.submit_decision(
        job["job_id"],
        {
            "decision_id": did,
            "actor_id": actor,
            "selected_intent": did,
            "proposed_actions": [action],
            "decisive_knowledge_or_belief_ids": knowledge or [],
            "decision_basis_tags": ["regression"],
            "declared_uncertainty": "Fixture quantities/procedures are not historical rates or universal rules.",
        },
    )
    assert result.ok, result.errors


def _advance_marriage_chain_to_final_consent(db, rid, eng: WorldEngine):
    assert eng.advance(150, allow_unresolved=True) == 150
    _submit(
        eng, _job(db, "marriage_discussion_opportunity", "P16"), "DEC-MAR-1", "P16",
        {"type": "request_marriage_discussion", "target_person_id": "P10", "reason": "explore whether marriage can fit both households"},
        knowledge=["K-LOCAL-MARRIAGE-001-P16"],
    )
    _submit(eng, _job(db, "marriage_discussion_request", "P10"), "DEC-MAR-2", "P10", {"type": "accept_marriage_discussion"},
            knowledge=["K-LOCAL-MARRIAGE-001-P10"])
    _submit(
        eng, _job(db, "marriage_household_terms", "P15"), "DEC-MAR-3", "P15",
        {
            "type": "propose_marriage_household_terms",
            "residence_household_id": "H-WIDOW",
            "continue_p16_care_to_p15": True,
            "target_household_senior_person_id": "P9",
            "reason": "preserve Bat-Rapiu's support while forming the marriage",
        },
        knowledge=["K-LOCAL-MARRIAGE-001-P15"],
    )
    _submit(
        eng, _job(db, "marriage_household_terms_review", "P9"), "DEC-MAR-4", "P9",
        {"type": "accept_marriage_household_terms", "residence_household_id": "H-WIDOW", "continue_p16_care_to_p15": True},
        knowledge=["K-LOCAL-MARRIAGE-001-P9"],
    )


def test_schema1_accepted_v005_hash_remains_stable_under_schema2_code():
    path = ROOT / "state" / "ugarit_living_v005.sqlite"
    if not path.exists():
        pytest.skip("host-local accepted v005 database is not present")
    with WorldDB(path) as db:
        rid = db.scalar("SELECT run_id FROM runs LIMIT 1")
        assert db.schema_version() == 1
        assert "marriages" not in db.canonical_hash_tables()
        assert db.state_hash(rid) == V005_HASH


def test_fresh_fixture_uses_schema2_and_hashes_normalized_marriage_state(world):
    db, rid = world
    assert db.schema_version() == 2
    assert int(db.scalar("SELECT schema_version FROM runs WHERE run_id=?", (rid,))) == 2
    assert {"marriages", "kinship_edges"}.issubset(set(db.canonical_hash_tables()))
    assert int(db.scalar("SELECT COUNT(*) FROM marriages WHERE run_id=? AND status='active'", (rid,))) == 5
    before = db.state_hash(rid)
    with db.transaction() as con:
        con.execute(
            "INSERT INTO kinship_edges VALUES (?,?,?,?,?,?,?,?)",
            ("KIN-TEST-SCHEMA2", rid, "P15", "P16", "test_only", 0, None, json.dumps({"test": True})),
        )
    assert db.state_hash(rid) != before


def test_marriage_requires_household_terms_and_both_final_consents(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _advance_marriage_chain_to_final_consent(db, rid, eng)
    assert not db.one(
        "SELECT 1 FROM marriages WHERE run_id=? AND status='active' AND ((person_a_id='P16' AND person_b_id='P10') OR (person_a_id='P10' AND person_b_id='P16'))",
        (rid,),
    )
    _submit(eng, _job(db, "marriage_final_consent", "P16"), "DEC-MAR-5", "P16",
            {"type": "give_marriage_consent", "partner_person_id": "P10"})
    assert not db.one(
        "SELECT 1 FROM marriages WHERE run_id=? AND status='active' AND ((person_a_id='P16' AND person_b_id='P10') OR (person_a_id='P10' AND person_b_id='P16'))",
        (rid,),
    )
    _submit(eng, _job(db, "marriage_final_consent", "P10"), "DEC-MAR-6", "P10",
            {"type": "give_marriage_consent", "partner_person_id": "P16"})
    marriage = db.one(
        "SELECT * FROM marriages WHERE run_id=? AND status='active' AND person_a_id='P16' AND person_b_id='P10'",
        (rid,),
    )
    assert marriage and marriage["residence_household_id"] == "H-WIDOW"
    assert db.scalar("SELECT household_id FROM household_memberships WHERE person_id='P10' AND until_day IS NULL") == "H-WIDOW"
    assert db.scalar("SELECT COUNT(*) FROM kinship_edges WHERE run_id=? AND start_day=150", (rid,)) == 3
    care = db.one("SELECT * FROM obligations WHERE obligation_type='continuing_kin_care' AND obligor_person_id='P16' AND beneficiary_person_id='P15'")
    assert care and care["status"] == "active"

    # New sealed packets expose normalized marriage/kinship state rather than relying on prose memory.
    scene_id = "SCENE-TEST-POST-MARRIAGE"
    with db.transaction() as con:
        con.execute(
            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (scene_id, rid, 150, "P-NORTH-NEIGH", "household", "post_marriage_inspection", "{}", "{}", "{}", "[]", "open"),
        )
        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (scene_id, "P10", "decision_actor"))
    jid = eng.enqueue_job(scene_id, "P10", ["wait"])
    packet = compile_packet(db, jid)
    assert any(m["marriage_id"] == marriage["marriage_id"] for m in packet["active_marriages"])
    assert any(k["kinship_type"] == "spouse" for k in packet["kinship_edges"])


def test_final_individual_decline_creates_no_marriage(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _advance_marriage_chain_to_final_consent(db, rid, eng)
    _submit(
        eng, _job(db, "marriage_final_consent", "P16"), "DEC-MAR-NO", "P16",
        {"type": "decline_marriage_consent", "reason": "I do not consent to the final arrangement."},
    )
    assert not db.one(
        "SELECT 1 FROM marriages WHERE run_id=? AND status='active' AND ((person_a_id='P16' AND person_b_id='P10') OR (person_a_id='P10' AND person_b_id='P16'))",
        (rid,),
    )
    assert db.scalar("SELECT COUNT(*) FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type='informal_mediation_review' AND s.day=150") == 0


def test_seasonal_surplus_storage_is_separate_from_neutral_staple_grain(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(154, allow_unresolved=True) == 154
    exposed = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='seasonal_produce'"))
    assert abs(exposed - 0.468) < 1e-9  # day147 production, day150 fixture loss, day154 production
    job = _job(db, "seasonal_surplus_storage_pressure", "P1")
    assert job is not None
    grain_before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='grain'"))
    _submit(
        eng, job, "DEC-STORAGE", "P1",
        {"type": "preserve_seasonal_surplus", "amount": 0.4, "reason": "reduce exposed surplus before further storage loss"},
        knowledge=["K-LOCAL-STORAGE-001-P1"],
    )
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='seasonal_produce'")) - 0.068) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='stored_seasonal_goods'")) - 0.36) < 1e-9
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='grain'")) == grain_before
    event = db.one("SELECT material_deltas_json FROM events WHERE run_id=? AND event_type='seasonal_surplus_preserved' ORDER BY event_seq DESC LIMIT 1", (rid,))
    deltas = json.loads(event["material_deltas_json"])
    assert "grain" not in deltas["H-FARM"]
