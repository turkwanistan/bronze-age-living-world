import json
from bronze_world.cognition import compile_packet
from bronze_world.engine import WorldEngine


def _ensure_resource_job(db,rid):
    eng=WorldEngine(db,rid)
    with db.transaction() as con: con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-WIDOW' AND resource_type='grain'")
    eng.detect_situations()
    return db.one("SELECT job_id,actor_person_id FROM cognition_jobs WHERE run_id=? AND status='pending' ORDER BY created_day,job_id LIMIT 1",(rid,))


def test_packet_is_character_scoped(world):
    db,rid=world; job=_ensure_resource_job(db,rid); packet=compile_packet(db,job["job_id"])
    actor=job["actor_person_id"]
    assert packet["actor"]["person_id"]==actor
    assert all(k["person_id"]==actor for k in packet["admissible_knowledge"])
    if actor not in {"P3","P11"}:
        assert all(k["proposition_id"]!="PROP-SHIP-001" for k in packet["admissible_knowledge"])


def test_validator_rejects_epistemic_leak(world):
    db,rid=world; job=_ensure_resource_job(db,rid); eng=WorldEngine(db,rid)
    env={"decision_id":"DEC-LEAK","actor_id":job["actor_person_id"],"selected_intent":"act on hidden shipping rumor","proposed_actions":[{"type":"refuse_proposal"}],"decisive_knowledge_or_belief_ids":["K-SHIP-P3"],"decision_basis_tags":["shipping_news"],"declared_uncertainty":"low"}
    result=eng.submit_decision(job["job_id"],env)
    if job["actor_person_id"]=="P3":
        assert result.ok
    else:
        assert not result.ok
        assert any(e.startswith("epistemic_leak:") for e in result.errors)


def test_packet_exposes_ritual_affordance_for_ritual_scene(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("INSERT INTO scenes VALUES ('SC-RIT',?,?,?,'religious','minor_illness','{}','{}','{}','[\"I-SHRINE\"]','open')",(rid,1,'P-NORTH-NEIGH'))
        con.execute("INSERT INTO scene_participants VALUES ('SC-RIT','P10','affected_actor')")
    job=eng.enqueue_job('SC-RIT','P10',['perform_ritual','communicate'])
    packet=compile_packet(db,job)
    assert 'perform_ritual' in packet['allowed_actions']
    assert any(i['institution_id']=='I-SHRINE' for i in packet['available_institutions'])


def test_sealed_packet_does_not_recompile_from_future_state(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-WIDOW' AND resource_type='grain'")
    eng.detect_situations()
    job=db.one("SELECT job_id FROM cognition_jobs WHERE run_id=? AND status='pending' ORDER BY created_day,job_id LIMIT 1",(rid,))
    first=compile_packet(db,job['job_id'])
    sealed_amount=first['household']['resources']['grain']['amount']
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=amount+10 WHERE household_id='H-WIDOW' AND resource_type='grain'")
    second=compile_packet(db,job['job_id'])
    assert second==first
    assert second['household']['resources']['grain']['amount']==sealed_amount


def test_normal_time_stops_at_unresolved_cognition(world):
    db,rid=world; eng=WorldEngine(db,rid)
    advanced=eng.advance(90)
    assert advanced < 90
    assert db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='pending'",(rid,)) > 0
    assert eng.advance(1)==0


def test_resource_request_creates_second_person_cognition_job(world):
    db,rid=world; eng=WorldEngine(db,rid)
    # Create a shortfall scene at day 0 without advancing time.
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-DEPEND' AND resource_type='grain'")
    eng.detect_situations(0)
    job=db.one("SELECT job_id FROM cognition_jobs WHERE actor_person_id='P13' AND status='pending' ORDER BY created_day LIMIT 1")
    env={
        "decision_id":"DEC-REQ-TEST","actor_id":"P13","selected_intent":"ask a trusted work neighbor for temporary aid",
        "proposed_actions":[{"type":"request_resource","target_person_id":"P1","resource":"grain","amount":2,"reason":"household stores are low"}],
        "decisive_knowledge_or_belief_ids":["K-LOCAL-P13"],"decision_basis_tags":["household_security","reciprocity"],
        "declared_uncertainty":"The neighbor may refuse."
    }
    result=eng.submit_decision(job['job_id'],env)
    assert result.ok
    responder=db.one("SELECT job_id,actor_person_id,packet_json FROM cognition_jobs WHERE actor_person_id='P1' AND status='pending'")
    assert responder is not None
    packet=json.loads(responder['packet_json'])
    assert packet['scene']['trigger']=='resource_request'
    assert packet['scene']['stakes']['requester_person_id']=='P13'
    assert packet['scene']['stakes']['amount']==2.0


def test_obligation_fulfillment_changes_state_and_memories(world):
    db,rid=world; eng=WorldEngine(db,rid)
    # Move directly to due day diagnostically, then reset to strict same-day resolution.
    eng.advance(21, allow_unresolved=True)
    job=db.one("SELECT job_id FROM cognition_jobs WHERE actor_person_id='P15' AND scene_id IN (SELECT scene_id FROM scenes WHERE trigger_type='obligation_due') ORDER BY created_day LIMIT 1")
    # Diagnostic advance may also have unrelated jobs; the obligation job itself is day 21 and current day is 21.
    env={
        "decision_id":"DEC-FULFILL-TEST","actor_id":"P15","selected_intent":"honor reciprocal aid without endangering household stores",
        "proposed_actions":[{"type":"transfer_resource","target_household_id":"H-FARM","social_target_person_id":"P2","resource":"grain","amount":1,"fulfills_obligation_id":"O-FAVOR-001"}],
        "decisive_knowledge_or_belief_ids":["K-LOCAL-P15"],"decision_basis_tags":["reciprocity","reputation","household_security"],
        "declared_uncertainty":"Exact customary equivalence is not modeled."
    }
    result=eng.submit_decision(job['job_id'],env)
    assert result.ok
    assert db.scalar("SELECT status FROM obligations WHERE obligation_id='O-FAVOR-001'")=='fulfilled'
    assert db.scalar("SELECT COUNT(*) FROM memories WHERE person_id='P2' AND memory_type='resource_exchange'")==1
    assert db.scalar("SELECT COUNT(*) FROM events WHERE decision_id='DEC-FULFILL-TEST' AND event_type='resource_transfer'")==1


def test_due_debt_creates_negotiable_scene_and_extension(world):
    db,rid=world; eng=WorldEngine(db,rid)
    eng.advance(28, allow_unresolved=True)
    job=db.one("SELECT job_id FROM cognition_jobs WHERE scene_id IN (SELECT scene_id FROM scenes WHERE trigger_type='debt_due') AND actor_person_id='P13' ORDER BY created_day LIMIT 1")
    assert job is not None
    env={
        "decision_id":"DEC-DEBT-REQ-TEST","actor_id":"P13","selected_intent":"make partial payment and request time",
        "proposed_actions":[
            {"type":"repay_debt","debt_id":"D-DEPEND-001","amount":1,"creditor_person_id":"P3"},
            {"type":"request_debt_extension","debt_id":"D-DEPEND-001","target_person_id":"P3","new_due_day":42,"reason":"household stores are tight"}
        ],
        "decisive_knowledge_or_belief_ids":["K-LOCAL-P13"],"decision_basis_tags":["debt","household_security"],
        "declared_uncertainty":"fixture debt terms are abstract"
    }
    assert eng.submit_decision(job['job_id'],env).ok
    responder=db.one("SELECT job_id FROM cognition_jobs WHERE actor_person_id='P3' AND scene_id IN (SELECT scene_id FROM scenes WHERE trigger_type='debt_extension_request') AND status='pending'")
    assert responder is not None
    packet=compile_packet(db,responder['job_id'])
    assert any(m['memory_type']=='debt' for m in packet['relevant_memories'])
    accept={
        "decision_id":"DEC-DEBT-ACCEPT-TEST","actor_id":"P3","selected_intent":"accept the extension after partial repayment",
        "proposed_actions":[{"type":"accept_debt_extension","debt_id":"D-DEPEND-001","new_due_day":42}],
        "decisive_knowledge_or_belief_ids":[],"decision_basis_tags":["partial_repayment","credit"],"declared_uncertainty":"none"
    }
    assert eng.submit_decision(responder['job_id'],accept).ok
    assert db.scalar("SELECT due_day FROM debts WHERE debt_id='D-DEPEND-001'")==42
    assert db.scalar("SELECT outstanding FROM debts WHERE debt_id='D-DEPEND-001'")==3.0


def test_packet_includes_scoped_household_routine_expectations(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-WIDOW' AND resource_type='grain'")
    eng.detect_situations(0)
    job=db.one("SELECT job_id FROM cognition_jobs WHERE actor_person_id='P15' AND status='pending' ORDER BY created_day LIMIT 1")
    packet=compile_packet(db,job['job_id'])
    routine=packet['household']['routine_expectations']
    assert routine['daily_grain_need']>0
    assert routine['weekly_grain_receipt']>0
    assert routine['next_weekly_receipt_day']==7
    assert 'fixture' in routine['notice'].lower()


def test_wait_is_valid_for_resource_shortfall(world):
    db,rid=world; eng=WorldEngine(db,rid)
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=1 WHERE household_id='H-WIDOW' AND resource_type='grain'")
    eng.detect_situations(0)
    job=db.one("SELECT job_id FROM cognition_jobs WHERE actor_person_id='P15' AND status='pending' ORDER BY created_day LIMIT 1")
    packet=compile_packet(db,job['job_id'])
    assert 'wait' in packet['allowed_actions']
    env={"decision_id":"DEC-WAIT-TEST","actor_id":"P15","selected_intent":"wait for expected routine receipt","proposed_actions":[{"type":"wait","reason":"expected receipt soon","until_day":7}],"decisive_knowledge_or_belief_ids":[],"decision_basis_tags":["routine_expectation"],"declared_uncertainty":"fixture schedule"}
    assert eng.submit_decision(job['job_id'],env).ok
    assert db.scalar("SELECT COUNT(*) FROM events WHERE decision_id='DEC-WAIT-TEST' AND event_type='decision_to_wait'")==1
