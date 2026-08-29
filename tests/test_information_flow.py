import json

from bronze_world.cognition import compile_packet
from bronze_world.engine import WorldEngine


def _pending_for(db, rid, actor, trigger):
    return db.one(
        "SELECT j.job_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.run_id=? AND j.actor_person_id=? AND j.status='pending' AND s.trigger_type=? "
        "ORDER BY j.created_day,j.job_id LIMIT 1",
        (rid, actor, trigger),
    )


def _place_run_at_day(db, rid, day):
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=? WHERE run_id=?", (day, rid))


def test_merchant_inquiries_and_replies_preserve_delivery_containment(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _place_run_at_day(db, rid, 7)
    eng.detect_situations(7)

    merchant_job = _pending_for(db, rid, "P3", "merchant_harbor_information_uncertainty")
    assert merchant_job is not None
    packet = compile_packet(db, merchant_job["job_id"])
    assert "send_message" in packet["allowed_actions"]
    assert {k["proposition_id"] for k in packet["admissible_knowledge"]} >= {"PROP-SHIP-001"}
    assert "PROP-SHIP-002" not in {k["proposition_id"] for k in packet["admissible_knowledge"]}

    inquiry = {
        "decision_id": "DEC-MERCHANT-INQUIRY",
        "actor_id": "P3",
        "selected_intent": "seek independent harbor and market confirmation before acting",
        "proposed_actions": [
            {"type": "send_message", "target_person_id": "P11", "sender_intent": "inquiry", "content": "What report do you currently have about the expected arrival timing?"},
            {"type": "send_message", "target_person_id": "P12", "sender_intent": "inquiry", "content": "What report do you currently have about the expected arrival timing?"},
        ],
        "decisive_knowledge_or_belief_ids": ["K-SHIP-P3"],
        "decision_basis_tags": ["information_provenance", "uncertainty"],
        "declared_uncertainty": "The existing report is unconfirmed and contacts may have different information.",
    }
    result = eng.submit_decision(merchant_job["job_id"], inquiry)
    assert result.ok, result.errors
    outbound = db.all("SELECT * FROM messages WHERE originator_person_id='P3' AND sender_intent='inquiry' ORDER BY recipient_person_id")
    assert [m["recipient_person_id"] for m in outbound] == ["P11", "P12"]
    assert all(m["departure_day"] == 7 and m["arrival_day"] == 8 and m["delivered_day"] is None for m in outbound)
    assert all(m["route_id"] for m in outbound)
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P3' AND proposition_id='PROP-SHIP-002'") == 0

    assert eng.advance(1) == 1
    p11_job = _pending_for(db, rid, "P11", "information_inquiry_received")
    p12_job = _pending_for(db, rid, "P12", "information_inquiry_received")
    assert p11_job is not None and p12_job is not None
    p11_packet = compile_packet(db, p11_job["job_id"])
    p12_packet = compile_packet(db, p12_job["job_id"])
    assert "PROP-SHIP-001" in {k["proposition_id"] for k in p11_packet["admissible_knowledge"]}
    assert "PROP-SHIP-002" not in {k["proposition_id"] for k in p11_packet["admissible_knowledge"]}
    assert "PROP-SHIP-002" in {k["proposition_id"] for k in p12_packet["admissible_knowledge"]}

    bad_report = {
        "decision_id": "DEC-P11-LEAK", "actor_id": "P11", "selected_intent": "report information I do not possess",
        "proposed_actions": [{"type": "send_message", "target_person_id": "P3", "sender_intent": "report", "proposition_id": "PROP-SHIP-002", "content": "I report the market-side no-confirmation report."}],
        "decisive_knowledge_or_belief_ids": [], "decision_basis_tags": [], "declared_uncertainty": "none",
    }
    leak_result = eng.submit_decision(p11_job["job_id"], bad_report)
    assert not leak_result.ok
    assert any("epistemic_leak_proposition:PROP-SHIP-002" in e for e in leak_result.errors)

    p11_reply = {
        "decision_id": "DEC-P11-REPLY", "actor_id": "P11", "selected_intent": "send the report I actually have",
        "proposed_actions": [{"type": "send_message", "target_person_id": "P3", "sender_intent": "report", "proposition_id": "PROP-SHIP-001", "content": "My report is that an expected vessel may be delayed."}],
        "decisive_knowledge_or_belief_ids": ["K-SHIP-P11"], "decision_basis_tags": ["direct_report", "provenance"],
        "declared_uncertainty": "The report does not establish the actual outcome.",
    }
    assert eng.submit_decision(p11_job["job_id"], p11_reply).ok

    p12_reply = {
        "decision_id": "DEC-P12-REPLY", "actor_id": "P12", "selected_intent": "send the independent market-side report",
        "proposed_actions": [{"type": "send_message", "target_person_id": "P3", "sender_intent": "report", "proposition_id": "PROP-SHIP-002", "content": "My contact has no confirmation that the expected arrival timing changed."}],
        "decisive_knowledge_or_belief_ids": ["K-SHIP-P12"], "decision_basis_tags": ["hearsay", "provenance"],
        "declared_uncertainty": "This is a no-confirmation report, not proof of arrival.",
    }
    assert eng.submit_decision(p12_job["job_id"], p12_reply).ok

    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P3' AND proposition_id='PROP-SHIP-002'") == 0
    assert eng.advance(1) == 1
    assert db.scalar("SELECT COUNT(*) FROM knowledge WHERE person_id='P3' AND proposition_id='PROP-SHIP-002'") == 1

    contradiction = _pending_for(db, rid, "P3", "contradictory_shipping_reports")
    assert contradiction is not None
    final_packet = compile_packet(db, contradiction["job_id"])
    props = {k["proposition_id"] for k in final_packet["admissible_knowledge"]}
    assert {"PROP-SHIP-001", "PROP-SHIP-002"} <= props
    assert final_packet["scene"]["stakes"]["epistemic_status"].startswith("reports are incomplete/discordant")


def test_typed_message_requires_engine_route(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    _place_run_at_day(db, rid, 7)
    eng.detect_situations(7)
    job = _pending_for(db, rid, "P3", "merchant_harbor_information_uncertainty")
    with db.transaction() as con:
        con.execute("UPDATE persons SET current_place_id='P-WELL-SHARED' WHERE person_id='P11'")
    envelope = {
        "decision_id": "DEC-NO-ROUTE", "actor_id": "P3", "selected_intent": "send inquiry",
        "proposed_actions": [{"type": "send_message", "target_person_id": "P11", "sender_intent": "inquiry", "content": "What have you heard?"}],
        "decisive_knowledge_or_belief_ids": [], "decision_basis_tags": [], "declared_uncertainty": "route availability",
    }
    result = eng.submit_decision(job["job_id"], envelope)
    assert not result.ok
    assert any("no_accessible_message_route" in e for e in result.errors)
