from pathlib import Path
import json
import pytest
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions

ROOT=Path(__file__).resolve().parents[1]
V013_HASH='8254bd35f77fa492dc28c9d3b66cde982c0da08f5310f20a062ae6b14160906b'

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/'w.sqlite')
    scenario=json.loads((ROOT/'scenarios/ugarit_1350/scenario.json').read_text())
    rid=init_fixture(db,ROOT,1701,scenario_override=scenario)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=459 WHERE run_id=?",(rid,))
        con.execute("UPDATE household_memberships SET until_day=150 WHERE household_id='H-RITUAL' AND person_id='P10' AND until_day IS NULL")
        con.execute("INSERT OR REPLACE INTO household_memberships VALUES ('H-WIDOW','P10','married_in_adult',150,NULL)")
        con.execute("UPDATE resource_stocks SET amount=3.20 WHERE household_id='H-WIDOW' AND resource_type='silver'")
        con.execute("INSERT INTO property_preferences VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(
            'PREF-TEST',rid,'H-WIDOW','P15','P16','care_informed_priority','household_property_if_later_negotiated',214,None,'active',
            json.dumps({'care_history':True}),json.dumps({'assumption_id':'ASM-FIXTURE-023'})))
    yield db,rid
    db.close()

def _job(db,trigger,actor):
    return db.one("SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid DESC LIMIT 1",(trigger,actor))

def _submit(eng,job,did,actor,action):
    env={'decision_id':did,'actor_id':actor,'selected_intent':did,'proposed_actions':[action],
         'decisive_knowledge_or_belief_ids':[],'decision_basis_tags':['property_use_regression'],
         'declared_uncertainty':'All local terms are fixture calibration; no inheritance or ownership transfer is implied.'}
    r=eng.submit_decision(job['job_id'],env); assert r.ok,r.errors

def _to_steward_consent(db,rid):
    eng=WorldEngine(db,rid); eng.detect_situations(459)
    p15=_job(db,'household_property_reserve_proposal','P15'); assert p15
    _submit(eng,p15,'DEC-PROP-PROPOSE','P15',{'type':'propose_household_property_reserve','reviewer_person_id':'P10','steward_person_id':'P16','reserve_amount':0.80,'purpose':'household_property_maintenance'})
    p10=_job(db,'household_property_reserve_review','P10'); assert p10
    _submit(eng,p10,'DEC-PROP-COUNTER','P10',{'type':'counter_household_property_reserve','steward_person_id':'P16','reserve_amount':0.40,'purpose':'household_property_maintenance','joint_approval_required':True})
    p15b=_job(db,'household_property_reserve_counter_review','P15'); assert p15b
    _submit(eng,p15b,'DEC-PROP-ACCEPT-COUNTER','P15',{'type':'accept_household_property_counter','steward_person_id':'P16','reserve_amount':0.40,'joint_approval_required':True})
    p16=_job(db,'household_property_stewardship_consent','P16'); assert p16
    return eng,p16

def test_v013_replay_remains_exact_under_v014_repo(tmp_path):
    src=ROOT/'state'/'ugarit_living_v013.sqlite'
    if not src.exists(): pytest.skip('accepted v013 DB unavailable')
    r=replay_recorded_decisions(ROOT,src,tmp_path/'v013.sqlite',target_day=458)
    assert r['recorded_decisions_applied']==149 and r['new_cognition_calls']==0
    assert r['source_hash']==V013_HASH and r['rebuilt_hash']==V013_HASH and r['exact_match'] is True

def test_countered_property_reserve_requires_steward_consent_and_earmarks_not_transfers(world):
    db,rid=world
    before=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))
    eng,p16=_to_steward_consent(db,rid)
    assert db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='property_maintenance_reserve'") is None
    _submit(eng,p16,'DEC-PROP-STEWARD-ACCEPT','P16',{'type':'accept_property_stewardship','reserve_amount':0.40,'joint_approval_required':True,'purpose':'household_property_maintenance'})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))-(before-0.40))<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='property_maintenance_reserve'"))-0.40)<1e-9
    o=db.one("SELECT * FROM obligations WHERE obligation_type='household_property_stewardship' AND status='active'"); assert o
    prov=json.loads(o['provenance_json']); assert prov['joint_approval_required'] is True and prov['reviewer_person_id']=='P10'
    pref=db.one("SELECT * FROM property_preferences WHERE preference_id='PREF-TEST'"); assert pref['status']=='active'
    assert db.scalar("SELECT COUNT(*) FROM marriages")==5  # no new marriage/succession state

def test_steward_can_decline_after_household_counter_without_reserve(world):
    db,rid=world
    before=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))
    eng,p16=_to_steward_consent(db,rid)
    _submit(eng,p16,'DEC-PROP-STEWARD-DECLINE','P16',{'type':'decline_property_stewardship','reason':'I do not accept responsibility for this reserve under the proposed terms.'})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='silver'"))-before)<1e-9
    assert db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-WIDOW' AND resource_type='property_maintenance_reserve'") is None
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE obligation_type='household_property_stewardship' AND status='active'")==0
