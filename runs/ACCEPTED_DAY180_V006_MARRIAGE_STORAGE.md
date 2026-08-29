# ACCEPTED DAY-180 V006 — MARRIAGE, KINSHIP, AND SEASONAL STORAGE

This manifest freezes the strict v006 candidate after the research-driven marriage/life-course and agricultural-storage tranche.

## Canonical checkpoint

- DB: `state/ugarit_living_v006.sqlite` (host-local, Git-ignored)
- run: `RUN-3dda7920595c1748`
- seed: 1701
- scenario: 0.4.0
- schema: 2
- day: 180
- events: 2,540
- cognition: 59 accepted / 0 rejected / 0 pending
- open scenes: 0
- state hash: `d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb`
- full suite: 48/48 PASS
- recorded replay: 59 decisions applied / 0 new cognition / exact hash match

## Research-to-model boundary

Source-supported structure:

- marriage can link households, residence, care, property expectations and kin networks;
- marriage rules vary by place/status/time and should not be universalized;
- household/labor composition changes through marriage/life course;
- seasonal processing/storage/surplus can become consequential;
- household strategy and reciprocity constrain individual choices.

Explicit simulation calibration:

- P16/P10 pairing and day-150 communal-gathering opportunity (`ASM-FIXTURE-019`);
- H-WIDOW/H-RITUAL bounded residence options and optional P16→P15 care term (`ASM-FIXTURE-020`);
- seasonal-produce quantities, threshold, 5% exposed-loss cadence, and 0.9 preservation yield (`ASM-FIXTURE-021`).

No historical Kothar/Šapšu marriage, exact Ugaritic matchmaking practice, dowry/bridewealth, residence rule, storage rate, crop yield, or spoilage rate is claimed.

## Strict marriage trace

Day 150:

1. P16 requests discussion; he does not know P10's private preference.
2. P10 independently agrees only to explore terms.
3. P15 proposes H-WIDOW residence + continuing P16 care to P15.
4. P9 accepts after the packet makes explicit that P10's ritual/healing roles remain active.
5. P16 gives separate final consent.
6. P10 gives separate final consent.
7. Only then: normalized marriage row, spouse + affinal kinship edges, P10 household move, relationship/memory updates, and continuing-care obligation are created atomically.

Final individual decline is separately regression-tested and produces no marriage or mediation override.

## Material/labor consequences

- P10 membership closes in H-RITUAL at day 150 and opens in H-WIDOW.
- Day-154 H-WIDOW labor allocation contains P10 ritual/healing work + P15 household/property work + P16 porter/seasonal work.
- H-RITUAL day-154 named labor allocation contains P9 alone.
- P10's day-154 illness packet sees H-WIDOW's smaller ritual-goods stock and yields a modest 0.2 ritual response despite her high ritual commitment.
- P16→P15 continuing care is canonical and appears in relevant household packets.

## Agricultural/storage trace

- separate seasonal produce begins after day 140 during grape/olive/field-preparation work;
- exposed storage-loss events occur for H-FARM and H-DEPEND on days 150 and 180;
- P1 preserves 0.4 on day 154 and 0.4 on day 180;
- P13 preserves 0.4 on day 168;
- day-180 H-FARM: 0.72 stored seasonal goods + 0.3486 exposed seasonal produce;
- day-180 H-DEPEND: 0.36 stored seasonal goods + 0.1843 exposed seasonal produce;
- preservation/storage loss does not alter staple grain.

## Persistent systems retained

- P3 household silver reserve remains 16.5 and blocks new discretionary trade on day 154;
- P7/P3 third workshop-credit cycle closes on day 170; all three reciprocal obligations are fulfilled and favor balances are zero;
- P13's stored surplus is visible before day-175 palace labor and contributes to a different material context for compliance;
- delayed-message containment remains intact;
- no false resource-shortfall scenes/events.

## Qualitative counts

- 26 scene trigger types;
- 1,440 routine consumption events;
- 400 occupation cycles;
- 200 household labor allocations;
- 200 weekly baseline receipts;
- 48 routine household ritual observances;
- 25 port cycles;
- 12 runtime minor illnesses;
- 59 accepted consequential decisions.

## Known limitations

- neutral staple provisioning is not yet composition-responsive after household membership changes;
- continuing care is canonical but has not yet generated a care-demand/inheritance consequence;
- agriculture remains an abstract surplus/storage layer rather than crop/livestock/weather production;
- no strict-history mediation was forced; mediation remains regression-tested;
- full 360-day ordinary-year acceptance remains future work.
