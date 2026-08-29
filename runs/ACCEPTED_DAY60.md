# Accepted strict Ugarit gate — day 60

This checkpoint is the first accepted 30–90 ordinary-day Ugaritic living-world gate after replacing the threshold-only resource detector and adding typed delayed character messaging.

## Canonical run

- DB: `state/ugarit_living_v002.sqlite` (host-local canonical SQLite; intentionally ignored by Git)
- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- accepted day: **60**
- state hash: `2b59046401f398c24604eee4242e12865690a64749811b6c56d31c5c3eb0f504`
- events: **577**
- cognition jobs: **8 accepted / 0 rejected / 0 pending**
- open scenes: **0**

## Acceptance evidence

- full test suite: **27/27 passing**;
- recorded-decision replay to day 60: **exact state-hash match**;
- replayed accepted decisions: **8**;
- new cognition calls during replay: **0**;
- `household_resource_shortfall` scenes in accepted run: **0**;
- message-derived knowledge before delivery: **0 violations**;
- undelivered messages with recipient knowledge: **0**.

Situation triggers exercised:

- merchant/harbor information uncertainty;
- two delivered information inquiries;
- contradictory/incomplete shipping reports;
- reciprocal-aid obligation due;
- debt due and repayment;
- two minor-illness situations.

The shipping reports are explicit simulation circumstances under `ASM-FIXTURE-005`; they are not assertions about a historically specific vessel, cargo, route, or outcome. Resource quantities remain abstract fixture units and are not historical rates.

## Information-containment evidence

On day 7 Yabninu had only his own stale, unconfirmed report. He sent bounded inquiries to Abdi-Rashap and Dagan-beli. Each recipient's sealed packet exposed only that recipient's own knowledge. Replies traveled with engine-selected route delays; Yabninu acquired the reported propositions only on actual day-9 delivery. The resulting scene represented incomplete/discordant reports while leaving the canonical shipment outcome unspecified.

## Resource-detector evidence

`RULE-RESOURCE-RUNWAY-001` projects one configured receipt cycle using current stock, deterministic daily need, scheduled receipt timing, and receipt amount. Regression tests prove both directions: low stock that safely reaches the next receipt does not trigger cognition; a projected inability to meet full daily need does. At day 60 the dependent household holds 2.6 abstract grain units and still does not trigger because it can meet full daily need through the scheduled day-63 receipt.

## Accepted decision envelopes

The eight bounded decision envelopes are stored beside this manifest in `runs/decision_day*.json`. They remain subordinate to canonical SQLite history but provide inspectable human-readable evidence of the cognition choices used in this accepted run.
