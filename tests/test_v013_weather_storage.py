from pathlib import Path
import json
import pytest
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions
from bronze_world.cognition import compile_packet

ROOT=Path(__file__).resolve().parents[1]

def _scenario():
    d=json.loads((ROOT/'scenarios/ugarit_1350/scenario.json').read_text())
    return d

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/'w.sqlite')
    rid=init_fixture(db,ROOT,1701,scenario_override=_scenario())
    yield db,rid
    db.close()

def _job(db,trigger,actor):
    return db.one("SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid DESC LIMIT 1",(trigger,actor))

def _submit(eng,job,did,actor,action):
    env={'decision_id':did,'actor_id':actor,'selected_intent':'bounded response','proposed_actions':[action],'decisive_knowledge_or_belief_ids':[],'decision_basis_tags':['weather_storage'],'declared_uncertainty':'fixture calibration'}
    r=eng.submit_decision(job['job_id'],env); assert r.ok,r.errors

def test_v012_replay_remains_exact_under_v013_repo(tmp_path):
    src=ROOT/'state'/'ugarit_living_v012.sqlite'
    if not src.exists(): pytest.skip('accepted v012 DB unavailable')
    r=replay_recorded_decisions(ROOT,src,tmp_path/'v012.sqlite',target_day=443)
    assert r['exact_match'] and r['recorded_decisions_applied']==144 and r['new_cognition_calls']==0

def test_weather_storage_protection_affects_only_exposed_produce(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=444 WHERE run_id=?",(rid,))
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES ('H-FARM','seasonal_produce',0.20,'abstract_fixture_unit','ASM-FIXTURE-034')")
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES ('H-FARM','stored_seasonal_goods',0.72,'abstract_fixture_unit','ASM-FIXTURE-021')")
        grain=float(con.execute("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='grain'").fetchone()[0])
    eng.detect_situations(444)
    job=_job(db,'local_storage_weather_exposure','P1'); assert job
    pkt=compile_packet(db,job['job_id']); assert pkt['scene']['stakes']['exposed_seasonal_produce']==0.20
    before_stored=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='stored_seasonal_goods'"))
    before_grain=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='grain'"))
    _submit(eng,job,'DEC-WX-PROTECT','P1',{'type':'protect_exposed_stores','labor_days':1})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='seasonal_produce'"))-0.19)<1e-9
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='stored_seasonal_goods'"))==before_stored
    assert float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='grain'"))==before_grain

def test_weather_storage_unprotected_loss_is_larger(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=444 WHERE run_id=?",(rid,))
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES ('H-DEPEND','seasonal_produce',0.20,'abstract_fixture_unit','ASM-FIXTURE-034')")
    eng.detect_situations(444)
    job=_job(db,'local_storage_weather_exposure','P13'); assert job
    _submit(eng,job,'DEC-WX-LOSS','P13',{'type':'accept_weather_storage_loss'})
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-DEPEND' AND resource_type='seasonal_produce'"))-0.14)<1e-9


def test_wait_on_recycling_choice_delays_reconsideration_fourteen_days(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=444 WHERE run_id=?",(rid,))
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES ('H-CRAFT','metal',0.01,'abstract_fixture_unit','ASM-FIXTURE-027')")
        con.execute("INSERT OR REPLACE INTO resource_stocks VALUES ('H-CRAFT','finished_metalwork',0.25,'abstract_fixture_unit','ASM-FIXTURE-027')")
        con.execute("INSERT OR IGNORE INTO propositions VALUES ('PROP-METAL-NONE-001','No usable lot now.','simulation_contingent','{}')")
        con.execute("INSERT OR REPLACE INTO knowledge VALUES ('K-TEST-NOLOT','P7','PROP-METAL-NONE-001',444,'message','MSG-TEST','[]','direct',0.9,'ordinary',NULL)")
    eng.detect_situations(444)
    job=_job(db,'market_unavailable_recycling_choice','P7'); assert job
    _submit(eng,job,'DEC-WAIT-RECYCLE','P7',{'type':'wait','reason':'preserve finished stock'})
    for d in range(445,458):
        eng.detect_situations(d)
        assert _job(db,'market_unavailable_recycling_choice','P7') is None
    eng.detect_situations(458)
    assert _job(db,'market_unavailable_recycling_choice','P7') is not None
