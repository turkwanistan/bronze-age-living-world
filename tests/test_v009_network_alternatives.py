from __future__ import annotations

from pathlib import Path

import pytest

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.replay import replay_recorded_decisions

ROOT = Path(__file__).resolve().parents[1]
V008_HASH = "66afa78360be1ba12b67639e844aee71079480d1df562df45f450e514796f6ce"


def _job(db, trigger: str, actor: str):
    return db.one(
        "SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",
        (trigger, actor),
    )


def _submit(eng, job, did, actor, action, knowledge=None):
    result=eng.submit_decision(job["job_id"],{
        "decision_id":did,"actor_id":actor,"selected_intent":did,
        "proposed_actions":[action],"decisive_knowledge_or_belief_ids":knowledge or [],
        "decision_basis_tags":["regression"],
        "declared_uncertainty":"All exact recycling, market terms, identities, and delays are fixture calibration rather than historical prices or shipments.",
    })
    assert result.ok, result.errors


def _prepare_post_refusal(world, day=364):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=? WHERE run_id=?",(day,rid))
        con.execute("UPDATE resource_stocks SET amount=.03 WHERE household_id='H-CRAFT' AND resource_type='metal'")
        con.execute("UPDATE resource_stocks SET amount=.63 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
        con.execute("UPDATE resource_stocks SET amount=.15 WHERE household_id='H-MERCH' AND resource_type='metal'")
        eng._ensure_relationship_pair(con,"P7","P3",relationship_type="exchange_contact")
        con.execute("UPDATE relationships SET conflicts=1,trust=.83,respect=.61 WHERE from_person_id='P7' AND to_person_id='P3'")
        con.execute("UPDATE relationships SET conflicts=1,trust=.77,respect=.67 WHERE from_person_id='P3' AND to_person_id='P7'")
        eng._event(con,308,"proposal_refused",actors=["P3","P7"],payload={"reason":"remaining metal stock too low"},discriminator="v009-test-refusal")
    eng.detect_situations(day)
    job=_job(db,"workshop_supply_alternatives","P7")
    assert job is not None
    return db,rid,eng,job


def test_v008_replay_remains_exact_under_v009_repo(tmp_path):
    source=ROOT/"state"/"ugarit_living_v008.sqlite"
    if not source.exists(): pytest.skip("host-local accepted v008 database is not present")
    result=replay_recorded_decisions(ROOT,source,tmp_path/"v008_replay.sqlite",target_day=360)
    assert result["recorded_decisions_applied"]==106
    assert result["new_cognition_calls"]==0
    assert result["source_hash"]==V008_HASH
    assert result["rebuilt_hash"]==V008_HASH
    assert result["exact_match"] is True


def test_finished_metalwork_recycling_is_lossy_and_material(world):
    db,rid,eng,job=_prepare_post_refusal(world)
    packet=compile_packet(db,job["job_id"])
    assert packet["scene"]["stakes"]["recycle_input_finished_metalwork"]==.20
    assert packet["scene"]["stakes"]["recycle_output_metal"]==.12
    _submit(eng,job,"DEC-V009-RECYCLE","P7",{
        "type":"recycle_finished_metalwork","input_finished_metalwork":.20,"output_metal":.12,
        "reason":"sacrifice finished output to restart one bounded work cycle without pressuring the exhausted supplier",
    },["K-LOCAL-RECYCLE-001-P7"])
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"))-.43)<1e-9
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'"))-.15)<1e-9
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='finished_metalwork_recycled'",(rid,))==1


def test_alternate_metal_source_requires_two_delayed_information_hops(world):
    db,rid,eng,job=_prepare_post_refusal(world)
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id IN ('PROP-METAL-ALT-001','PROP-METAL-TERMS-001')")==0
    _submit(eng,job,"DEC-V009-INTRO-REQUEST","P7",{
        "type":"request_market_introduction","target_person_id":"P3","requested_contact_person_id":"P11",
        "reason":"seek a new information path rather than repeat the refused metal request",
    },["K-LOCAL-ALT-METAL-001-P7"])
    p3=_job(db,"market_introduction_request","P3"); assert p3 is not None
    _submit(eng,p3,"DEC-V009-INTRO-GRANT","P3",{
        "type":"grant_market_introduction","requester_person_id":"P7","contact_person_id":"P11",
        "reason":"introduce a proven counterparty to a harbor contact without promising supply",
    },["K-LOCAL-ALT-METAL-001-P3"])
    inquiry=_job(db,"harbor_metal_inquiry_opportunity","P7"); assert inquiry is not None
    _submit(eng,inquiry,"DEC-V009-P11-INQUIRY","P7",{
        "type":"send_message","target_person_id":"P11","content":"Do your harbor contacts know of another small raw-metal lot I could seek terms for?","sender_intent":"inquiry",
    })
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-ALT-001'")==0
    eng.advance(1,allow_unresolved=True)
    p11=_job(db,"information_inquiry_received","P11"); assert p11 is not None
    _submit(eng,p11,"DEC-V009-P11-REPORT","P11",{
        "type":"send_message","target_person_id":"P7","content":"A market-side contact reports that Dagan-beli may be able to arrange one small raw-metal lot on delayed terms.",
        "sender_intent":"report","proposition_id":"PROP-METAL-ALT-001",
    },["K-METAL-ALT-P11"])
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-ALT-001'")==0
    eng.advance(1,allow_unresolved=True)
    lead=_job(db,"alternate_metal_lead_received","P7"); assert lead is not None
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-ALT-001'")==1
    _submit(eng,lead,"DEC-V009-P12-INQUIRY","P7",{
        "type":"send_message","target_person_id":"P12","content":"Abdi-Rashap says you may know a small raw-metal lot. What terms are actually available?","sender_intent":"inquiry",
    },[compile_packet(db,lead["job_id"])["scene"]["stakes"]["lead_knowledge_id"]])
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-TERMS-001'")==0
    eng.advance(1,allow_unresolved=True)
    p12=_job(db,"information_inquiry_received","P12"); assert p12 is not None
    _submit(eng,p12,"DEC-V009-P12-REPORT","P12",{
        "type":"send_message","target_person_id":"P7","content":"I can arrange one small lot: 0.30 silver now for 0.30 metal after three days in fixture terms.",
        "sender_intent":"report","proposition_id":"PROP-METAL-TERMS-001",
    },["K-METAL-TERMS-P12"])
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-TERMS-001'")==0
    eng.advance(1,allow_unresolved=True)
    offer=_job(db,"alternate_metal_exchange_offer","P7"); assert offer is not None
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-TERMS-001'")==1
    silver_before=float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='silver'"))
    _submit(eng,offer,"DEC-V009-ALT-ACCEPT","P7",{
        "type":"accept_alternate_metal_exchange","silver_cost":.30,"metal_amount":.30,"delivery_days":3,
        "reason":"pay for the alternate lot now that actual terms have arrived through the network",
    },[compile_packet(db,offer["job_id"])["scene"]["stakes"]["terms_knowledge_id"]])
    assert abs(float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='silver'"))-(silver_before-.30))<1e-9
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='scheduled' AND obligation_type='fixture_alternate_metal_exchange'")==1
    rel=db.one("SELECT relationship_type,trust,respect FROM relationships WHERE from_person_id='P7' AND to_person_id='P12'")
    assert rel is not None and rel["relationship_type"]=="market_contact" and float(rel["trust"])>0.55
    assert db.scalar("SELECT COUNT(*) FROM memories WHERE person_id='P12' AND memory_type='trade' AND created_day=?",(eng.day,))>=1
    eng.advance(3,allow_unresolved=True)
    assert db.scalar("SELECT COUNT(*) FROM obligations WHERE status='fulfilled' AND obligation_type='fixture_alternate_metal_exchange'")==1
    event=db.one("SELECT material_deltas_json FROM events WHERE run_id=? AND event_type='alternate_metal_exchange_completed' ORDER BY event_seq DESC LIMIT 1",(rid,))
    assert event is not None and '0.3' in event["material_deltas_json"]
