from __future__ import annotations
import json
from pathlib import Path
import pytest
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.cognition import compile_packet
from bronze_world.replay import replay_recorded_decisions

ROOT=Path(__file__).resolve().parents[1]
V011_HASH='0b55f95796bc28a9995b3e63ab35c0c5f951c884fe99ad3ad2ca291eb0ed0102'

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/'world.sqlite'); rid=init_fixture(db,ROOT,1701)
    try: yield db,rid
    finally: db.close()

def _job(db,trigger,actor):
    return db.one("SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",(trigger,actor))

def _submit(eng,job,did,action):
    env={'decision_id':did,'actor_id':'P7','selected_intent':did,'proposed_actions':[action],
         'decisive_knowledge_or_belief_ids':['K-LOCAL-WORKSHOP-TOOLS-001-P7'],'decision_basis_tags':['regression'],
         'declared_uncertainty':'Failure timing, repair material and duration are fixture calibration.'}
    r=eng.submit_decision(job['job_id'],env); assert r.ok,r.errors

def test_v011_replay_remains_exact_under_v012_repo(tmp_path):
    src=ROOT/'state'/'ugarit_living_v011.sqlite'
    if not src.exists(): pytest.skip('accepted v011 DB unavailable')
    r=replay_recorded_decisions(ROOT,src,tmp_path/'v011.sqlite',target_day=421)
    assert r['recorded_decisions_applied']==137 and r['new_cognition_calls']==0
    assert r['source_hash']==V011_HASH and r['rebuilt_hash']==V011_HASH and r['exact_match'] is True

def test_tool_failure_blocks_viable_master_cycle_and_repair_restores_later_work(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=434 WHERE run_id=?",(rid,))
        con.execute("UPDATE resource_stocks SET amount=0.16 WHERE household_id='H-CRAFT' AND resource_type='metal'")
        con.execute("UPDATE resource_stocks SET amount=0.70 WHERE household_id='H-CRAFT' AND resource_type='charcoal'")
        con.execute("UPDATE resource_stocks SET amount=0.47 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
        con.execute("UPDATE resource_stocks SET amount=1.0 WHERE household_id='H-CRAFT' AND resource_type='workshop_tool_condition'")
        eng._apply_recurring_lifeways(con,434)
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='workshop_tool_condition'"))==0.0
    # The otherwise-viable 0.15/0.20 master cycle was blocked before consuming inputs.
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))-0.16)<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='charcoal'"))-0.70)<1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='workshop_tool_damage'")==1
    eng.detect_situations(434)
    job=_job(db,'workshop_tool_repair_pressure','P7'); assert job
    pkt=compile_packet(db,job['job_id']); assert pkt['scene']['stakes']['repair_finished_metalwork_input']==0.10
    _submit(eng,job,'DEC-TOOL-REPAIR',{'type':'repair_workshop_tool','finished_metalwork_input':0.10,'repair_days':1})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"))-0.37)<1e-9
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_workshop_tool_repair'")==1
    assert eng.advance(1,allow_unresolved=True)==1
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='workshop_tool_condition'"))-1.0)<1e-9
    # Later weekly work can use the same inputs that damage had prevented from being consumed.
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=441 WHERE run_id=?",(rid,))
        eng._apply_recurring_lifeways(con,441)
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))-0.01)<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='charcoal'"))-0.50)<1e-9
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")) >= 0.45-1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE event_type='workshop_tool_repair_completed'")==1
