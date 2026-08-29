# STATUS

**Checkpoint:** accepted v018 repeated same-packet fresh-cognition validation over the unchanged canonical v015 day-462 runtime.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, canonical SQLite and accepted validation manifests govern implementation beneath those authorities.

## Canonical strict runtime

v016-v018 are validation-only. Canonical simulation remains accepted v015:

- DB `state/ugarit_living_v015.sqlite`
- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- day **462**
- **6,608 events**
- **157 accepted / 0 rejected / 0 pending / 0 open**
- hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`

Canonical manifest: `runs/ACCEPTED_DAY462_V015_HARBOR_LIFE_COURSE.md`.
Validation manifests: v016 second-seed/counterfactual, v017 fresh paired cognition, and v018 repeated same-packet cognition.

## v018 repeated-fresh result

Six v017 sealed packets were each given three independently authored fresh cognition attempts, for **18 total decisions**. Each attempt runs on its own disposable branch and passes the ordinary engine validator.

- P10 adequate ritual stock: `perform_ritual` 3/3, material costs 0.10–0.20.
- P10 depleted ritual stock: `perform_ritual` 3/3, material costs 0.00–0.05.
- P7 buffered finished output: `recycle_finished_metalwork` 3/3.
- P7 near-exhausted finished output: `wait` 3/3.
- P3 one unconfirmed shipping report: `send_message` 3/3.
- P3 discordant delivered reports: `wait` 2/3, clarification inquiries 1/3.

All 18 decisions validate; there are 0 rejected branch jobs and 0 negative branch resource stocks. Packet hashes are identical within each three-attempt group.

The key interpretation is that controlled resource/epistemic differences remain stronger than within-packet variation. The one varying action family is an underdetermined shipping-information case, and every attempt remains epistemically conservative rather than inventing an outcome.

Frozen evidence:

- `runs/VALIDATION_V018_REPEATED_FRESH_DECISIONS.json`
- `runs/VALIDATION_V018_REPEATED_FRESH_RESULTS.json`
- `scripts/repeated_fresh_cognition_validation.py`
- `tests/test_v018_repeated_fresh_cognition.py`

## Next priority

Finish the v018 acceptance gate and commit. Then broaden repeated-fresh testing to social/relationship-heavy packets where several actions may be legitimate: care negotiation, household property negotiation, work requests/refusals, and relationship repair after a material refusal. Use instability to find missing causal state before adding new world mechanics.

Choice frequencies remain model diagnostics only and are never historical probabilities.

**The world is structured. The people are not scripted.**
