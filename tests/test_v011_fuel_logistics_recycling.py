from __future__ import annotations
import json
from pathlib import Path
import pytest
from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions

ROOT=Path(__file__).resolve().parents[1]
V010_HASH='e2720f1e974c23901ce746f0ffa2d5afbf7d4ce65e317d51653b899b8634c661'

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/'world.sqlite'); rid=init_fixture(db,ROOT,1701)
    try: yield db,rid
    finally: db.close()

def _job(db,trigger,actor):
    return db.one("SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",(trigger,actor))

def _submit(eng,job,did,actor,action,knowledge=None):
    r=eng.submit_decision(job['job_id'],{'decision_id':did,'actor_id':actor,'selected_intent':did,'proposed_actions':[action],
        'decisive_knowledge_or_belief_ids':knowledge or [],'decision_basis_tags':['regression'],
        'declared_uncertainty':'All quantities, identities, timing and exchange terms in this regression are explicit fixture calibration.'})
    assert r.ok,r.errors

def test_v010_replay_remains_exact_under_v011_repo(tmp_path):
    source=ROOT/'state'/'ugarit_living_v010.sqlite'
    if not source.exists(): pytest.skip('accepted v010 DB unavailable')
    r=replay_recorded_decisions(ROOT,source,tmp_path/'v010.sqlite',target_day=385)
    assert r['recorded_decisions_applied']==124 and r['new_cognition_calls']==0
    assert r['source_hash']==V010_HASH and r['rebuilt_hash']==V010_HASH and r['exact_match'] is True

def test_fuel_haul_can_be_refused_in_harvest_then_accepted_in_later_phase(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=386 WHERE run_id=?",(rid,))
        con.execute("UPDATE resource_stocks SET amount=0.40 WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'")
        con.execute("UPDATE resource_stocks SET amount=3.40 WHERE household_id='H-CRAFT' AND resource_type='silver'")
    eng.detect_situations(386)
    offer=_job(db,'workshop_fuel_procurement_pressure','P7'); assert offer
    pp=compile_packet(db,offer['job_id']); assert pp['scene']['stakes']['seasonal_context']['agricultural_intensity']==1.0
    _submit(eng,offer,'DEC-FUEL-REQ-HARVEST','P7',{'type':'request_fuel_haul','target_person_id':'P16','fuel_feedstock_amount':0.80,'silver_payment':0.20,'service_days':1})
    response=_job(db,'fuel_haul_request','P16'); assert response
    _submit(eng,response,'DEC-FUEL-DECLINE-HARVEST','P16',{'type':'decline_fuel_haul','reason':'harvest transport and household labor are already at their peak'})
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE obligation_type='fixture_fuel_haul'")==0
    # New agricultural phase permits one new bounded offer rather than daily nagging.
    with db.transaction() as con: con.execute("UPDATE runs SET current_day=420 WHERE run_id=?",(rid,))
    eng.detect_situations(420)
    later=_job(db,'workshop_fuel_procurement_pressure','P7'); assert later
    lp=compile_packet(db,later['job_id']); assert lp['scene']['stakes']['seasonal_context']['agricultural_intensity']<0.85
    _submit(eng,later,'DEC-FUEL-REQ-SUMMER','P7',{'type':'request_fuel_haul','target_person_id':'P16','fuel_feedstock_amount':0.80,'silver_payment':0.20,'service_days':1})
    accept=_job(db,'fuel_haul_request','P16'); assert accept
    _submit(eng,accept,'DEC-FUEL-ACCEPT-SUMMER','P16',{'type':'accept_fuel_haul','requester_person_id':'P7','fuel_feedstock_amount':0.80,'silver_payment':0.20,'service_days':1})
    before_feed=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'"))
    before_craft_silver=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='silver'"))
    before_widow_silver=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))
    assert eng.advance(1,allow_unresolved=True)==1
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='fuel_feedstock'"))-(before_feed+0.80))<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='silver'"))-(before_craft_silver-0.20))<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))-(before_widow_silver+0.20))<1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='fuel_haul_completed'")==1

def test_no_lot_report_is_private_until_delivery_then_recycling_is_material(world):
    db,rid=world; eng=WorldEngine(db,rid)
    # Synthetic post-v010 state: disrupted lot completed, established P7<->P12 market contact, metal low.
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=386 WHERE run_id=?",(rid,))
        con.execute("UPDATE resource_stocks SET amount=0.06 WHERE household_id='H-CRAFT' AND resource_type='metal'")
        con.execute("UPDATE resource_stocks SET amount=0.87 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
        eng._ensure_relationship_pair(con,'P7','P12',relationship_type='market_contact')
        con.execute("UPDATE relationships SET relationship_type='market_contact' WHERE (from_person_id='P7' AND to_person_id='P12') OR (from_person_id='P12' AND to_person_id='P7')")
        eng._event(con,385,'alternate_metal_exchange_completed',actors=['P12','P7'],rules=['ASM-FIXTURE-030','RULE-ALTERNATE-METAL-SOURCING-001'],payload={'synthetic_regression':True},discriminator='v011-no-lot')
    eng.detect_situations(386)
    inquiry=_job(db,'second_repeat_alternate_metal_inquiry_opportunity','P7'); assert inquiry
    pkt=compile_packet(db,inquiry['job_id']); assert not any(k['proposition_id']=='PROP-METAL-NONE-001' for k in pkt['admissible_knowledge'])
    _submit(eng,inquiry,'DEC-NOLOT-INQUIRE','P7',{'type':'send_message','target_person_id':'P12','sender_intent':'inquiry','content':'Is any usable raw-metal lot actually available now?'})
    # Ignore unrelated synthetic jump jobs; this test is about message provenance.
    assert eng.advance(1,allow_unresolved=True)==1
    reply=_job(db,'information_inquiry_received','P12'); assert reply
    rp=compile_packet(db,reply['job_id']); kid=next(k['knowledge_id'] for k in rp['admissible_knowledge'] if k['proposition_id']=='PROP-METAL-NONE-001')
    _submit(eng,reply,'DEC-NOLOT-REPORT','P12',{'type':'send_message','target_person_id':'P7','sender_intent':'report','proposition_id':'PROP-METAL-NONE-001','content':'The same contact has no additional usable raw-metal lot available now.'},[kid])
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-NONE-001'")==0
    assert eng.advance(1,allow_unresolved=True)==1
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-NONE-001'")==1
    eng.detect_situations(388)
    recycle=_job(db,'market_unavailable_recycling_choice','P7'); assert recycle
    before_f=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")); before_m=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    _submit(eng,recycle,'DEC-NOLOT-RECYCLE','P7',{'type':'recycle_finished_metalwork','input_finished_metalwork':0.20,'output_metal':0.12})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"))-(before_f-0.20))<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))-(before_m+0.12))<1e-9


def test_market_unavailable_recycling_requires_fourteen_days_between_uses(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=392 WHERE run_id=?",(rid,))
        con.execute("UPDATE resource_stocks SET amount=0.03 WHERE household_id='H-CRAFT' AND resource_type='metal'")
        con.execute("UPDATE resource_stocks SET amount=0.75 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
        con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",('K-TEST-NOLOT','P7','PROP-METAL-NONE-001',388,'message','MSG-TEST','[]','direct',.9,'ordinary',None))
        eng._event(con,388,'finished_metalwork_recycled',actors=['P7'],rules=['ASM-FIXTURE-027'],payload={'test':True},discriminator='cadence-test')
    eng.detect_situations(392)
    assert _job(db,'market_unavailable_recycling_choice','P7') is None
    with db.transaction() as con: con.execute("UPDATE runs SET current_day=402 WHERE run_id=?",(rid,))
    eng.detect_situations(402)
    assert _job(db,'market_unavailable_recycling_choice','P7') is not None

def test_v011_craft_threshold_tolerates_float_dust_at_exact_fixture_cycle(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=406 WHERE run_id=?",(rid,))
        con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-CRAFT' AND resource_type='metal'",(0.14999999999999997,))
        con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-CRAFT' AND resource_type='charcoal'",(0.20,))
        before=float(con.execute("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'").fetchone()[0])
        eng._apply_recurring_lifeways(con,406)
    after=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"))
    metal=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))
    assert after >= before + 0.08 - 1e-9
    assert metal >= -1e-12 and metal < 1e-9
