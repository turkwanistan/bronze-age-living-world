from __future__ import annotations
import json
from pathlib import Path
import pytest
from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB, canonical_json
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions

ROOT=Path(__file__).resolve().parents[1]
V015_HASH='a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0'


def test_v015_replay_remains_exact_under_v020_packet_policy(tmp_path):
    src=ROOT/'state/ugarit_living_v015.sqlite'
    if not src.exists(): pytest.skip('accepted v015 DB unavailable')
    r=replay_recorded_decisions(ROOT,src,tmp_path/'v015.sqlite',target_day=462)
    assert r['recorded_decisions_applied']==157 and r['new_cognition_calls']==0
    assert r['source_hash']==V015_HASH and r['rebuilt_hash']==V015_HASH and r['exact_match'] is True


def test_old_relationship_relevant_refusal_memory_survives_after_recent_window(tmp_path):
    db=WorldDB(tmp_path/'w.sqlite')
    try:
        rid=init_fixture(db,ROOT,1701)
        eng=WorldEngine(db,rid)
        with db.transaction() as con:
            con.execute('UPDATE runs SET current_day=520 WHERE run_id=?',(rid,))
            eng._ensure_relationship_pair(con,'P3','P7',relationship_type='exchange_contact')
            con.execute("UPDATE relationships SET conflicts=1,trust=.77,respect=.67 WHERE from_person_id='P3' AND to_person_id='P7'")
            # One old, relationship-relevant refusal decision is deliberately crowded out
            # by twelve newer high-salience memories and is older than the v008 30-day window.
            refusal_event=eng._event(
                con,400,'proposal_refused',actors=['P3','P7'],
                payload={'reason':'last usable metal reserve'},discriminator='v020-refusal')
            con.execute("INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                'MEM-V020-REFUSAL','P3','decision',
                'Refused P7 because the household was down to its last usable metal reserve.',
                refusal_event,400,.5,.60,.65,.60,canonical_json({'validation':'v020'})))
            for i in range(12):
                con.execute("INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                    f'MEM-V020-CROWD-{i}','P3','resource_exchange',f'High-salience later exchange memory {i}',
                    None,500+i,.5,.90,.80,.70,'{}'))
            unrelated_event=eng._event(
                con,450,'proposal_refused',actors=['P3','P6'],
                payload={'reason':'unrelated relationship dispute'},discriminator='v020-unrelated')
            con.execute("INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                'MEM-V020-UNRELATED','P3','decision',
                'Refused an unrelated proposal from P6.',unrelated_event,450,.5,.59,.99,.99,'{}'))
            sid='SCENE-V020-MEMORY'
            place=con.execute("SELECT current_place_id FROM persons WHERE person_id='P3'").fetchone()[0]
            con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",(sid,rid,520,place,'economic','resource_request',canonical_json({'requester_person_id':'P7','requester_household_id':'H-CRAFT','resource':'metal','amount':.12}),'{}','{}',canonical_json(['I-MARKET']),'open'))
            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,'P3','decision_actor'))
        jid=eng.enqueue_job('SCENE-V020-MEMORY','P3',['transfer_resource','refuse_proposal','communicate'])
        packet=compile_packet(db,jid)
        ids={m['memory_id'] for m in packet['relevant_memories']}
        assert 'MEM-V020-REFUSAL' in ids
        assert len([m for m in packet['relevant_memories'] if m['memory_id'].startswith('MEM-V020-REFUSAL')])==1
        assert 'MEM-V020-UNRELATED' not in ids
    finally:
        db.close()
