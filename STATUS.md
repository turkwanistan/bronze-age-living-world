# STATUS

**Checkpoint:** accepted v016 second-seed + paired-counterfactual validation over the canonical v015 day-462 runtime.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance/validation manifests govern implementation beneath those authorities.

## Canonical strict runtime

v016 changes validation tooling/evidence only; the canonical simulation remains accepted v015:

- DB `state/ugarit_living_v015.sqlite`
- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- day **462**
- hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`
- **6,608 events**
- **157 accepted / 0 rejected / 0 pending / 0 open**
- exact replay remains required and exact

Canonical runtime manifest: `runs/ACCEPTED_DAY462_V015_HARBOR_LIFE_COURSE.md`.
Validation manifest: `runs/ACCEPTED_V016_SECOND_SEED_COUNTERFACTUAL_VALIDATION.md`.

## v016 second-seed result

Seed `1702` was run to day 462 under the same v015 scenario using the validation-only semantic policy-transfer harness plus explicit reviewed fresh cognition only where the source policy could not legitimately cover the new situation.

Final seed-1702 validation state:

- day **462**
- **6,632 events**
- **164 accepted decisions**
- 0 rejected / pending / open
- **34 runtime minor-illness circumstances**, versus 27 in seed 1701
- 0 negative stocks, shortfalls or overdue obligations
- 0 message-arrival or knowledge-before-delivery violations
- validation hash `870ac079134c5f6c9ef75af64f5fb1113b23ba73b30d54652c047cd3c8633405`

Critical mechanisms remain structurally stable across both seeds, with the same counts and accepted timing for: marriage conclusion, the 8 fulfilled + 2 deferred care episodes, care-informed property preference, property-maintenance stewardship, two alternate-metal deliveries, four recycling episodes, one tool failure + repair, two local weather exposures/protections, three trade commitments, and P11 harbor specialization.

The meaningful divergence is concentrated in stochastic illness history and downstream resource pressure. Seed 1702 requires fresh/revised cognition when the source policy no longer fits:

- P12 has minor illness despite no seed-1701 P12 illness template; a modest first-episode response is reviewed explicitly.
- P1 similarly receives new illness episodes and gets a reviewed first response, then same-actor repeat reuse.
- Šapšu's fourth seed-1702 illness finds H-WIDOW ritual stock too low for her old 0.20-material response; the validator rejects the stale policy and the reviewed replacement uses a smaller 0.10 observance.
- Bat-Rapiu later finds only ~0.05 ritual goods remaining and switches to a non-material spoken observance plus practical rest rather than inventing an arbitrary tiny material cost.
- Rapanu, rather than a source-template feast contributor, receives the day-390 communal contribution boundary and independently contributes 0.40 grain + 0.10 ritual goods from H-SCRIBE.

At day 462 H-WIDOW therefore holds ~0.05 ritual goods in seed 1702 versus ~0.30 in seed 1701, while its 0.40 property-maintenance reserve and 2.80 liquid silver remain intact in both.

## v016 paired counterfactual

From the same v015 day-459 pre-progression state:

- **accept branch:** P12 accepts P11's request; porter ends at day 460, `harbor_coordinator` begins, sailor remains;
- **refuse branch:** P12 refuses; porter+sailor remain active and no coordinator role is created.

Both branches reach day 462 with P11 still a `free_laborer`, still H-HARBOR senior, no negative resources and no rejected/pending/open jobs. Day-462 occupation output differs exactly where expected.

## Interpretation / next priorities

- Semantic policy transfer is not independent cognition and must not be used to estimate behavior frequency.
- The validation result supports robustness of causal mechanics under a different stochastic history, not historical probability claims.
- Highest-value next validation is a **fresh-cognition paired subset**: rerun selected situations with new cognition under controlled packet differences (knowledge, household obligation, institution, status or resources) and measure validity/coherence without expecting identical choices.
- Do not add another world mechanic until validation identifies a real modeling gap.

**The world is structured. The people are not scripted.**
