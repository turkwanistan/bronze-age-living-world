from __future__ import annotations

import json
from pathlib import Path

from .db import WorldDB, canonical_json


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ingest_evidence(db: WorldDB, root: Path) -> None:
    sources = load_jsonl(root / "research/evidence-index/sources.jsonl")
    claims = load_jsonl(root / "research/evidence-index/claims.jsonl")
    assumptions = load_jsonl(root / "research/evidence-index/assumptions.jsonl")
    mappings = load_jsonl(root / "research/evidence-index/mappings.jsonl")
    with db.transaction() as con:
        for s in sources:
            con.execute(
                "INSERT OR REPLACE INTO research_sources(source_id,kind,title,locator,sha256,metadata_json) VALUES (?,?,?,?,?,?)",
                (s["source_id"], s["kind"], s["title"], s.get("path"), s.get("sha256"), canonical_json(s)),
            )
        for c in claims:
            con.execute(
                "INSERT OR REPLACE INTO historical_claims(claim_id,claim_text,geography,date_range,social_scope,evidence_grade,uncertainty_note) VALUES (?,?,?,?,?,?,?)",
                (c["claim_id"], c["text"], c.get("geography"), c.get("date_range"), c.get("social_scope"), c["evidence_grade"], c.get("limitations")),
            )
        for a in assumptions:
            con.execute(
                "INSERT OR REPLACE INTO model_assumptions(assumption_id,assumption_text,kind,confidence,active,metadata_json) VALUES (?,?,?,?,?,?)",
                (a["assumption_id"], a["text"], a["kind"], a.get("confidence"), 1, canonical_json(a)),
            )
        seq = 0
        for m in mappings:
            for source_id in m.get("source_ids", []) or [None]:
                for claim_id in m.get("claim_ids", []) or [None]:
                    for assumption_id in m.get("assumption_ids", []) or [None]:
                        seq += 1
                        con.execute(
                            "INSERT OR REPLACE INTO evidence_links(evidence_link_id,source_id,claim_id,assumption_id,rule_id,note) VALUES (?,?,?,?,?,?)",
                            (f"EL-{seq:04d}", source_id, claim_id, assumption_id, m.get("rule_id"), canonical_json(m)),
                        )
