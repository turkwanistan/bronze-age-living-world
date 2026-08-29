# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-140 Ugarit v005 household-strategy / life-course gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` remains the primary supplied historical/research foundation; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` is the revised research-driven implementation authority from 2026-08-29; SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Current repository state, accepted evidence mappings, tests, and canonical SQLite state govern implementation details after those authorities.

## Accepted strict runtime

Current canonical host-local DB: `state/ugarit_living_v005.sqlite`. v002, v003, and v004 remain prior accepted histories. v005 was rebuilt from seed whenever fixture/scene logic changed rather than mutating an accepted history.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario version: `0.3.0`
- accepted day: **140**
- state hash: `959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df`
- events: **1,966**
- cognition: **40 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **43/43 passing**
- recorded-decision replay to day 140: **exact hash match**, 40 stored decisions applied, **0 new cognition calls**
- message temporal violations: **0**
- resource-shortfall scenes: **0**

Acceptance evidence: `runs/ACCEPTED_DAY140_V005_HOUSEHOLD_LIFECYCLE.md`.

## Accepted v005 additions

### Household strategy constrains later individual action

Pidduya's `merchant_account_partner` role can now generate a state-driven household resource-priority review after repeated completed trade exchanges. On day 91 she asked Yabninu to preserve 16.5 abstract silver units. He accepted.

The agreement is an active canonical `household_reserve_commitment`, not prose. Typed trade validation must honor it. Yabninu made one final 0.5 fixture commitment on day 98, leaving exactly 16.5. At the next port opportunity on day 126 he chose to wait because another standard commitment would violate the household agreement. Regression tests independently prove that a commitment crossing the floor fails closed.

`ASM-FIXTURE-016` labels the trigger/floor as engineering calibration, not a reconstructed Ugaritic household-capital or property rule.

### Apprenticeship becomes a life-course transition

Niqmepa's progression eligibility is derived from accumulated canonical work history rather than a birthday or fixed story beat. Day-91 eligibility required at least 91 simulation days in-role, twelve recorded apprenticeship work cycles, and workshop output.

Niqmepa requested recognition from Urtenu; he did not self-promote. Urtenu granted it. Canonical consequences:

- `craft_apprentice` ended day 91;
- `recognized_craft_worker` began day 91;
- household membership changed `apprentice` → `attached_worker`;
- simulation legal status changed to `dependent_craft_worker`;
- mentor relationship types and trust/respect changed;
- both actors formed autobiographical life-course memories;
- later occupation cycles use the new role and its material production workflow.

`ASM-FIXTURE-017` explicitly says the timing, label, status and production values are simulation calibration rather than reconstructed Ugaritic apprenticeship law/rank/duration.

### Reusable informal dispute ladder

`I-MEDIATION` is now an abstract, bounded kin/patron/elder-style mediation interface. Supported proposal scenes can proceed private negotiation → direct refusal → relationship strain → one optional mediation review. A review reopens a typed decision for the relevant party; it does not invent an omniscient mediator verdict or universal Bronze Age court.

Regression coverage proves refusal increments directed conflict state, lowers trust, opens at most one mediation review, and can produce a later typed settlement. The strict v005 history contains **0 proposal refusals and 0 mediation reviews** because both new day-91 negotiations resolved consensually. Conflict is available but not manufactured for coverage.

`ASM-FIXTURE-018` leaves exact mediator identity, authority, and local Ugaritic procedure unspecified.

### Persistent specialist exchange network

Urtenu↔Yabninu now demonstrate repeated supply without resource magic or automatic entitlement:

1. first workshop metal advance → open reciprocal obligation → finished-metalwork return → fulfilled;
2. second advance day 98 → Urtenu later refuses to stack a third unpaid advance → second output return day 128 → fulfilled;
3. third advance begins day 140 only after the second is cleared.

The relationship accumulates trust/respect across successful cycles. Each new transfer still creates a distinct open reciprocal obligation; no fixed price, interest rate, maturity, or standing contract is asserted.

### Seasonal palace conflict generalized

Development at day 140 exposed that the old reschedule helper only knew the end of cereal harvest. During the later `grape_olive_and_field_preparation` phase it would have suggested another still-high-intensity day. `RULE-SEASONAL-LABOR-CONFLICT-001` now searches the modeled 360-day calendar for the next genuinely lower-intensity phase.

The strict history itself shows contextual behavior rather than one scripted response: Arhalbu deferred palace service during the earlier intensity-1.00 cereal-harvest bottleneck, but on day 140 accepted service during the intensity-0.88 grape/olive/field-preparation phase because institutional compliance outweighed the less-severe labor conflict.

### Existing v004 realism substrate remains active

- 360-day seasonal calendar and sealed seasonal context;
- recurring occupation and household labor-allocation cycles;
- textile and metal material workflows;
- neutral baseline provisioning;
- recurring household ritual + communal feast;
- recurring port/market cycles and delayed exchanges;
- palace labor requests;
- emergent craft input scarcity;
- delayed information and packet containment;
- debt, reciprocal aid, outside work, water negotiation and social credit;
- exact recorded replay preserving same-day decision order.

## Day-140 qualitative gate

Routine life still dominates the accepted history:

- 1,120 routine consumption events;
- 320 occupation work cycles;
- 160 household labor-allocation events;
- 160 neutral weekly provisioning events;
- 32 recurring household ritual observances;
- 20 port/market cycles;
- 40 cognition jobs/accepted decisions total;
- 8 stochastic minor-illness circumstances with differentiated actor responses;
- 4 palace labor requests (all fulfilled; one rescheduled earlier, one accepted during a later bottleneck);
- 3 completed delayed port exchanges;
- 3 workshop resource-request chains by day 140;
- 2 fulfilled workshop reciprocal-credit returns and a third new obligation active at the gate.

Long-horizon causal examples:

- day 91 household reserve agreement → day 98 last permissible trade → day 126 trade restraint;
- Niqmepa apprenticeship history → negotiated day-91 role progression → later packet/status/workflow changes;
- first and second Urtenu/Yabninu credit cycles affect later willingness to request/supply and are cleared before new advances;
- same Arhalbu dispositions + different seasonal intensity produce different palace-labor choices.

No message-derived knowledge appears before delivery. No undelivered message has recipient knowledge. The accepted history contains no household-resource-shortfall scenes.

## Evidence / regression additions

- `CLM-GEN-005` — life course can change through apprenticeship/work specialization and other household transitions; local form remains uncertain.
- `CLM-GEN-006` — dispute-resolution routes can include private negotiation, kin/patron/elder mediation, compensation and later escalation, but exact ladders are local.
- `MAP-018` — household resource priority / reserve agreement.
- `MAP-019` — apprenticeship progression.
- `MAP-020` — bounded informal dispute ladder.
- `MAP-021` — seasonal palace rescheduling across the full modeled calendar.
- `ASM-FIXTURE-016..018` — explicit non-historical calibration boundaries for those systems.
- new regression file: `tests/test_household_disputes_lifecycle.py`.

## Not yet claimed / current weaknesses

- a full ordinary 360-day year;
- the Phase-5 target of 50–100 inspected cognition decisions (current accepted total: 40);
- marriage formation, marriage negotiation, household fission/fusion, birth/death, inheritance/property succession, aging and migration;
- Ugarit-specific local legal/dispute procedures beyond the deliberately abstract informal mediation interface;
- a naturally occurring strict-history refusal/mediation case (capability is test-proven, not forced into history);
- generalized crop/livestock yields, storage loss, tools, weather, water and agricultural output chains;
- alternate workshop suppliers / market substitution beyond the current Yabninu relationship;
- richer port counterparties, cargo damage/loss, multilingual/literacy brokerage and network alternatives;
- reserve renegotiation/release when household conditions materially change;
- generalized reputation propagation beyond directed relationships, conflicts, favors, obligations and memories;
- observer UI;
- geopolitics/collapse systems;
- evidence that a new Self-Building Computer generation is needed.

## Guardrails

All fixture quantities/cadences remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates or events. Character cognition may use only sealed packet information available to that character at that time. Historical uncertainty, epistemic uncertainty, and runtime stochasticity remain distinct. Culture constrains institutions, roles, norms, obligations and affordances; it does not generate civilization-wide personality stereotypes.

The governing principle remains: **The world is structured. The people are not scripted.**
