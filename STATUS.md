# STATUS

**Checkpoint:** accepted strict Ugarit v012 workshop-tool interruption + repair gate at day 443.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v012.sqlite`; v002-v011 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.10.0`, schema `3`
- accepted day **443**
- hash `46bea8ae1c1614e51e3e11b7372f955af4fd5bc5a9fd4ac95da59e648c668c5b`
- **6,300 events**
- **144 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **73/73 tests**
- exact replay: **144 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls, overdue scheduled obligations, delivery-before-arrival or knowledge-before-delivery violations

Acceptance manifest: `runs/ACCEPTED_DAY443_V012_TOOL_REPAIR.md`.

## v012 result

The first post-v011 master metalwork cycle that is otherwise viable is interrupted by one bounded tool/mold failure on day 434. H-CRAFT has ~0.16 metal and 0.70 charcoal; damage occurs before either input is consumed and sets `workshop_tool_condition` to 0. P7 spends 0.10 finished metalwork on repair and schedules one day of downtime. The day-435 completion restores condition to 1.0. Ordinary day-441 work then consumes the preserved 0.15 metal + 0.20 charcoal and produces 0.08 finished work. Damage and repair each occur exactly once.

Existing household/economic constraints remain causal: P3 still protects the 16.5 silver reserve, P7 still makes zero post-refusal resource requests to P3, and unrelated illness decisions remain sparse and individually grounded.

## Current limitations

Tool condition is a bounded engineering abstraction, not a generic durability simulator. Repair uses workshop output rather than a separate specialist. The current market no-lot state is still fixture-bounded. Agricultural weather/storage shocks, shared/renegotiated care, property-use disagreement, a second life-course transition, language/scribal transaction constraints and second-seed/paired-counterfactual validation remain future work.

**The world is structured. The people are not scripted.**
