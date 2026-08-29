from pathlib import Path
import json
import pytest
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions

ROOT=Path(__file__).resolve().parents[1]
V014_HASH='6e92d7ab618cc014b5a6668b63753c46780745d4542e272b0ca8580f3dd1c5a2'

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/'w.sqlite')
    scenario=json.loads((ROOT/'scenarios/ugarit_1350/scenario.json').read_text())
    rid=init_fixture(db,ROOT,1701,scenario_override=scenario)
    eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=460 WHERE run_id=?",(rid,))
        for i in range(60):
            eng._event(con,i+1,'occupation_work_cycle',actors=['P11'],rules=['ASM-FIXTURE-008'],payload={'roles':['sailor','porter']},discriminator=f'P11-test-{i}')
        eng._event(con,100,'message_sent',actors=['P11'],payload={'sender_intent':'report','recipient':'P3'},discriminator='P11-test-report')
    yield db,rid
    db.close()

def _job(db,trigger,actor):
    return db.one("SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid DESC LIMIT 1",(trigger,actor))

def _submit(eng,job,did,actor,action):
    env={'decision_id':did,'actor_id':actor,'selected_intent':did,'proposed_actions':[action],
         'decisive_knowledge_or_belief_ids':[],'decision_basis_tags':['adult_work_progression'],
         'declared_uncertainty':'Threshold and title are fixture calibration; legal status and household remain unchanged.'}
    r=eng.submit_decision(job['job_id'],env); assert r.ok,r.errors

def _request(eng,db):
    eng.detect_situations(460)
    p11=_job(db,'harbor_role_progression_review','P11'); assert p11
    _submit(eng,p11,'DEC-HARBOR-REQUEST','P11',{'type':'request_harbor_role_progression','reviewer_person_id':'P12','requested_role':'harbor_coordinator','reason':'sustained harbor and information work'})
    p12=_job(db,'harbor_role_progression_request','P12'); assert p12
    return p12

def test_v014_replay_remains_exact_under_v015_repo(tmp_path):
    src=ROOT/'state'/'ugarit_living_v014.sqlite'
    if not src.exists(): pytest.skip('accepted v014 DB unavailable')
    r=replay_recorded_decisions(ROOT,src,tmp_path/'v014.sqlite',target_day=459)
    assert r['recorded_decisions_applied']==153 and r['new_cognition_calls']==0
    assert r['source_hash']==V014_HASH and r['rebuilt_hash']==V014_HASH and r['exact_match'] is True

def test_adult_harbor_progression_changes_specialization_not_legal_or_household(world):
    db,rid=world; eng=WorldEngine(db,rid); p12=_request(eng,db)
    _submit(eng,p12,'DEC-HARBOR-ACCEPT','P12',{'type':'accept_harbor_role_progression','worker_person_id':'P11','old_role':'porter','new_role':'harbor_coordinator','reason':'sustained harbor coordination and information work justify revising our division of labor'})
    active=[r['name'] for r in db.all("SELECT r.name FROM person_roles pr JOIN roles r USING(role_id) WHERE pr.person_id='P11' AND pr.end_day IS NULL ORDER BY r.name")]
    assert active==['harbor_coordinator','sailor']
    old=db.one("SELECT end_day FROM person_roles WHERE person_id='P11' AND role_id='R-PORTER'"); assert old['end_day']==460
    p=db.one("SELECT legal_status FROM persons WHERE person_id='P11'"); assert p['legal_status']=='free_laborer'
    hm=db.one("SELECT household_id,membership_role FROM household_memberships WHERE person_id='P11' AND until_day IS NULL"); assert hm['household_id']=='H-HARBOR' and hm['membership_role']=='senior'
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='adult_harbor_role_progressed'")==1

def test_household_reviewer_can_refuse_harbor_progression(world):
    db,rid=world; eng=WorldEngine(db,rid); p12=_request(eng,db)
    _submit(eng,p12,'DEC-HARBOR-REFUSE','P12',{'type':'refuse_proposal','reason':'keep the current porter/sailor division of labor for now'})
    active=[r['name'] for r in db.all("SELECT r.name FROM person_roles pr JOIN roles r USING(role_id) WHERE pr.person_id='P11' AND pr.end_day IS NULL ORDER BY r.name")]
    assert active==['porter','sailor']
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='adult_harbor_role_progressed'")==0
