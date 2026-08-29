# ACCEPTED DAY 462 — v015 ADULT HARBOR LIFE-COURSE SPECIALIZATION

## Gate

- Canonical DB: `state/ugarit_living_v015.sqlite`
- Run: `RUN-3dda7920595c1748`
- Seed: `1701`
- Scenario: `0.13.0`
- Schema: `3`
- Day: **462**
- State hash: `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`
- Events: **6,608**
- Cognition: **157 accepted / 0 rejected / 0 pending**
- Open scenes: **0**
- Tests: **83/83 PASS**
- Exact replay: **157 recorded decisions applied / 0 new cognition / exact hash match**

## Accepted mechanism

v015 adds the second independent state-based life-course transition.

Abdi-Rashap (P11) reaches the fixture eligibility boundary with 65 recurring work cycles and two actual provenance-preserving information/report episodes. He requests a household division-of-labor change from routine porter+sailor work toward `harbor_coordinator`+sailor. Dagan-beli (P12) independently reviews and accepts.

Canonical result:

- `porter`: active day 0 → day 460;
- `harbor_coordinator`: active from day 460;
- `sailor`: remains active from day 0;
- `legal_status`: remains `free_laborer`;
- H-HARBOR membership: remains senior from day 0;
- day-462 occupation work uses coordinator + sailor activities and no longer routine porter activity.

This is occupational specialization only. It does not assert a historical Ugaritic harbor title, office, promotion threshold, legal-status change, patronage appointment, or household move.

## Independent-agency regression

`tests/test_v015_harbor_life_course.py` proves P12 can refuse P11's request. Refusal leaves P11's porter+sailor roles, legal status and household membership unchanged.

## Coexisting older constraints

- Talmiyanu's unrelated day-460 minor illness is resolved conservatively without creating illness progression.
- On day 462 Yabninu remains exactly at the H-MERCH 16.5-silver reserve floor and waits rather than commit another discretionary trade exchange.
- No negative resource stock, false resource shortfall, overdue scheduled obligation, rejected cognition or open scene exists at acceptance.

## Evidence boundary

- `CLM-GEN-021`: constrained adult occupational specialization/mobility is supported broadly.
- `ASM-FIXTURE-036`: the 60-cycle threshold, P11/P12 pairing, `harbor_coordinator` title and household-review procedure are engineering fixtures.
- `MAP-043` / `RULE-ADULT-HARBOR-PROGRESSION-001` map the mechanism to code and regressions.

## Next validation milestone

Run a second deterministic seed and paired mechanism counterfactuals. Compare invariants and causal mechanisms, not exact stochastic event identity. Two seeds remain insufficient for historical frequency claims.
