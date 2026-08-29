import json

from bronze_world.cognition import compile_packet
from bronze_world.db import canonical_json
from bronze_world.engine import WorldEngine
from bronze_world.ids import stable_id


def _job_for(db, rid, trigger, actor=None):
    sql = (
        "SELECT j.job_id,j.actor_person_id,s.scene_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.run_id=? AND j.status='pending' AND s.trigger_type=?"
    )
    params = [rid, trigger]
    if actor:
        sql += " AND j.actor_person_id=?"
        params.append(actor)
    sql += " ORDER BY j.created_day,j.rowid LIMIT 1"
    return db.one(sql, tuple(params))


def _set_day(db, rid, day):
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=? WHERE run_id=?", (day, rid))


def _add_trade_history(eng, count=2):
    with eng.db.transaction() as con:
        for n in range(count):
            eng._event(
                con, 49 + 28 * n, "fixture_trade_exchange_completed", actors=["P3"],
                rules=["ASM-FIXTURE-012", "RULE-PORT-TRADE-CYCLE-001"],
                payload={"test_history": True, "trade_goods_amount": 0.5}, discriminator=f"test-trade-{n}",
            )


def _add_apprenticeship_history(eng, cycles=12):
    with eng.db.transaction() as con:
        for n in range(cycles):
            eng._event(
                con, 7 * (n + 1), "occupation_work_cycle", actors=["P8"],
                rules=["ASM-FIXTURE-008", "ASM-FIXTURE-009", "RULE-OCCUPATION-WORKFLOW-001"],
                payload={"roles": ["craft_apprentice", "porter"], "test_history": True},
                discriminator=f"test-apprentice-{n}",
            )
        con.execute(
            "UPDATE resource_stocks SET amount=0.7 WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'"
        )


def _decision(decision_id, actor, intent, actions, knowledge=None):
    return {
        "decision_id": decision_id,
        "actor_id": actor,
        "selected_intent": intent,
        "proposed_actions": actions,
        "decisive_knowledge_or_belief_ids": knowledge or [],
        "decision_basis_tags": ["test"],
        "declared_uncertainty": "Fixture mechanics are not historical quantitative reconstruction.",
    }


def test_household_reserve_negotiation_constrains_later_trade(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _set_day(db, rid, 91)
    _add_trade_history(eng, 2)

    eng.detect_situations(91)
    job = _job_for(db, rid, "household_trade_reserve_priority", "P4")
    assert job is not None
    packet = compile_packet(db, job["job_id"])
    stakes = packet["scene"]["stakes"]
    assert stakes["completed_trade_exchanges"] == 2
    assert stakes["proposed_reserve_floor"] == 17.5
    assert "request_household_reserve_agreement" in packet["allowed_actions"]

    request = _decision(
        "DEC-TEST-RESERVE-REQUEST", "P4", "ask the merchant to protect household reserves",
        [{
            "type": "request_household_reserve_agreement", "target_person_id": "P3", "resource": "silver",
            "reserve_floor": 17.5, "reason": "repeated trade exposure should leave a protected household reserve"
        }],
        ["K-LOCAL-TRADE-001-P4", "K-LOCAL-DISPUTE-001-P4"],
    )
    assert eng.submit_decision(job["job_id"], request).ok

    merchant = _job_for(db, rid, "household_reserve_request", "P3")
    assert merchant is not None
    accept = _decision(
        "DEC-TEST-RESERVE-ACCEPT", "P3", "accept a household reserve floor",
        [{"type": "accept_household_reserve", "resource": "silver", "reserve_floor": 17.5,
          "reason": "preserve household continuity while continuing bounded trade"}],
        ["K-LOCAL-TRADE-001-P3", "K-LOCAL-P3"],
    )
    assert eng.submit_decision(merchant["job_id"], accept).ok
    obligation = db.one(
        "SELECT * FROM obligations WHERE obligation_type='household_reserve_commitment' AND status='active'"
    )
    assert obligation is not None
    provenance = json.loads(obligation["provenance_json"])
    assert provenance["resource"] == "silver" and provenance["reserve_floor"] == 17.5

    # At the floor, even an otherwise valid 0.5 trade commitment must fail closed.
    with db.transaction() as con:
        con.execute("UPDATE resource_stocks SET amount=17.5 WHERE household_id='H-MERCH' AND resource_type='silver'")
        sid = stable_id("SCENE", rid, "test_port_after_reserve")
        stakes = {"max_silver_commitment": 0.5, "transit_days": 7, "exchange_goods_ratio": 1.0, "trade_cycle": 99}
        con.execute(
            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sid, rid, 91, "P-NORTH-NEIGH", "economic", "port_trade_opportunity", canonical_json(stakes), "{}", "{}", canonical_json(["I-MARKET"]), "open"),
        )
        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P3", "decision_actor"))
    trade_job = eng.enqueue_job(sid, "P3", ["commit_trade_exchange", "wait"])
    invalid = _decision(
        "DEC-TEST-RESERVE-BLOCK", "P3", "commit trade despite reserve",
        [{"type": "commit_trade_exchange", "silver_amount": 0.5, "reason": "test reserve enforcement"}],
        ["K-LOCAL-TRADE-001-P3"],
    )
    result = eng.validate_decision(trade_job, invalid)
    assert not result.ok
    assert "action_0:household_reserve_floor_violation" in result.errors


def test_apprenticeship_progression_changes_role_and_household_status(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _set_day(db, rid, 91)
    _add_apprenticeship_history(eng, 12)

    eng.detect_situations(91)
    apprentice = _job_for(db, rid, "apprenticeship_progression_review", "P8")
    assert apprentice is not None
    packet = compile_packet(db, apprentice["job_id"])
    assert packet["scene"]["stakes"]["work_cycles_as_apprentice"] == 12
    assert packet["scene"]["stakes"]["proposed_recognition"] == "recognized_craft_worker"

    request = _decision(
        "DEC-TEST-APPRENTICE-REQUEST", "P8", "ask for recognition after sustained workshop work",
        [{"type": "request_apprenticeship_progression", "target_person_id": "P7",
          "requested_recognition": "recognized_craft_worker", "reason": "sustained supervised work merits greater workshop responsibility"}],
        ["K-LOCAL-DISPUTE-001-P8"],
    )
    assert eng.submit_decision(apprentice["job_id"], request).ok
    master = _job_for(db, rid, "apprenticeship_progression_request", "P7")
    assert master is not None

    grant = _decision(
        "DEC-TEST-APPRENTICE-GRANT", "P7", "recognize the apprentice as a workshop craft worker",
        [{"type": "grant_apprenticeship_progression", "apprentice_person_id": "P8",
          "reason": "the accumulated work history supports greater supervised responsibility"}],
        ["K-LOCAL-DISPUTE-001-P7"],
    )
    assert eng.submit_decision(master["job_id"], grant).ok
    assert db.scalar(
        "SELECT COUNT(*) FROM person_roles pr JOIN roles r USING(role_id) WHERE pr.person_id='P8' AND r.name='craft_apprentice' AND pr.end_day IS NULL"
    ) == 0
    assert db.scalar(
        "SELECT COUNT(*) FROM person_roles pr JOIN roles r USING(role_id) WHERE pr.person_id='P8' AND r.name='recognized_craft_worker' AND pr.end_day IS NULL"
    ) == 1
    assert db.scalar("SELECT legal_status FROM persons WHERE person_id='P8'") == "dependent_craft_worker"
    assert db.scalar(
        "SELECT membership_role FROM household_memberships WHERE person_id='P8' AND until_day IS NULL ORDER BY since_day DESC LIMIT 1"
    ) == "attached_worker"
    assert db.scalar("SELECT relationship_type FROM relationships WHERE from_person_id='P7' AND to_person_id='P8'") == "workshop_mentor"
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='apprenticeship_progressed'", (rid,)) == 1


def test_refusal_creates_strain_and_one_bounded_mediation_review(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _set_day(db, rid, 91)
    _add_apprenticeship_history(eng, 12)
    eng.detect_situations(91)
    apprentice = _job_for(db, rid, "apprenticeship_progression_review", "P8")
    request = _decision(
        "DEC-TEST-MEDIATION-REQUEST", "P8", "ask for workshop progression",
        [{"type": "request_apprenticeship_progression", "target_person_id": "P7",
          "requested_recognition": "recognized_craft_worker", "reason": "sustained work merits review"}],
        ["K-LOCAL-DISPUTE-001-P8"],
    )
    assert eng.submit_decision(apprentice["job_id"], request).ok
    master = _job_for(db, rid, "apprenticeship_progression_request", "P7")
    before_conflicts = int(db.scalar("SELECT conflicts FROM relationships WHERE from_person_id='P8' AND to_person_id='P7'"))
    refuse = _decision(
        "DEC-TEST-MEDIATION-REFUSE", "P7", "refuse immediate progression",
        [{"type": "refuse_proposal", "reason": "I am not yet willing to recognize the progression directly."}],
        ["K-LOCAL-DISPUTE-001-P7"],
    )
    assert eng.submit_decision(master["job_id"], refuse).ok
    assert int(db.scalar("SELECT conflicts FROM relationships WHERE from_person_id='P8' AND to_person_id='P7'")) == before_conflicts + 1
    follow = _job_for(db, rid, "proposal_refusal_followup", "P8")
    assert follow is not None

    mediate = _decision(
        "DEC-TEST-MEDIATION-SEEK", "P8", "seek one informal review rather than abandon or escalate the dispute",
        [{"type": "seek_mediation", "institution_id": "I-MEDIATION",
          "issue": "workshop progression after sustained apprenticeship work"}],
        ["K-LOCAL-DISPUTE-001-P8"],
    )
    assert eng.submit_decision(follow["job_id"], mediate).ok
    review = _job_for(db, rid, "informal_mediation_review", "P7")
    assert review is not None
    review_packet = compile_packet(db, review["job_id"])
    assert review_packet["scene"]["stakes"]["source_trigger"] == "apprenticeship_progression_request"
    assert "grant_apprenticeship_progression" in review_packet["allowed_actions"]

    grant = _decision(
        "DEC-TEST-MEDIATION-GRANT", "P7", "grant progression after bounded informal review",
        [{"type": "grant_apprenticeship_progression", "apprentice_person_id": "P8",
          "reason": "the mediated review supports recognizing accumulated work without claiming a universal procedure"}],
        ["K-LOCAL-DISPUTE-001-P7"],
    )
    assert eng.submit_decision(review["job_id"], grant).ok
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='informal_mediation_review_opened'", (rid,)) == 1
    assert db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='apprenticeship_progressed'", (rid,)) == 1


def test_palace_reschedule_finds_next_actual_lower_intensity_phase(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    # Simulation day 140 maps to day-of-year 260, inside the modeled 0.88
    # grape/olive/field-preparation phase. The next <0.85 phase is after the
    # calendar wraps to wet winter, not merely seven days later.
    assert eng._seasonal_context(140)["agricultural_intensity"] == 0.88
    assert eng._next_lower_agricultural_intensity_day(140) == 240
    assert eng._seasonal_context(240)["agricultural_intensity"] < 0.85
