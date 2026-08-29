from __future__ import annotations

from pathlib import Path

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.replay import replay_recorded_decisions

ROOT = Path(__file__).resolve().parents[1]
V009_HASH = "7ea6a82c61fcd10f94b1e741b357efba0bafb50e5acaa24ebf4e0e6319c4ada3"


def _job(db: WorldDB, trigger: str, actor: str):
    return db.one(
        "SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",
        (trigger, actor),
    )


def _submit(eng: WorldEngine, job, decision_id: str, actor: str, action: dict, knowledge=None):
    result = eng.submit_decision(job["job_id"], {
        "decision_id": decision_id,
        "actor_id": actor,
        "selected_intent": decision_id,
        "proposed_actions": [action],
        "decisive_knowledge_or_belief_ids": knowledge or [],
        "decision_basis_tags": ["regression"],
        "declared_uncertainty": "Exact fuel conversion, disrupted lot size, price and delay are fixture calibration rather than historical quantitative claims.",
    })
    assert result.ok, result.errors


def test_v009_replay_remains_exact_under_v010_repo(tmp_path):
    source = ROOT / "state" / "ugarit_living_v009.sqlite"
    if not source.exists():
        pytest.skip("host-local accepted v009 database is not present")
    result = replay_recorded_decisions(ROOT, source, tmp_path / "v009_replay.sqlite", target_day=375)
    assert result["recorded_decisions_applied"] == 114
    assert result["new_cognition_calls"] == 0
    assert result["source_hash"] == V009_HASH
    assert result["rebuilt_hash"] == V009_HASH
    assert result["exact_match"] is True


def test_fuel_preparation_consumes_finite_feedstock(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=376 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.10 WHERE household_id='H-CRAFT' AND resource_type='charcoal'")
    eng.detect_situations(376)
    job = _job(db, "workshop_fuel_preparation_pressure", "P7")
    assert job is not None
    packet = compile_packet(db, job["job_id"])
    assert packet["scene"]["stakes"]["feedstock_input"] == 0.40
    assert packet["scene"]["stakes"]["charcoal_output"] == 0.50
    before_feed = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'"))
    _submit(eng, job, "DEC-V010-FUEL", "P7", {
        "type": "prepare_charcoal_fuel", "feedstock_input": 0.40, "charcoal_output": 0.50,
        "reason": "fuel is now the binding workshop input",
    }, ["K-LOCAL-CRAFT-FUEL-001-P7"])
    after_feed = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'"))
    charcoal = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='charcoal'"))
    assert abs(after_feed - (before_feed - 0.40)) < 1e-9
    assert abs(charcoal - 0.60) < 1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='charcoal_fuel_prepared'", (rid,)) == 1



def test_fuel_preparation_can_recur_while_finite_feedstock_remains(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=376 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.10 WHERE household_id='H-CRAFT' AND resource_type='charcoal'")
    eng.detect_situations(376)
    first = _job(db, "workshop_fuel_preparation_pressure", "P7")
    _submit(eng, first, "DEC-V010-FUEL-FIRST", "P7", {"type":"prepare_charcoal_fuel","feedstock_input":0.40,"charcoal_output":0.50})
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=385 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.19 WHERE household_id='H-CRAFT' AND resource_type='charcoal'")
    eng.detect_situations(385)
    rows=db.all("SELECT j.job_id FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type='workshop_fuel_preparation_pressure' AND j.actor_person_id='P7' ORDER BY j.rowid")
    assert len(rows) == 1
    second=rows[0]
    _submit(eng, second, "DEC-V010-FUEL-SECOND", "P7", {"type":"prepare_charcoal_fuel","feedstock_input":0.40,"charcoal_output":0.50})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'")) - 0.40) < 1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='charcoal_fuel_prepared'", (rid,)) == 2

def _seed_repeat_market_state(db: WorldDB, rid: str):
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=376 WHERE run_id=?", (rid,))
        con.execute("UPDATE resource_stocks SET amount=0.03 WHERE household_id='H-CRAFT' AND resource_type='metal'")
        con.execute("UPDATE resource_stocks SET amount=0.70 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
        con.execute("UPDATE resource_stocks SET amount=0.0 WHERE household_id='H-MERCH' AND resource_type='metal'")
        con.execute(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("REL-V010-P7-P12", "P7", "P12", "market_contact", None, 0.45, 0.57, 0.03, 0.56, 0.0, 0.0, 0.0, 0, "{}", 365),
        )
        con.execute(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("REL-V010-P12-P7", "P12", "P7", "market_contact", None, 0.45, 0.56, 0.03, 0.56, 0.0, 0.0, 0.0, 0, "{}", 365),
        )
        con.execute(
            "INSERT INTO events(event_id,run_id,day,event_type,actor_ids_json,payload_json) VALUES (?,?,?,?,?,?)",
            ("EV-V010-PRIOR-ALT", rid, 368, "alternate_metal_exchange_completed", '["P12","P7"]', '{"metal_amount":0.3}'),
        )


def _deliver_disrupted_terms(db: WorldDB, rid: str, eng: WorldEngine):
    eng.detect_situations(376)
    inquiry = _job(db, "repeat_alternate_metal_inquiry_opportunity", "P7")
    assert inquiry is not None
    p7_packet = compile_packet(db, inquiry["job_id"])
    assert not any(k["proposition_id"] == "PROP-METAL-DISRUPT-001" for k in p7_packet["admissible_knowledge"])
    _submit(eng, inquiry, "DEC-V010-INQUIRE", "P7", {
        "type": "send_message", "target_person_id": "P12", "sender_intent": "inquiry",
        "content": "What raw-metal availability and terms can you actually offer now?",
    })
    assert eng.advance(1, allow_unresolved=True) == 1
    response = _job(db, "information_inquiry_received", "P12")
    assert response is not None
    p12_packet = compile_packet(db, response["job_id"])
    assert any(k["knowledge_id"] == "K-METAL-DISRUPT-P12" for k in p12_packet["admissible_knowledge"])
    _submit(eng, response, "DEC-V010-REPORT", "P12", {
        "type": "send_message", "target_person_id": "P7", "sender_intent": "report",
        "proposition_id": "PROP-METAL-DISRUPT-001",
        "content": "The later lot is disrupted: only a smaller usable amount and a longer delay are currently available.",
    }, ["K-METAL-DISRUPT-P12"])
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-DISRUPT-001'") == 0
    assert eng.advance(1, allow_unresolved=True) == 1
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-DISRUPT-001'") == 1
    shock = _job(db, "disrupted_alternate_metal_terms_received", "P7")
    assert shock is not None
    return shock


def test_disrupted_repeat_terms_require_delayed_report_and_can_trigger_recycling(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _seed_repeat_market_state(db, rid)
    shock = _deliver_disrupted_terms(db, rid, eng)
    packet = compile_packet(db, shock["job_id"])
    assert packet["scene"]["stakes"]["metal_amount"] == 0.18
    assert packet["scene"]["stakes"]["delivery_days"] == 5
    before_finished = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"))
    before_metal = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    _submit(eng, shock, "DEC-V010-RECYCLE", "P7", {
        "type": "recycle_finished_metalwork", "input_finished_metalwork": 0.20, "output_metal": 0.12,
        "reason": "the disrupted external terms are poor enough to use the immediate local fallback",
    }, [next(k["knowledge_id"] for k in packet["admissible_knowledge"] if k["proposition_id"] == "PROP-METAL-DISRUPT-001")])
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")) - (before_finished - 0.20)) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'")) - (before_metal + 0.12)) < 1e-9
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_alternate_metal_exchange'") == 0


def test_disrupted_repeat_terms_can_be_accepted_and_deliver_partial_lot(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _seed_repeat_market_state(db, rid)
    shock = _deliver_disrupted_terms(db, rid, eng)
    packet = compile_packet(db, shock["job_id"])
    kid = next(k["knowledge_id"] for k in packet["admissible_knowledge"] if k["proposition_id"] == "PROP-METAL-DISRUPT-001")
    before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    _submit(eng, shock, "DEC-V010-ACCEPT-DISRUPT", "P7", {
        "type": "accept_alternate_metal_exchange", "silver_cost": 0.30, "metal_amount": 0.18, "delivery_days": 5,
        "reason": "accept the degraded lot despite the temporary disruption",
    }, [kid])
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_alternate_metal_exchange'") == 1
    assert eng.advance(5, allow_unresolved=True) == 5
    after = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    assert after >= before + 0.18 - 1e-9
    row = db.one("SELECT provenance_json,status FROM obligations WHERE obligation_type='fixture_alternate_metal_exchange' ORDER BY rowid DESC LIMIT 1")
    assert row["status"] == "fulfilled"
    assert 'ASM-FIXTURE-030' in row["provenance_json"]
