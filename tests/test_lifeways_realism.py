import json

from bronze_world.cognition import compile_packet
from bronze_world.engine import WorldEngine


def _job_for(db, rid, trigger):
    return db.one(
        "SELECT j.job_id,j.actor_person_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.run_id=? AND j.status='pending' AND s.trigger_type=? ORDER BY j.created_day,j.rowid LIMIT 1",
        (rid, trigger),
    )


def test_weekly_occupations_have_season_and_material_dependencies(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng._seasonal_context(0)["phase"] == "cereal_harvest_and_threshing"
    assert eng._seasonal_context(0)["agricultural_intensity"] == 1.0
    assert eng.advance(7, allow_unresolved=True) == 7
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND day=7 AND event_type='occupation_work_cycle'", (rid,)) == 16
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND day=7 AND event_type='household_labor_allocation'", (rid,)) == 8
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND day=7 AND event_type='port_market_cycle'", (rid,)) == 1
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'")) - 1.35) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='charcoal'")) - 2.8) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")) - 0.08) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='fiber'")) - 3.38) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='textile_goods'")) - 0.08) < 1e-9


def test_packets_expose_current_seasonal_context(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(7, allow_unresolved=True) == 7
    job = _job_for(db, rid, "merchant_harbor_information_uncertainty")
    packet = compile_packet(db, job["job_id"])
    assert packet["seasonal_context"]["phase"] == "cereal_harvest_and_threshing"
    assert packet["seasonal_context"]["agricultural_intensity"] == 1.0
    assert "exact" in packet["seasonal_context"]["calendar_notice"]


def test_recurring_household_ritual_and_communal_feast_are_material(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='ritual_goods'"))
    assert eng.advance(30, allow_unresolved=True) == 30
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND day=30 AND event_type='household_ritual_observance'", (rid,)) == 8
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND day=30 AND event_type='communal_feast_calendar_due'", (rid,)) == 1
    feast = _job_for(db, rid, "communal_feast_contribution")
    assert feast is not None
    packet = compile_packet(db, feast["job_id"])
    assert "contribute_communal_feast" in packet["allowed_actions"]
    actor_house = packet["household"]["household_id"]
    grain_before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='grain'", (actor_house,)))
    ritual_before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='ritual_goods'", (actor_house,)))
    decision = {
        "decision_id": "DEC-TEST-FEAST",
        "actor_id": feast["actor_person_id"],
        "selected_intent": "make a bounded contribution without endangering household stores",
        "proposed_actions": [{"type": "contribute_communal_feast", "grain_amount": 0.4, "ritual_goods_amount": 0.2, "reason": "participate while preserving household reserves"}],
        "decisive_knowledge_or_belief_ids": [],
        "decision_basis_tags": ["ritual_obligation", "household_security", "reputation"],
        "declared_uncertainty": "Exact contribution norms are not reconstructed.",
    }
    assert eng.submit_decision(feast["job_id"], decision).ok
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='grain'", (actor_house,))) - (grain_before - 0.4)) < 1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='ritual_goods'", (actor_house,))) - (ritual_before - 0.2)) < 1e-9
    assert before - float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='ritual_goods'")) >= 0.05


def test_palace_labor_conflict_can_move_past_harvest_bottleneck(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(35, allow_unresolved=True) == 35
    job = _job_for(db, rid, "institutional_labor_conflict")
    assert job is not None and job["actor_person_id"] == "P13"
    packet = compile_packet(db, job["job_id"])
    assert packet["seasonal_context"]["agricultural_intensity"] == 1.0
    stakes = packet["scene"]["stakes"]
    decision = {
        "decision_id": "DEC-TEST-PALACE-RESCHEDULE",
        "actor_id": "P13",
        "selected_intent": "preserve harvest labor now and meet the institutional demand after the bottleneck",
        "proposed_actions": [{"type": "reschedule_palace_labor", "obligation_id": stakes["obligation_id"], "new_due_day": stakes["suggested_reschedule_day"], "reason": "current household harvest labor is time-sensitive"}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-LABOR-001-P13"],
        "decision_basis_tags": ["household_labor", "institutional_obligation", "seasonal_bottleneck"],
        "declared_uncertainty": "The rescheduling procedure is a bounded fixture, not reconstructed palace law.",
    }
    assert eng.submit_decision(job["job_id"], decision).ok
    assert int(db.scalar("SELECT due_day FROM obligations WHERE obligation_id=?", (stakes["obligation_id"],))) == stakes["suggested_reschedule_day"]
    assert eng.advance(stakes["suggested_reschedule_day"] - 35, allow_unresolved=True) == stakes["suggested_reschedule_day"] - 35
    assert db.scalar("SELECT status FROM obligations WHERE obligation_id=?", (stakes["obligation_id"],)) == "fulfilled"


def test_port_trade_commitment_is_delayed_material_exchange(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(42, allow_unresolved=True) == 42
    job = _job_for(db, rid, "port_trade_opportunity")
    assert job is not None and job["actor_person_id"] == "P3"
    packet = compile_packet(db, job["job_id"])
    silver_before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='silver'"))
    goods_before = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='trade_goods'"))
    decision = {
        "decision_id": "DEC-TEST-TRADE",
        "actor_id": "P3",
        "selected_intent": "commit a small amount while preserving household credit reserves",
        "proposed_actions": [{"type": "commit_trade_exchange", "silver_amount": 0.5, "reason": "bounded exposure despite incomplete shipping information"}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-TRADE-001-P3"],
        "decision_basis_tags": ["trade", "credit", "information_uncertainty"],
        "declared_uncertainty": "Exchange ratio and delay are fixture calibration.",
    }
    assert eng.submit_decision(job["job_id"], decision).ok
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='silver'")) - (silver_before - 0.5)) < 1e-9
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='trade_goods'")) == goods_before
    assert eng.advance(7, allow_unresolved=True) == 7
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='trade_goods'")) - (goods_before + 0.5)) < 1e-9


def test_craft_supply_pressure_emerges_from_consumed_input(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(56, allow_unresolved=True) == 56
    amount = float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    assert amount < 0.31
    job = _job_for(db, rid, "craft_supply_pressure")
    assert job is not None and job["actor_person_id"] == "P7"
    packet = compile_packet(db, job["job_id"])
    assert packet["scene"]["stakes"]["known_supplier_person_id"] == "P3"
    assert "request_resource" in packet["allowed_actions"]


def test_craft_supply_can_be_met_as_reciprocal_social_credit(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(56, allow_unresolved=True) == 56
    craft_job = _job_for(db, rid, "craft_supply_pressure")
    assert craft_job is not None
    request = {
        "decision_id": "DEC-TEST-CRAFT-REQUEST-CREDIT",
        "actor_id": "P7",
        "selected_intent": "ask the merchant household for a modest metal replenishment",
        "proposed_actions": [{
            "type": "request_resource", "target_person_id": "P3", "resource": "metal", "amount": 0.6,
            "reason": "keep the workshop supplied for recurring production"
        }],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P7"],
        "decision_basis_tags": ["craft_dependency"],
        "declared_uncertainty": "Production quantities are fixture calibration.",
    }
    assert eng.submit_decision(craft_job["job_id"], request).ok
    merchant_job = _job_for(db, rid, "resource_request")
    assert merchant_job is not None and merchant_job["actor_person_id"] == "P3"
    supply = {
        "decision_id": "DEC-TEST-METAL-SOCIAL-CREDIT",
        "actor_id": "P3",
        "selected_intent": "supply metal as open reciprocal social credit",
        "proposed_actions": [{
            "type": "transfer_resource", "target_household_id": "H-CRAFT", "social_target_person_id": "P7",
            "resource": "metal", "amount": 0.6, "create_reciprocal_obligation": True,
            "reciprocal_obligation_description": "Craft household owes a future reciprocal return for supplied metal."
        }],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P3", "K-LOCAL-TRADE-001-P3"],
        "decision_basis_tags": ["social_credit", "specialist_network"],
        "declared_uncertainty": "No fixed price, interest, or maturity is reconstructed.",
    }
    assert eng.submit_decision(merchant_job["job_id"], supply).ok
    obligation = db.one(
        "SELECT * FROM obligations WHERE obligation_type='reciprocal_exchange' AND obligor_person_id='P7' AND beneficiary_person_id='P3'"
    )
    assert obligation is not None and obligation["status"] == "active" and obligation["due_day"] is None
    assert db.scalar("SELECT COUNT(*) FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'") == 1
    assert db.scalar("SELECT COUNT(*) FROM relationships WHERE from_person_id='P7' AND to_person_id='P3'") == 1
    assert float(db.scalar("SELECT favors_given FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'")) == 1.0
    assert float(db.scalar("SELECT favors_owed FROM relationships WHERE from_person_id='P7' AND to_person_id='P3'")) == 1.0
    assert "reciprocal obligation" in db.scalar(
        "SELECT summary FROM memories WHERE person_id='P7' AND memory_type='resource_exchange' ORDER BY created_day DESC LIMIT 1"
    )


def test_routine_provisioning_is_neutral_without_shocks(world):
    db, _ = world
    rows = db.all("SELECT household_id,fixture_daily_food_need,fixture_weekly_receipt FROM households ORDER BY household_id")
    assert rows
    for row in rows:
        assert abs(float(row["fixture_weekly_receipt"]) - 7.0 * float(row["fixture_daily_food_need"])) < 1e-9


def test_reciprocal_social_credit_can_be_returned_from_occupational_output(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    assert eng.advance(56, allow_unresolved=True) == 56
    craft_job = _job_for(db, rid, "craft_supply_pressure")
    request = {
        "decision_id": "DEC-TEST-RETURN-REQUEST", "actor_id": "P7",
        "selected_intent": "request metal",
        "proposed_actions": [{"type": "request_resource", "target_person_id": "P3", "resource": "metal", "amount": 0.6, "reason": "keep workshop supplied"}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P7"], "decision_basis_tags": ["craft_dependency"],
        "declared_uncertainty": "fixture quantities",
    }
    assert eng.submit_decision(craft_job["job_id"], request).ok
    merchant_job = _job_for(db, rid, "resource_request")
    supply = {
        "decision_id": "DEC-TEST-RETURN-SUPPLY", "actor_id": "P3",
        "selected_intent": "supply as reciprocal credit",
        "proposed_actions": [{"type": "transfer_resource", "target_household_id": "H-CRAFT", "social_target_person_id": "P7", "resource": "metal", "amount": 0.6, "create_reciprocal_obligation": True}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P3", "K-LOCAL-TRADE-001-P3"], "decision_basis_tags": ["social_credit"],
        "declared_uncertainty": "no fixed price or maturity",
    }
    assert eng.submit_decision(merchant_job["job_id"], supply).ok
    oid = db.scalar("SELECT obligation_id FROM obligations WHERE obligation_type='reciprocal_exchange' AND obligor_person_id='P7' AND beneficiary_person_id='P3'")
    assert oid
    assert eng.advance(30, allow_unresolved=True) == 30
    return_job = _job_for(db, rid, "reciprocal_return_opportunity")
    assert return_job is not None and return_job["actor_person_id"] == "P7"
    return_packet = compile_packet(db, return_job["job_id"])
    assert any(o["obligation_id"] == oid for o in return_packet["active_obligations"])
    give_back = {
        "decision_id": "DEC-TEST-RETURN-FULFILL", "actor_id": "P7",
        "selected_intent": "return workshop output and clear the reciprocal obligation",
        "proposed_actions": [{"type": "transfer_resource", "target_household_id": "H-MERCH", "social_target_person_id": "P3", "resource": "finished_metalwork", "amount": 0.3, "fulfills_obligation_id": oid}],
        "decisive_knowledge_or_belief_ids": ["K-LOCAL-P7"], "decision_basis_tags": ["reciprocity", "craft_output"],
        "declared_uncertainty": "return amount is fixture calibration, not a fixed equivalence",
    }
    assert eng.submit_decision(return_job["job_id"], give_back).ok
    assert db.scalar("SELECT status FROM obligations WHERE obligation_id=?", (oid,)) == "fulfilled"
    assert float(db.scalar("SELECT favors_owed FROM relationships WHERE from_person_id='P7' AND to_person_id='P3'")) == 0.0
    assert float(db.scalar("SELECT favors_given FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'")) == 0.0
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='finished_metalwork'")) == 0.3
