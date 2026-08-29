from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_semantic_seed_rebind_matches_dynamic_knowledge_by_exact_canonical_text():
    mod = _load("semantic_seed_validation", "semantic_seed_validation.py")
    source_env = {"decisive_knowledge_or_belief_ids": ["K-SOURCE-DYNAMIC"]}
    source_packet = {
        "admissible_knowledge": [
            {
                "knowledge_id": "K-SOURCE-DYNAMIC",
                "proposition_id": "PROP-SOURCE-DYNAMIC",
                "canonical_text": "The same introduced-contact fact is known here.",
            }
        ]
    }
    dest_packet = {
        "admissible_knowledge": [
            {
                "knowledge_id": "K-DEST-DYNAMIC",
                "proposition_id": "PROP-DEST-DYNAMIC",
                "canonical_text": "The same introduced-contact fact is known here.",
            }
        ]
    }
    rebound, missing = mod._rebind_knowledge(source_env, source_packet, dest_packet)
    assert missing == []
    assert rebound == ["K-DEST-DYNAMIC"]


def test_semantic_seed_rebase_changes_only_matching_stake_values():
    mod = _load("semantic_seed_validation_rebase", "semantic_seed_validation.py")
    source_stakes = {
        "obligation_id": "O-SOURCE",
        "nested": {"message_id": "MSG-SOURCE"},
        "stable_person_id": "P11",
    }
    dest_stakes = {
        "obligation_id": "O-DEST",
        "nested": {"message_id": "MSG-DEST"},
        "stable_person_id": "P11",
    }
    action = {
        "obligation_id": "O-SOURCE",
        "message_id": "MSG-SOURCE",
        "target_person_id": "P11",
        "literal": "unchanged",
    }
    got = mod._rebase_obj(action, source_stakes, dest_stakes)
    assert got["obligation_id"] == "O-DEST"
    assert got["message_id"] == "MSG-DEST"
    assert got["target_person_id"] == "P11"
    assert got["literal"] == "unchanged"
