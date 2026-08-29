# STATUS

**Checkpoint:** accepted strict Ugarit v014 household property-use negotiation gate at day 459.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v014.sqlite`; v002-v013 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.12.0`, schema `3`
- accepted day **459**
- state hash `6e92d7ab618cc014b5a6668b63753c46780745d4542e272b0ca8580f3dd1c5a2`
- **6,537 events**
- **153 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **80/80 tests**
- exact replay: **153 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls or overdue scheduled obligations

Acceptance manifest: `runs/ACCEPTED_DAY459_V014_PROPERTY_USE_NEGOTIATION.md`.

## v014 result

Bat-Rapiu's care-informed property preference finally affects current household strategy without becoming ownership or inheritance.

On day 459 Bat-Rapiu proposes earmarking **0.80 silver** for H-WIDOW property maintenance with Kothar as proposed steward. Šapšu, now a married-in adult household member, independently counters at **0.40 silver with joint approval required**, preserving more liquid household silver while still supporting maintenance. Bat-Rapiu accepts the counter rather than escalating the disagreement. Kothar then receives a separate stewardship-consent decision and accepts.

Only after all three decisions does canonical state move **0.40 H-WIDOW silver → 0.40 `property_maintenance_reserve`** and create an active `household_property_stewardship` obligation for Kothar. H-WIDOW liquid silver falls from 3.20 to 2.80; total earmarked+liquid silver remains 3.20. The stewardship provenance records Šapšu as joint reviewer.

The pre-existing `care_informed_priority` preference remains active and non-binding. No ownership, inheritance, marriage, or succession state changes. A regression separately proves that Kothar can decline after Bat-Rapiu and Šapšu agree, in which case no reserve is established and no silver moves.

## Current limitations / next priorities

- The reserve amount, joint approval structure and stewardship role are engineering fixtures, not a reconstructed Ugaritic property procedure.
- No succession or inheritance transfer is modeled.
- `property_maintenance_reserve` is an earmark abstraction; spending it should require a real future maintenance decision before deeper property machinery is added.
- Highest-value next step is a **second independent life-course transition** or **second-seed / paired-counterfactual validation**, rather than another scripted household shock.
- Language/interpreter or scribal-record constraints should be added only when they materially alter a multi-party transaction.

**The world is structured. The people are not scripted.**
