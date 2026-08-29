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
