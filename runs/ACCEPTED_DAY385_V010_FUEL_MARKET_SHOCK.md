# ACCEPTED DAY 385 — v010 FUEL + BOUNDED MARKET SHOCK

Accepted strict checkpoint for `state/ugarit_living_v010.sqlite`.

## Gate

- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.8.0`
- schema: `3`
- day: **385**
- state hash: `e2720f1e974c23901ce746f0ffa2d5afbf7d4ce65e317d51653b899b8634c661`
- events: **5,475**
- cognition: **124 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **66/66**
- exact recorded replay: **124 stored decisions / 0 new cognition / exact hash match**
- negative stocks: **0**
- resource-shortfall scenes: **0**
- delivery-before-arrival violations: **0**
- knowledge-before-delivery violations: **0**
- overdue scheduled obligations: **0**
- global composition-neutral provisioning: **5.08/day**

## v010 accepted behavior

### Fuel becomes causal

The year-one projection showed that H-CRAFT's actual post-v009 bottleneck was charcoal, not metal. `ASM-FIXTURE-029` adds finite `fuel_feedstock` only for v010 and later. P7 prepares fuel on days 376 and 385, each time consuming 0.40 feedstock and creating 0.50 charcoal. The reserve falls from 1.20 -> 0.80 -> 0.40. The first preparation enables the day-378 master work cycle, which consumes 0.15 metal + 0.20 charcoal and produces 0.08 finished metalwork.

The quantities are calibration only; the research-supported claim is that charcoal/fuel is a distinct metalworking dependency.

### First bounded non-catastrophic network shock

The first v009 alternate lot does not become an automatic permanent supplier. Once the workshop is short again, P7 must ask established market contact P12 for **new information**. P12 privately knows the v010 disruption proposition. P7 has no access to it until P12's report departs day 379 and is delivered day 380.

The new fixture terms are worse than the first lot: 0.30 silver for 0.18 usable metal after five days. The same sealed decision also exposes the already-tested lossy recycling fallback (0.20 finished metalwork -> 0.12 raw metal). Strict history chooses the degraded external lot because H-CRAFT has ample silver relative to finished output and the lot still arrives by the next weekly production boundary.

Silver moves immediately on day 380. The 0.18 metal appears only on day 385, then ordinary craft work consumes 0.15 metal + 0.20 charcoal and produces 0.08 finished work. No magical stock or hidden supplier is created.

### Existing systems remain causal

- P7 still makes zero post-day-308 resource requests to P3.
- P3's 16.5-silver reserve remains binding.
- P7<->P12 remains a market relationship; the disruption is treated as external scarcity, not betrayal.
- Arhalbu again reschedules palace labor at the 1.00 cereal-harvest bottleneck, preserving service for day 420.
- Kothar's continuing-care obligation and Bat-Rapiu's non-binding property preference remain active.

## Limitations

- `fuel_feedstock` is an engineering resource abstraction, not a reconstructed Ugaritic woodland/charcoal economy.
- Only one bounded repeat-market disruption is modeled; no frequency or probability is claimed.
- The disrupted lot is known before P7 accepts it; surprise damage after commitment is not yet modeled.
- Recycling is available and regression-tested but strict v010 chooses the external lot.
- No generic herd, weather generator, broad commodity-price model, or collapse simulation is introduced.
