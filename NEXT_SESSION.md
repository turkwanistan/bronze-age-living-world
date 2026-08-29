# NEXT SESSION

Start from accepted v016 validation in `STATUS.md` and `runs/ACCEPTED_V016_SECOND_SEED_COUNTERFACTUAL_VALIDATION.md`. Canonical runtime remains accepted v015 day 462.

1. Verify Git, authority hashes, canonical `state/current.json`, full test suite, and exact **157-decision** replay of `state/ugarit_living_v015.sqlite`.
2. Reproduce the seed-1702 validation using `scripts/semantic_seed_validation.py` and `runs/VALIDATION_SEED1702_OVERRIDES.json`; it must reach day 462 with no failures or invariant violations.
3. Reproduce `scripts/paired_harbor_progression_validation.py`; all paired invariants must remain true.
4. Highest-value next milestone: **fresh-cognition paired evaluation**, not another simulation feature.
   - choose ~5–10 consequential scenes from the existing behavioral library;
   - vary one controlled factor at a time (knowledge, household obligation, institution/access, material constraint, status/role or relationship history);
   - obtain fresh cognition rather than semantic policy transfer;
   - compare action validity, causal sensitivity, unsupported invention, persona drift and relationship continuity;
   - do not score historical realism with one number and do not treat choice frequencies as historical probabilities.
5. Especially valuable pairs include:
   - Šapšu illness with adequate vs depleted ritual stock;
   - Kothar care need with no conflict vs harvest/own-illness conflict;
   - P11 harbor progression accepted vs refused;
   - P7 recycling with sufficient finished stock vs severe finished-stock depletion;
   - household property reserve with steward consent vs steward refusal;
   - shipping information with one report vs contradictory delivered reports.
6. Keep seed-1702 as validation evidence only. Do not promote it over the canonical seed-1701 strict history.
7. Add no new shock/mechanic merely for variety. Let validation reveal the next real modeling gap.
8. Every future canonical behavior checkpoint still requires exact replay; validation checkpoints must clearly label whether cognition is transferred, fresh, or counterfactual.

Current canonical v015 facts:

- day 462, seed 1701, scenario 0.13.0;
- 6,608 events; 157 accepted decisions;
- hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`.

Current v016 validation facts:

- seed 1702 reaches day 462 with 6,632 events and 164 accepted decisions;
- 34 stochastic minor illnesses vs 27 in seed 1701;
- critical mechanism counts/timing remain stable;
- H-WIDOW ritual goods diverge materially (~0.05 vs ~0.30) because of extra illness burden;
- semantic-transfer validation has 0 rejected/pending/open jobs and 0 containment/material violations;
- harbor accept/refuse paired counterfactual passes all declared invariants.

**The world is structured. The people are not scripted.**
