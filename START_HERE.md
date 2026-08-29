# START HERE

## Authority order

1. Current repository state, canonical SQLite state, tests, accepted evidence, and explicit authority files.
2. `plan.md` for implementation/architecture.
3. `bronze-age-simulation-encyclopedia.md` for the supplied historical/research foundation.
4. Supplemental research only when explicitly recorded in the evidence index.
5. Old chat context is advisory only.

## Project purpose

Build a living anthropological simulation in which historically situated people have persistent households, relationships, beliefs, memories, material constraints, obligations, reputations, and imperfect information. Large outcomes must arise from accumulated lower-level interactions rather than scripted historical destiny.

## Permanent safeguards

- SQLite is the single canonical state. Markdown, JSONL, chronicles, dashboards, and `state/current.json` are derived.
- Culture alters constraints and social pressure, not personality by civilization.
- Evidence uncertainty remains visible. Grade-D claims never silently become defaults.
- Internet research is permitted only in explicit research/calibration work, never while ChatGPT is making an in-world character decision.
- Cognition is pull-based. The engine queues jobs; ChatGPT receives only character-scoped packets and returns typed proposed actions.
- Every decisive factual premise must be present in the packet. Action validation is fail-closed.
- Routine life is deterministic where appropriate. RNG creates circumstances, not arbitrary social destiny.
- Recorded validated cognition decisions are canonical run inputs and must be reusable for replay.
- No vector DB, graph DB, generic agent framework, model API, distributed agents, or microservices without demonstrated need.

## Fresh-session workflow

1. Run project preflight and inspect Git status without destroying work.
2. Read this file, `NEXT_SESSION.md`, `state/current.json` (if present), then `STATUS.md`.
3. Verify the canonical DB/run manifest and run `python -m pytest`.
4. Inspect pending cognition jobs and evidence gaps.
5. Resume from repository/live authority.

## Current decision gate

Prove a Ugaritic micro-community of roughly 6–10 households and 12–20 important named people can live through 30–90 ordinary days with distinct household/material/social positions, imperfect information, meaningful relationships, religion, obligations, and consequential bounded cognition.

**Operating principle: The world is structured. The people are not scripted.**
