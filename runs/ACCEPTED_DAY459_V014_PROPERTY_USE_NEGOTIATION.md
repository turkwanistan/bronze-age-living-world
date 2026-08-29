# ACCEPTED DAY 459 — v014 HOUSEHOLD PROPERTY-USE NEGOTIATION

Accepted strict checkpoint for `state/ugarit_living_v014.sqlite`.

## Gate

- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.12.0`
- schema: `3`
- day: **459**
- state hash: `6e92d7ab618cc014b5a6668b63753c46780745d4542e272b0ca8580f3dd1c5a2`
- events: **6,537**
- cognition: **153 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **80/80**
- exact replay: **153 stored decisions / 0 new cognition / exact hash**
- negative stocks / false shortfalls / overdue scheduled obligations: **0 / 0 / 0**

## Accepted behavior

### Current property use is separated from inheritance

`ASM-FIXTURE-035` turns Bat-Rapiu's already-active, care-informed, non-binding preference into a bounded current-use negotiation rather than an automatic property transfer.

Strict day-459 sequence:

1. P15/Bat-Rapiu proposes earmarking **0.80 silver** for `household_property_maintenance`, naming P16/Kothar as proposed steward.
2. P10/Šapšu independently counters at **0.40 silver** and requires joint approval for future use. Her packet shows adult H-WIDOW membership, care/ritual goals, limited ritual stock and the research-derived distinction between current property use and inheritance.
3. P15 accepts the smaller jointly reviewed reserve rather than escalating.
4. P16 receives separate stewardship consent and accepts. He is not appointed without consent.

Only step 4 changes material state:

- H-WIDOW `silver`: **3.20 → 2.80**
- H-WIDOW `property_maintenance_reserve`: **0 → 0.40**
- total liquid+earmarked silver remains **3.20**
- active `household_property_stewardship` obligation names P16 as steward and P10 as joint reviewer

The existing `care_informed_priority` property preference remains active and explicitly non-binding. No ownership, inheritance, marriage or succession state is created or changed.

### Agency regression

A direct regression drives the same proposal → counter → counter acceptance chain and then has P16 decline stewardship. In that branch no reserve is created, no stewardship obligation becomes active and no silver moves. Household agreement therefore cannot override the proposed steward's individual consent.

## Evidence / rules

- `CLM-GEN-009`
- `CLM-GEN-020`
- `ASM-FIXTURE-035`
- `MAP-042` → `RULE-HOUSEHOLD-PROPERTY-USE-001`

## Limitations

- The people, timing, 0.80/0.40 amounts, reserve abstraction, stewardship label and joint-approval rule are fixture mechanics.
- No Ugaritic inheritance rule, co-ownership doctrine, testament, dowry transfer or succession result is asserted.
- The earmarked reserve has not yet been spent; a future material maintenance decision must precede any expenditure.
