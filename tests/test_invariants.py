import pytest
from bronze_world.engine import WorldEngine


def test_routine_advance_never_negative(world):
    db,rid=world
    WorldEngine(db,rid).advance(90, allow_unresolved=True)
    assert db.scalar("SELECT MIN(amount) FROM resource_stocks") >= 0
    assert db.scalar("SELECT current_day FROM runs WHERE run_id=?",(rid,))==90


def test_message_cannot_arrive_before_departure(world):
    db,_=world
    with pytest.raises(Exception):
        with db.transaction() as con:
            con.execute("INSERT INTO messages(message_id,originator_person_id,recipient_person_id,actual_content,language,departure_day,arrival_day,distortion_json,secrecy) VALUES ('bad','P1','P2','x','Ugaritic',5,4,'{}','ordinary')")


def test_message_delivery_creates_recipient_knowledge_only_on_arrival(world):
    db,rid=world; eng=WorldEngine(db,rid)
    mid=eng.send_message("P11","P6","PROP-SHIP-001","The vessel may be delayed.",3)
    eng.advance(2, allow_unresolved=True)
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P6' AND proposition_id='PROP-SHIP-001'")==0
    eng.advance(1, allow_unresolved=True)
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P6' AND proposition_id='PROP-SHIP-001'")==1
    assert db.scalar("SELECT delivered_day FROM messages WHERE message_id=?",(mid,))==3


def test_failed_transfer_is_atomic(world):
    db,rid=world; eng=WorldEngine(db,rid); eng.advance(30)
    job=db.one("SELECT job_id,actor_person_id FROM cognition_jobs WHERE run_id=? AND status='pending' ORDER BY created_day LIMIT 1",(rid,))
    if job is None:
        # Force detection by lowering one household stock, still through a transaction.
        with db.transaction() as con: con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-WIDOW' AND resource_type='grain'")
        eng.detect_situations(); job=db.one("SELECT job_id,actor_person_id FROM cognition_jobs WHERE run_id=? AND status='pending' ORDER BY created_day LIMIT 1",(rid,))
    before=db.scalar("SELECT amount FROM resource_stocks WHERE household_id=(SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL) AND resource_type='grain'",(job["actor_person_id"],))
    env={"decision_id":"DEC-TOO-MUCH","actor_id":job["actor_person_id"],"selected_intent":"give impossible amount","proposed_actions":[{"type":"transfer_resource","target_household_id":"H-MERCH","resource":"grain","amount":999}],"decisive_knowledge_or_belief_ids":[],"decision_basis_tags":[],"declared_uncertainty":"none"}
    result=eng.submit_decision(job["job_id"],env)
    after=db.scalar("SELECT amount FROM resource_stocks WHERE household_id=(SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL) AND resource_type='grain'",(job["actor_person_id"],))
    assert not result.ok
    assert before==after
    assert db.scalar("SELECT COUNT(*) FROM events WHERE decision_id='DEC-TOO-MUCH' AND event_type='resource_transfer'")==0
