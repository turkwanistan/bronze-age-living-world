# ACCEPTED — Day 375 v009 Network Alternatives

## Gate

- scenario: `0.7.0`
- schema: `3`
- seed: `1701`
- accepted day: **375**
- canonical events: **5,290**
- cognition: **114 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- state hash: `7ea6a82c61fcd10f94b1e741b357efba0bafb50e5acaa24ebf4e0e6319c4ada3`
- tests: **61/61 passing**
- recorded replay: **114 decisions, 0 new cognition calls, exact hash match**

## Accepted behavior

v009 retires the obsolete single-supplier workshop loop after Yabninu's day-308 scarcity refusal.

Urtenu receives a bounded alternatives decision rather than another automatic request to Yabninu. Two alternatives exist:

1. lossy remelting: 0.20 finished metalwork -> 0.12 raw metal under `ASM-FIXTURE-027`;
2. a provenance-preserving alternate-market search under `ASM-FIXTURE-028`.

Strict history chooses the network path:

- day 361: Urtenu asks Yabninu only for an introduction to P11;
- day 361: Yabninu grants the introduction without transferring scarce material;
- day 361: Urtenu sends P11 an inquiry; P7 still has no private alternate-metal knowledge;
- day 362: P11 independently reports only `PROP-METAL-ALT-001`;
- day 363: the report reaches P7; P12's terms remain unknown;
- day 363: P7 sends P12 a second inquiry;
- day 364: P12 independently reports `PROP-METAL-TERMS-001`;
- day 365: the terms reach P7 and become actionable;
- day 365: Urtenu pays 0.30 silver for a delayed 0.30-metal fixture lot;
- day 368: the scheduled external lot delivers 0.30 metal;
- day 371: ordinary workshop production consumes 0.15 of that metal and produces 0.08 finished metalwork.

P7 learns the market lead only on day 363 and the terms only on day 365. There are zero delivery-before-arrival or knowledge-before-delivery violations. No P7->P3 resource request occurs after the day-308 refusal.

The accepted exchange creates durable market-contact state between P7 and P12; P12 also remembers the accepted transaction. P7->P11 remains an introduced harbor-information relationship rather than being rewritten as a supplier relationship.

## Care consequence

At day 364, Kothar's seventh continuing-care episode lands during the modeled cereal-harvest intensity 1.00 bottleneck. After six prior fulfillments, he defers one support day rather than treating care as unconditional automation. The continuing-care obligation and Bat-Rapiu's non-binding property preference both remain active; no inheritance or property transfer occurs.

## Non-claims / limitations

- Recycling is implemented and regression-tested but strict v009 chose the network path.
- The 0.20->0.12 recycling ratio is not historical evidence.
- P11/P12, the fixture market lead, exact 0.30/0.30 terms and three-day delivery are simulation calibration, not a reconstructed historical shipment or price.
- One successful alternate lot does not create a permanent second supplier or infinite market access.
- Broader cargo damage/delay, interpreter/language constraints, repeated alternate sourcing, and counterfactual/second-seed behavior remain future work.
