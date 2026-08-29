# ACCEPTED DAY 458 — v013 LOCAL WEATHER/STORAGE RESILIENCE

Accepted strict checkpoint for `state/ugarit_living_v013.sqlite`.

## Gate

- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.11.0`
- schema: `3`
- day: **458**
- state hash: `8254bd35f77fa492dc28c9d3b66cde982c0da08f5310f20a062ae6b14160906b`
- events: **6,516**
- cognition: **149 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **77/77**
- exact replay: **149 stored decisions / 0 new cognition / exact hash**
- negative stocks / false shortfalls / overdue scheduled obligations: **0 / 0 / 0**
- delivery-before-arrival / knowledge-before-delivery violations: **0 / 0**

## Accepted behavior

### Localized weather/storage exposure

`ASM-FIXTURE-034` adds one bounded dry-summer moisture/rain exposure on day 444 for the two agricultural households that currently hold exposed `seasonal_produce`.

The event is intentionally narrow: neutral staple grain and already-preserved `stored_seasonal_goods` are excluded. Each household senior independently chooses between one modeled protection-labor day or accepting a larger extra loss.

Strict history:

- P1/Ilimilku protects H-FARM's ~0.2313 exposed produce; extra fixture loss is ~0.0116 (5%).
- P13/Arhalbu protects H-DEPEND's ~0.1223 exposed produce; extra fixture loss is ~0.0061 (5%).
- The regression-only unprotected path applies a 30% extra loss to exposed produce and still leaves staple grain/stored goods untouched.
- Exactly two exposure scenes exist and the weather episode does not recur later in the checkpoint.

The local anomaly, households, date, labor cost, loss fractions and protective effectiveness are engineering calibration, not a historical Ugaritic weather event or spoilage estimate.

### Reconsideration respects an explicit wait

At day 444 P7 has ~0.25 finished metalwork and ~0.01 raw metal under the existing no-lot market state. He declines another 0.20→0.12 remelt because it would consume almost all remaining finished output while still failing to restore a full master cycle.

From the v013 boundary onward, an explicit wait on `market_unavailable_recycling_choice` starts the same fourteen-day reconsideration window as actual recycling. The same prompt therefore does not reopen on day 448 merely because a calendar bucket changed. It returns exactly on day 458; the state remains materially unchanged, so P7 waits again.

This is a persistence correction, not a new historical claim. Earlier accepted histories retain exact replay semantics.

### Ordinary life remains independent

- P16/Kothar fulfills the active continuing-care obligation again on day 454 after the earlier illness-based deferment.
- Existing provisioning, property preference, relationships, market-message containment and storage routines remain intact.
- No negative stocks, false shortfalls, overdue obligations, delivery timing violations or knowledge timing violations occur.

## Evidence / rules

- `CLM-GEN-019`
- `ASM-FIXTURE-034`
- `MAP-040` → `RULE-LOCAL-STORAGE-WEATHER-001`
- `MAP-041` → `RULE-RECYCLING-RECONSIDERATION-001`

## Limitations

- One bounded local weather event, not a stochastic climate/weather engine.
- One abstract labor-day protection response, not reconstructed storage architecture or labor productivity.
- No crop-yield shock, famine, collapse, or neutral-grain damage.
- Shared-care/property conflict, second life-course transition, second-seed validation and language/scribal constraints remain future work.
