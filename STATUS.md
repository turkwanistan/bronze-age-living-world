# STATUS

**Checkpoint:** accepted strict Ugarit v013 local-weather/storage resilience + recycling-restraint gate at day 458.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v013.sqlite`; v002-v012 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.11.0`, schema `3`
- accepted day **458**
- state hash `8254bd35f77fa492dc28c9d3b66cde982c0da08f5310f20a062ae6b14160906b`
- **6,516 events**
- **149 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **77/77 tests**
- exact replay: **149 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls, overdue scheduled obligations, delivery-before-arrival or knowledge-before-delivery violations

Acceptance manifest: `runs/ACCEPTED_DAY458_V013_WEATHER_STORAGE.md`.

## v013 result

### Bounded local weather/storage shock

On day 444 one localized dry-summer moisture/rain exposure threatens only exposed `seasonal_produce` in H-FARM and H-DEPEND. It does **not** touch neutral staple grain or already-protected `stored_seasonal_goods`.

Both household seniors independently choose one modeled labor day of protection at agricultural intensity 0.68. Under explicit fixture calibration this reduces the extra-loss fraction from 0.30 to 0.05:

- H-FARM exposed produce ~0.2313; protected loss ~0.0116 instead of ~0.0694 unprotected.
- H-DEPEND exposed produce ~0.1223; protected loss ~0.0061 instead of ~0.0367 unprotected.

The weather episode occurs exactly once per affected household. The larger unprotected path is regression-tested but was not forced into strict history.

### Recycling restraint becomes decision-aware

At day 444 H-CRAFT has only ~0.25 finished metalwork and ~0.01 raw metal. P7 decides **not** to destroy 0.20 finished output for another 0.12 raw-metal recovery because that would leave almost no finished stock and still would not support a full master cycle.

That explicit wait now starts the same true fourteen-day reconsideration interval as a recycle. The unchanged choice does not reappear on day 448; it returns on day 458. With the material and market facts still unchanged, P7 waits again. This prevents repetitive prompts from overriding remembered economic restraint.

### Existing systems remain causal

Kothar returns to fulfilling the continuing-care obligation on day 454 after the prior illness-based deferment. The weather shock does not alter neutral provisioning, stored surplus, marriage/property state, market-message containment, or prior P7→P3 scarcity boundaries.

## Current limitations / next priorities

- The weather episode is one bounded fixture, not a stochastic climate model or historical Ugaritic rain event.
- Protection is represented as one household labor day rather than a reconstructed storage technology inventory.
- Bat-Rapiu's property preference remains non-binding; genuine shared-care/property-use disagreement should precede succession modeling.
- A second independent life-course transition remains needed.
- Second-seed / paired-counterfactual validation should begin before treating behavior frequency as meaningful.
- P12's no-lot market state should recover only through new information, never automatically.

**The world is structured. The people are not scripted.**
