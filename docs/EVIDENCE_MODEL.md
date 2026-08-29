# Evidence Model v1

## Six layers

1. `research_source`
2. `historical_claim`
3. `model_assumption`
4. `model_rule_or_parameter`
5. `scenario_value`
6. `runtime_sample`

A source supports a claim. A claim may permit multiple assumptions. A scenario chooses/weights assumptions. A run samples concrete runtime values. No layer may silently collapse into another.

## Stable identifiers

- `SRC-*` source
- `CLM-*` historical claim
- `ASM-*` model assumption
- `RULE-*` rule/parameter
- `SIT-*` behavioral situation

## Required fields for historically specific parameters

- geography
- date range
- social scope
- evidence grade A–D
- source IDs
- competing models
- confidence/limitations
- review date

## Fixture assumptions

The first executable world needs numbers before every number is historically calibrated. Such values use `ASM-FIXTURE-*`, are described as abstract units, and are prohibited from supporting historical conclusions. This keeps engineering progress separate from false precision.

## Runtime provenance

Every consequential event should preserve, when applicable:

- run/time/scene/decision;
- actors;
- causing event IDs;
- knowledge/belief IDs;
- model assumption/rule IDs;
- material, relationship, and institutional deltas.

## Derived views

`state/current.json`, chronicles, JSONL exports, reports, and observer pages are generated from SQLite and must carry an explicit derived-state marker. They are never an alternate canonical state.
