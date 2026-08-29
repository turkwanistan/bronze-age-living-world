from pathlib import Path
from bronze_world.replay import deterministic_fixture_hash

ROOT=Path(__file__).resolve().parents[1]

def test_seeded_fixture_exact_replay():
    assert deterministic_fixture_hash(ROOT,1701,45)==deterministic_fixture_hash(ROOT,1701,45)


def test_seed_changes_runtime_history_hash():
    assert deterministic_fixture_hash(ROOT,1701,90)!=deterministic_fixture_hash(ROOT,1702,90)


def test_recorded_decisions_replay_without_new_cognition(tmp_path):
    from bronze_world.db import WorldDB
    from bronze_world.engine import WorldEngine
    from bronze_world.fixture import init_fixture
    from bronze_world.replay import replay_recorded_decisions

    source = tmp_path / "source.sqlite"
    rebuilt = tmp_path / "rebuilt.sqlite"
    with WorldDB(source) as db:
        run_id = init_fixture(db, ROOT, 1701)
        engine = WorldEngine(db, run_id)
        assert engine.advance(7) == 7
        job = db.one(
            "SELECT job_id FROM cognition_jobs WHERE run_id=? AND actor_person_id='P3' AND status='pending' "
            "AND scene_id IN (SELECT scene_id FROM scenes WHERE trigger_type='merchant_harbor_information_uncertainty')",
            (run_id,),
        )[0]
        envelope = {
            "decision_id": "DEC-REPLAY-MERCHANT-WAIT",
            "actor_id": "P3",
            "selected_intent": "wait rather than act on an unconfirmed report",
            "decision_basis_tags": ["information_uncertainty"],
            "decisive_knowledge_or_belief_ids": ["K-SHIP-P3"],
            "declared_uncertainty": "The report is stale and unconfirmed.",
            "proposed_actions": [{"type": "wait", "reason": "do not act on an unconfirmed report", "until_day": 8}],
        }
        result = engine.submit_decision(job, envelope)
        assert result.ok, result.errors
        source_hash = db.state_hash(run_id)

    result = replay_recorded_decisions(ROOT, source, rebuilt)
    assert result["new_cognition_calls"] == 0
    assert result["recorded_decisions_applied"] == 1
    assert result["exact_match"] is True
    assert result["source_hash"] == source_hash
    assert result["rebuilt_hash"] == source_hash


def test_recorded_replay_preserves_same_day_source_decision_order(tmp_path):
    """Replay must use source application order, not destination job creation order."""
    import json
    from bronze_world.db import WorldDB
    from bronze_world.engine import WorldEngine
    from bronze_world.fixture import init_fixture
    from bronze_world.replay import replay_recorded_decisions

    source = tmp_path / "source_same_day.sqlite"
    rebuilt = tmp_path / "rebuilt_same_day.sqlite"
    with WorldDB(source) as db:
        run_id = init_fixture(db, ROOT, 1701)
        engine = WorldEngine(db, run_id)
        assert engine.advance(7) == 7
        merchant_job = db.scalar(
            "SELECT j.job_id FROM cognition_jobs j JOIN scenes s USING(scene_id) "
            "WHERE j.run_id=? AND j.actor_person_id='P3' AND j.status='pending' "
            "AND s.trigger_type='merchant_harbor_information_uncertainty'",
            (run_id,),
        )
        inquiry = {
            "decision_id": "DEC-ORDER-INQUIRY",
            "actor_id": "P3",
            "selected_intent": "seek independent confirmation",
            "proposed_actions": [
                {"type": "send_message", "target_person_id": "P11", "sender_intent": "inquiry", "content": "What report do you have?"},
                {"type": "send_message", "target_person_id": "P12", "sender_intent": "inquiry", "content": "What report do you have?"},
            ],
            "decisive_knowledge_or_belief_ids": ["K-SHIP-P3"],
            "decision_basis_tags": ["information_provenance"],
            "declared_uncertainty": "Reports may differ.",
        }
        assert engine.submit_decision(merchant_job, inquiry).ok
        assert engine.advance(1) == 1

        jobs = {
            r["actor_person_id"]: r["job_id"]
            for r in db.all(
                "SELECT actor_person_id,job_id FROM cognition_jobs WHERE status='pending' AND created_day=8"
            )
        }
        # Deliberately apply P12 before P11 even if cognition-job creation order differs.
        p12 = {
            "decision_id": "DEC-ORDER-P12",
            "actor_id": "P12",
            "selected_intent": "report what I know",
            "proposed_actions": [{"type": "send_message", "target_person_id": "P3", "sender_intent": "report", "proposition_id": "PROP-SHIP-002", "content": "No confirmation of changed timing."}],
            "decisive_knowledge_or_belief_ids": ["K-SHIP-P12"],
            "decision_basis_tags": ["provenance"],
            "declared_uncertainty": "This is hearsay, not proof.",
        }
        p11 = {
            "decision_id": "DEC-ORDER-P11",
            "actor_id": "P11",
            "selected_intent": "report what I know",
            "proposed_actions": [{"type": "send_message", "target_person_id": "P3", "sender_intent": "report", "proposition_id": "PROP-SHIP-001", "content": "An expected vessel may be delayed."}],
            "decisive_knowledge_or_belief_ids": ["K-SHIP-P11"],
            "decision_basis_tags": ["provenance"],
            "declared_uncertainty": "The report does not establish the outcome.",
        }
        assert engine.submit_decision(jobs["P12"], p12).ok
        assert engine.submit_decision(jobs["P11"], p11).ok
        source_order = [
            r[0] for r in db.all(
                "SELECT actor_person_id FROM decisions WHERE applied_day=8 ORDER BY rowid"
            )
        ]
        assert source_order == ["P12", "P11"]
        source_hash = db.state_hash(run_id)

    result = replay_recorded_decisions(ROOT, source, rebuilt)
    assert result["exact_match"] is True
    assert result["rebuilt_hash"] == source_hash
    with WorldDB(rebuilt) as db:
        rebuilt_order = [
            r[0] for r in db.all(
                "SELECT actor_person_id FROM decisions WHERE applied_day=8 ORDER BY rowid"
            )
        ]
    assert rebuilt_order == ["P12", "P11"]
