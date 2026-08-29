# ACCEPTED v016 — SECOND-SEED + PAIRED-COUNTERFACTUAL VALIDATION

## Scope

v016 is a **validation checkpoint**, not a new canonical simulation scenario. Canonical authority remains accepted v015 seed 1701 at day 462.

## Canonical baseline

- DB: `state/ugarit_living_v015.sqlite`
- seed: `1701`
- day: `462`
- events: `6,608`
- accepted cognition: `157`
- state hash: `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`
- exact replay: 157 recorded decisions, 0 new cognition, exact hash

## Second-seed validation

Tool: `scripts/semantic_seed_validation.py`

Inputs:

- source policy/history: accepted v015 seed 1701
- destination RNG seed: `1702`
- target day: `462`
- explicit reviewed overrides: `runs/VALIDATION_SEED1702_OVERRIDES.json`

Result: `runs/VALIDATION_SEED1702.json`

- reached day `462`
- completed target: true
- `164` accepted semantic/fresh validation decisions
- `0` rejected
- `0` pending
- `0` open scenes
- `6,632` events
- `34` runtime minor-illness circumstances vs `27` in seed 1701
- `0` negative stocks
- `0` resource shortfalls
- `0` overdue obligations
- validation state hash `870ac079134c5f6c9ef75af64f5fb1113b23ba73b30d54652c047cd3c8633405`

Containment/material audit: `runs/VALIDATION_SEED1702_INVARIANTS.json`

- delivery before arrival: `0`
- arrival before departure: `0`
- message-derived knowledge before delivery: `0`
- negative stocks: `0`
- shortfalls: `0`
- overdue obligations: `0`
- rejected/pending/open cognition state: all `0`

## Structural comparison

Artifact: `runs/VALIDATION_SEED_COMPARISON.json`

The following mechanism counts remain identical across seeds 1701 and 1702 through day 462:

- marriage concluded: `1`
- kin care fulfilled: `8`
- kin care deferred: `2`
- care-informed property preference: `1`
- property-maintenance reserve established: `1`
- adult harbor progression: `1`
- alternate metal exchanges completed: `2`
- finished metalwork recycling: `4`
- workshop tool damage: `1`
- workshop repair completed: `1`
- local weather/storage exposures: `2`
- weather protection completions: `2`
- trade commitments: `3`
- explicit wait decisions: `30`

The accepted timing of those major mechanisms also remains aligned in the comparison artifact.

## Seed-specific cognition findings

The seed change is not behaviorally empty.

1. P12 receives minor illness despite having no seed-1701 illness template; fresh reviewed seed cognition is required.
2. P1 likewise receives previously unseen illness episodes.
3. Repeated seed-1702 illness exhausts H-WIDOW ritual materials faster. Šapšu's old 0.20-material illness policy becomes invalid and is rejected by normal action validation at day 351. The reviewed valid replacement uses 0.10 ritual goods plus practical rest.
4. By Bat-Rapiu's day-381 illness H-WIDOW has only ~0.05 ritual goods. Her reviewed response becomes a non-material spoken household observance plus rest, rather than inventing an arbitrary tiny material expenditure.
5. Rapanu receives the day-390 communal-feast contribution boundary and makes a fresh bounded 0.40 grain + 0.10 ritual-goods contribution from H-SCRIBE.

At day 462 H-WIDOW ritual goods are ~0.05 under seed 1702 versus ~0.30 under seed 1701. The negotiated 0.40 property reserve and 2.80 liquid silver remain intact in both.

## Paired harbor counterfactual

Tool: `scripts/paired_harbor_progression_validation.py`
Artifact: `runs/VALIDATION_HARBOR_COUNTERFACTUAL.json`

Both branches restore the same v015 day-459 state and apply the same P11 progression request.

- accept branch: P12 accepts; P11 becomes `harbor_coordinator` + sailor, porter ends;
- refuse branch: P12 refuses; P11 remains porter + sailor.

Declared invariants all pass:

- P11 legal status remains `free_laborer` in both;
- H-HARBOR senior membership remains identical;
- no negative resource stocks;
- no rejected/pending/open jobs/scenes;
- accept branch has coordinator role;
- refusal branch retains porter role and never creates coordinator role.

The day-462 occupation payload changes accordingly, proving the decision is causally meaningful without leaking into unrelated legal/household state.

## Interpretation boundary

The second-seed run is **semantic policy-transfer validation plus explicit reviewed fresh overrides**, not an independent end-to-end cognition sample. It tests robustness to stochastic history while holding much of decision policy constant.

Do not infer behavior frequencies or historical probabilities from these two seeds.

Next: fresh-cognition paired evaluation on selected controlled scenes.
