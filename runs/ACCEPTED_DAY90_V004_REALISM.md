# Accepted Day-90 V004 Lifeways Realism Gate

## Identity

- canonical DB: `state/ugarit_living_v004.sqlite` (host-local / Git-ignored)
- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.2.0`
- schema: `1`
- cognition protocol: `cognition-v1`
- accepted day: **90**
- canonical state hash: `973f348742a5da1db23264b1485cd4e583ae951229976b40f25100f1bdd29890`

## Acceptance gates

- full tests: **39/39 PASS**
- accepted cognition jobs: **21**
- rejected cognition jobs: **0**
- pending cognition jobs: **0**
- open scenes: **0**
- canonical events: **1,225**
- exact recorded-decision replay to day 90: **PASS**
- replay decisions applied: **21**
- replay new cognition calls: **0**
- replay rebuilt hash: `973f348742a5da1db23264b1485cd4e583ae951229976b40f25100f1bdd29890`
- message pre-delivery knowledge violations: **0**
- undelivered-message recipient-knowledge violations: **0**
- `household_resource_shortfall` scenes: **0**

## Ordinary-life density

Canonical event counts at acceptance include:

- `routine_consumption`: 720
- `occupation_work_cycle`: 192
- `household_labor_allocation`: 96
- `routine_weekly_receipt`: 96
- `household_ritual_observance`: 24
- `port_market_cycle`: 12
- `cognition_job_enqueued`: 21
- `decision_accepted`: 21
- `message_sent`: 4
- `message_delivered`: 4
- `resource_transfer`: 3
- `ritual_performed`: 3
- `runtime_circumstance`: 3
- `decision_to_wait`: 2
- `trade_exchange_committed`: 2
- `fixture_trade_exchange_completed`: 2
- `palace_labor_requested`: 2
- `palace_labor_completed`: 2
- single accepted chains for communal feast contribution, debt repayment, outside work, water negotiation, and reciprocal return.

Cognition trigger diversity: **16 trigger types**.

## Seasonal evidence in accepted history

Observed occupation-cycle phases:

1. `cereal_harvest_and_threshing`
2. `dry_summer_storage_and_vines` from day 63 onward

The seasonal context affected consequential cognition rather than serving as flavor only. Arhalbu rescheduled a palace labor obligation during the harvest bottleneck and completed it after the bottleneck. A later recurring palace service in the lower-intensity season completed without requiring a second conflict decision.

Exact dates/boundaries are `ASM-FIXTURE-008` calibration, not an attested Ugaritic calendar conversion.

## Accepted cognition history

1. day 7 — Yabninu seeks independent confirmation of stale shipping information.
2. day 8 — Abdi-Rashap reports only the harbor information he possesses.
3. day 8 — Dagan-beli reports only the independent market information she possesses.
4. day 9 — Yabninu waits rather than treat discordant reports as settled fact.
5. day 14 — Kothar asks for household agreement before outside porter work during harvest pressure.
6. day 14 — Bat-Rapiu accepts the bounded one-day opportunity.
7. day 18 — Ahatmilku asks for temporary negotiated water access.
8. day 18 — Talmiyanu grants a bounded temporary accommodation.
9. day 21 — Bat-Rapiu fulfills reciprocal food-aid obligation.
10. day 27 — Mullissu uses a modest rite plus practical rest for minor illness.
11. day 28 — Arhalbu fully repays debt while stores safely permit it.
12. day 30 — Bat-Rapiu makes a modest communal rite/feast contribution.
13. day 35 — Arhalbu reschedules palace labor past the harvest bottleneck rather than refuse it.
14. day 36 — Ahatmilku uses a modest rite plus practical rest for minor illness.
15. day 42 — Yabninu makes a small delayed port-trade commitment.
16. day 56 — Urtenu requests a modest workshop metal reserve after recurring production consumes input stock.
17. day 56 — Yabninu supplies metal as reciprocal social credit rather than a free gift/fixed-price fiction.
18. day 70 — Yabninu makes a second small port-trade commitment after the prior exchange completes.
19. day 78 — Talmiyanu uses a modest household rite plus rest for minor illness.
20. day 84 — Urtenu declines to ask Yabninu for more metal while he still owes him and has usable stock.
21. day 86 — Urtenu returns 0.3 finished metalwork and fulfills the reciprocal obligation.

All quantities/cadences in those decisions remain fixture calibration where explicitly labeled.

## Persistent consequence proof: craft ↔ merchant social credit

- recurring workshop cycles consumed metal and charcoal and produced finished metalwork;
- day 56 low metal emerged from that consumption;
- Urtenu requested 0.6 metal from Yabninu;
- Yabninu supplied it using `RULE-RECIPROCAL-SOCIAL-CREDIT-001` / `ASM-FIXTURE-013`;
- a new `exchange_contact` relationship and open reciprocal obligation were created;
- day 84 low metal recurred; Urtenu's sealed packet contained the prior transfer, obligation, favor balance, and relationship, and he chose to wait rather than deepen dependence;
- day 86 accumulated finished output made a return possible under `ASM-FIXTURE-015`;
- Urtenu returned 0.3 finished metalwork and fulfilled the obligation;
- at day 90 both P7→P3 and P3→P7 favor balances are 0; relationship trust/respect remain above their initial created values.

This demonstrates occupation → material dependency → social request → relationship/obligation → later constrained behavior → occupational-output repayment.

## Baseline stability correction

During development, extending the old fixture exposed that several configured weekly grain receipts were below seven configured daily needs, guaranteeing long-run decline even without a shock. That was rejected as artificial pressure rather than accepted history.

`ASM-FIXTURE-014` now calibrates routine weekly provisioning to exactly seven configured daily needs. This is an engineering stability baseline, not a historical ration/production claim. The accepted v004 history was rebuilt from seed after this change. No resource-shortfall scene appears through day 90.

## Evidence mappings added

- MAP-011 — `RULE-OCCUPATION-WORKFLOW-001`
- MAP-012 — `RULE-HOUSEHOLD-LABOR-ALLOCATION-001`
- MAP-013 — `RULE-RECURRING-HOUSEHOLD-RITUAL-001`
- MAP-014 — `RULE-SEASONAL-LABOR-CONFLICT-001`
- MAP-015 — `RULE-PORT-TRADE-CYCLE-001`
- MAP-016 — `RULE-RECIPROCAL-SOCIAL-CREDIT-001`
- MAP-017 — neutral routine provisioning stability gate

## Non-claims

This checkpoint does **not** claim exact historical dates, agricultural yields, household consumption/ration levels, wages, production rates, metal/textile conversion ratios, trade prices/profits, corvée cadence, ritual frequency, feast contribution norms, or reciprocal-return equivalence. Those remain explicit modeling assumptions where quantitative behavior is required.

The accepted result is a stronger causal ordinary-life substrate, not a quantitative reconstruction of Ugaritic economy or calendar.
