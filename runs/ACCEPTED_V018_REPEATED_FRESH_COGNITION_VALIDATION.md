# ACCEPTED V018 — Repeated Same-Packet Fresh Cognition Validation

v018 is a **validation-only checkpoint**. It does not modify canonical simulation state, scenario mechanics, historical claims, or accepted seed-1701 decisions.

## Canonical authority preserved

Canonical runtime remains accepted v015:

- DB `state/ugarit_living_v015.sqlite`
- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- day `462`
- 6,608 events
- 157 accepted / 0 rejected / 0 pending / 0 open
- state hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`

Prior v016 second-seed/counterfactual and v017 fresh paired validation remain accepted evidence.

## Method

`scripts/repeated_fresh_cognition_validation.py` uses the accepted v017 pair builder to recreate six selected sealed packets. For each packet it creates three independent disposable branch copies and submits three separately authored fresh cognition envelopes from `runs/VALIDATION_V018_REPEATED_FRESH_DECISIONS.json`.

Every attempt:

- uses the same sealed packet hash as the other attempts for that packet;
- is submitted through the ordinary engine validator;
- runs on its own disposable SQLite branch;
- never enters canonical history.

Frozen result: `runs/VALIDATION_V018_REPEATED_FRESH_RESULTS.json`.

## Result

18/18 fresh decisions validate with:

- zero rejected cognition jobs;
- zero negative resource stocks;
- byte-identical packet hash within each three-attempt packet group.

Action-family results:

- **P10 adequate ritual stock:** `perform_ritual` 3/3;
- **P10 depleted ritual stock:** `perform_ritual` 3/3;
- **P7 buffered finished stock:** `recycle_finished_metalwork` 3/3;
- **P7 near-exhausted finished stock:** `wait` 3/3;
- **P3 single unconfirmed shipping report:** `send_message` 3/3;
- **P3 discordant delivered reports:** `wait` 2/3 and `send_message` 1/3.

The P10 material amounts vary within the same packet, but the controlled resource constraint dominates the variation: adequate-stock attempts spend 0.10–0.20 fixture ritual goods, while depleted-stock attempts spend 0.00–0.05. The P7 material control completely separates the action family across all six attempts.

The only action-family variation is the genuinely ambiguous P3 discordant-report packet. Two attempts wait; one asks both contacts to clarify report provenance. All three preserve household credit and explicitly refuse to infer a canonical shipment outcome from contradictory evidence.

## Interpretation

The useful result is **stable causal principles without requiring robotic identical wording or action in an underdetermined case**.

The experiment supports that, for this selected subset:

- material scarcity changes decision intensity coherently;
- severe finished-stock depletion dominates within-packet reasoning noise;
- one uncertain report reliably produces information seeking;
- contradictory reports remain epistemically conservative even when the exact conservative action varies.

This is not a historical frequency study. Three attempts per packet are too few for statistical claims even about the model, and no observed frequency is interpretable as a Bronze Age human probability.

## Reproducibility

`tests/test_v018_repeated_fresh_cognition.py` rebuilds all six packet groups and all 18 disposable attempts from accepted DB state and checks the frozen stability shape. No v018 validation SQLite database is committed.

Acceptance still requires the full repository test suite plus exact canonical v015 replay (157 recorded decisions, 0 new cognition, exact hash).

## Next

Broaden the repeated-fresh evaluation to a small set of **social/relationship-heavy** packets where multiple defensible actions exist, then use any instability to identify missing packet state or validator constraints. High-value candidates are care negotiation, property negotiation, work requests/refusals, and relationship repair after refusal. Do not add new simulation mechanics merely to create test variety.
