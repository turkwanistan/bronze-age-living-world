# ACCEPTED DAY 421 — v011 FUEL LOGISTICS + MARKET-UNAVAILABLE RECYCLING

Accepted strict checkpoint for `state/ugarit_living_v011.sqlite`.

## Gate

- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.9.0`
- schema: `3`
- day: **421**
- state hash: `0b55f95796bc28a9995b3e63ab35c0c5f951c884fe99ad3ad2ca291eb0ed0102`
- events: **5,998**
- cognition: **137 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **71/71**
- exact recorded replay: **137 stored decisions / 0 new cognition / exact hash match**
- negative stocks: **0**
- resource-shortfall scenes: **0**
- delivery-before-arrival violations: **0**
- knowledge-before-delivery violations: **0**
- overdue scheduled obligations: **0**
- global composition-neutral provisioning: **5.08/day**

## v011 accepted behavior

### Fuel replenishment becomes social and material

H-CRAFT begins v011 with only 0.40 fuel_feedstock, one final preparation batch. On day 386 P7 asks P16/Kothar for a bounded paid haul. P16 is a porter/seasonal worker but the modeled cereal-harvest bottleneck is intensity 1.00 and his continuing household-care obligation remains active, so he declines without creating a relationship conflict.

The engine does not reopen the same request every day. The offer is keyed to agricultural phase. At day 420 the phase changes to dry-summer/storage/vines and intensity falls to 0.68. P7 asks again because the condition that justified the refusal changed. P16 has also fulfilled Bat-Rapiu's day-394 care episode, so he accepts the paid haul.

Payment and material do not move at acceptance. On day 421 the scheduled labor completes: H-CRAFT pays 0.20 silver to H-WIDOW and receives 0.80 external local fuel_feedstock. P7 then converts 0.40 of the delivered feedstock into 0.50 charcoal through the already-established finite fuel-preparation rule. P7<->P16 now has a modest `work_contact` relationship with zero conflicts.

The exact hauler, payment, duration and feedstock quantity are ASM-FIXTURE-031 calibration; no historical wage, woodland yield or route is claimed.

### The alternate metal market can actually be empty

The v010 degraded P12 lot is not followed by another automatic offer. On day 386 P7 asks P12 for current availability. P12 privately knows that the same fixture contact has no additional usable lot. P7 does not learn that fact until P12's report is delivered on day 388.

Once the no-lot state is known, recycling becomes a recurring but costly resilience path. Strict history chooses the lossy 0.20 finished_metalwork -> 0.12 metal remelt on days **388, 402 and 416**. A real minimum 14-day interval prevents bucket-edge recurrence. The recovered material is consumed through ordinary workshop cycles; from v011 onward a tiny numeric tolerance prevents binary float dust from blocking an exact calibrated 0.15 master-cycle threshold.

Finished metalwork therefore falls materially as the workshop survives the market cutoff. This is not free or unlimited supply, and P7 still makes zero post-day-308 resource requests to P3.

### Existing systems remain causal

- P3's 16.5 silver reserve remains binding.
- P16's day-386 outside-work refusal and day-394 care fulfillment are consistent with the same harvest labor pressure.
- P13's postponed palace service completes when the calendar reaches the lower-intensity day-420 phase.
- Bat-Rapiu's property preference remains non-binding; no succession/property transfer occurs.
- The staple provisioning stability gate remains untouched.

## Limitations

- External local fuel_feedstock remains an explicit material fixture rather than a simulated woodland, charcoal-maker household or ecological regeneration model.
- P16 is the first modeled hauler; no general labor market is claimed.
- The current no-lot state does not yet have an endogenous recovery mechanism or new supplier discovery beyond future implementation.
- Recycling uses finished workshop output as the available scrap proxy; there is no generalized object/scrap inventory.
- Tool/mold breakage, weather damage, broader fuel ecology, second-seed/counterfactual behavior and multilingual/scribal trade constraints remain future work.
