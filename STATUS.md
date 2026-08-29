# STATUS

**Checkpoint:** accepted strict Ugarit v010 fuel + bounded market-shock gate at day 385.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v010.sqlite`; v002-v009 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.8.0`, schema `3`
- accepted day **385**
- hash `e2720f1e974c23901ce746f0ffa2d5afbf7d4ce65e317d51653b899b8634c661`
- **5,475 events**
- **124 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **66/66 tests**
- exact replay: **124 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls, delivery-before-arrival, knowledge-before-delivery, or overdue scheduled-obligation violations
- neutral provisioning remains globally conserved at **5.08/day**

Acceptance manifest: `runs/ACCEPTED_DAY385_V010_FUEL_MARKET_SHOCK.md`.

## v010 result

The post-v009 projection exposed charcoal as the true workshop bottleneck. v010 therefore makes fuel preparation material instead of decorative. H-CRAFT receives a finite fixture `fuel_feedstock` reserve; P7 converts 0.40 feedstock -> 0.50 charcoal on days 376 and 385. Feedstock is now 0.40. Day-378 and day-385 ordinary production prove the prepared fuel is actually consumed.

The first repeat alternate-metal opportunity also requires new information. P7 asks established market contact P12; P12 privately knows a bounded harbor/weather handling disruption and reports it only after inquiry. P7 learns the changed terms on day 380, never before delivery. Terms degrade from the first lot's 0.30 silver / 0.30 metal / 3 days to **0.30 silver / 0.18 usable metal / 5 days**. Recycling remains available in the same packet. P7 accepts the degraded lot because preserving finished output is still attractive at current stocks. Silver leaves day 380; 0.18 metal arrives day 385 and is consumed through normal production.

P7 still makes zero post-refusal resource requests to P3. Arhalbu reschedules a new palace-labor demand from the day-385 1.00 harvest bottleneck to day 420.

## Current limitations

Fuel-feedstock quantity/yield and shock terms are explicit fixture calibration, not historical rates. Only one repeat-market disruption is modeled. Surprise damage after commitment, repeated availability updates, recycling chosen in strict history, broader tool/livestock/weather systems, second-seed/counterfactual frequency analysis, and language/scribal transaction constraints remain future work.

**The world is structured. The people are not scripted.**
