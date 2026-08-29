# STATUS

**Checkpoint:** accepted-candidate v017 fresh-cognition paired validation over the unchanged canonical v015 day-462 runtime.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, canonical SQLite and acceptance/validation manifests govern implementation beneath those authorities.

## Canonical strict runtime

v016-v017 are validation-only. Canonical simulation remains accepted v015:

- DB `state/ugarit_living_v015.sqlite`
- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- day **462**
- hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`
- **6,608 events**
- **157 accepted / 0 rejected / 0 pending / 0 open**
- exact replay requirement: 157 decisions, 0 new cognition, exact hash

Canonical manifest: `runs/ACCEPTED_DAY462_V015_HARBOR_LIFE_COURSE.md`.
Prior validation: `runs/ACCEPTED_V016_SECOND_SEED_COUNTERFACTUAL_VALIDATION.md`.
v017 validation: `runs/ACCEPTED_V017_FRESH_COGNITION_PAIRED_VALIDATION.md`.

## v017 fresh-cognition paired result

Ten new cognition decisions were made from ten sealed validation packets arranged as five controlled pairs. They are validation evidence only: none is copied into canonical history.

1. **Šapšu illness / ritual stock** — adequate stock produces a 0.20-material observance + rest; near-depleted stock produces a zero-material spoken observance + rest.
2. **Urtenu recycling / finished-output stock** — 0.75 finished output supports lossy recycling; 0.21 causes a wait that preserves nearly exhausted finished work.
3. **Kothar care / competing duty** — without conflict he fulfills care; with an explicit same-day recovery-rest obligation he defers one episode while keeping the continuing obligation active.
4. **Kothar stewardship / liquid silver** — 3.20 silver supports the agreed 0.40 reserve; 0.20 silver leads him to decline presently unfundable terms.
5. **Yabninu shipping / knowledge** — one unconfirmed report leads to independent inquiries; two delivered discordant reports lead to waiting rather than invented certainty.

All ten decisions pass the normal validator, create zero rejected jobs and zero negative stocks, and all five causal-sensitivity checks pass.

`tests/test_v017_fresh_cognition_pairs.py` reproduces all ten disposable branches and reapplies the frozen decisions. No branch SQLite file is canonical or committed.

## Interpretation / next priority

v017 demonstrates fresh-cognition causal sensitivity across resources, obligations and epistemic state. It does **not** measure instability because each packet has only one fresh cognition attempt.

Highest-value next step is repeated fresh cognition on a selected identical-packet subset (several independent attempts per packet), comparing action validity, controlled-factor sensitivity, unsupported invention, persona/relationship continuity and rationale/action-family variance. Frequencies remain model diagnostics, never historical probabilities.

Do not add a new world mechanic merely for variety; let repeated validation expose the next real modeling deficiency.

**The world is structured. The people are not scripted.**
