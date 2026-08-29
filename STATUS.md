# STATUS

**Checkpoint:** accepted strict Ugarit v011 fuel-logistics + market-unavailable recycling gate at day 421.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v011.sqlite`; v002-v010 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.9.0`, schema `3`
- accepted day **421**
- state hash `0b55f95796bc28a9995b3e63ab35c0c5f951c884fe99ad3ad2ca291eb0ed0102`
- **5,998 events**
- **137 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **71/71 tests**
- exact replay: **137 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls, delivery-before-arrival, knowledge-before-delivery, or overdue scheduled-obligation violations
- neutral provisioning remains globally conserved at **5.08/day**

Acceptance manifest: `runs/ACCEPTED_DAY421_V011_FUEL_LOGISTICS_RECYCLING.md`.

## v011 result

Workshop fuel replenishment is no longer automatic. With only one feedstock batch left, P7 asks P16/Kothar for a paid fuel haul on day 386. Kothar declines during the 1.00 harvest bottleneck without relationship conflict. The offer does not recur daily; it returns only when the agricultural phase changes. On day 420 intensity falls to 0.68, P7 asks again, and Kothar accepts after also having fulfilled his household care duty on day 394. The scheduled day-421 completion moves 0.20 silver H-CRAFT→H-WIDOW and 0.80 fuel_feedstock into H-CRAFT. P7 then prepares 0.40 of that feedstock into 0.50 charcoal.

The alternate metal network can also be truly unavailable. P7 asks P12 for a new update; P12's private no-lot state reaches P7 only by delayed message on day 388. Strict history then chooses lossy recycling on days 388, 402 and 416. Each use consumes 0.20 finished metalwork to recover 0.12 raw metal, with a true minimum 14-day interval. Recovered metal is consumed by ordinary workshop work; a v011-only numeric tolerance prevents binary floating-point dust from blocking exact calibrated material thresholds while older replay remains unchanged.

P7 still makes zero post-day-308 resource requests to P3. P3's 16.5 silver reserve remains binding. Arhalbu's postponed palace service completes on the lower-intensity day-420 boundary. Care/property and neutral staple provisioning remain intact.

## Current limitations

Fuel feedstock still enters from an explicit external-local fixture rather than a simulated woodland/ecology or charcoal-maker household. P16 is the first modeled hauler, not a generalized labor market. The no-lot market state does not yet recover endogenously. Recycling uses finished output as the scrap proxy rather than a generalized object inventory. Tool/mold damage, local weather effects, shared/renegotiated care, second-seed/counterfactual analysis and language/scribal trade constraints remain next work.

**The world is structured. The people are not scripted.**
