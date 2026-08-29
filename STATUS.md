# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-90 Ugarit v004 lifeways-realism gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` remains the primary supplied historical/research foundation; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` was deliberately revised on 2026-08-29 to incorporate the research-driven ordinary-life realism substrate requested during development; current SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Current repository state, accepted evidence mappings, tests, and canonical SQLite govern implementation details after those authorities.

## Accepted strict runtime

Current canonical host-local DB: `state/ugarit_living_v004.sqlite`. Earlier v002/v003 histories remain prior accepted checkpoints; v004 was rebuilt from seed after realism and baseline-calibration changes rather than mutating those accepted histories.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario version: `0.2.0`
- accepted day: **90**
- state hash: `973f348742a5da1db23264b1485cd4e583ae951229976b40f25100f1bdd29890`
- events: **1,225**
- cognition: **21 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **39/39 passing**
- recorded-decision replay to day 90: **exact hash match**, 21 stored decisions applied, **0 new cognition calls**
- message temporal violations: **0**
- resource-shortfall scenes: **0**

Acceptance evidence is summarized in `runs/ACCEPTED_DAY90_V004_REALISM.md`.

## Implemented realism substrate

- explicit 360-day modeled seasonal calendar with research-constrained ordering and fixture-labeled exact alignment (`ASM-FIXTURE-008`);
- seasonal context compiled into sealed cognition packets without exposing omniscient world state;
- recurring role-specific occupation cycles for all 16 important people;
- household labor-allocation events so multiple roles compete for the same people and seasonal bottlenecks alter opportunity cost;
- material textile workflow: fiber consumption → textile goods;
- material metalwork workflow: metal/charcoal consumption → finished metalwork;
- neutral routine provisioning baseline (`ASM-FIXTURE-014`) so ordinary no-shock life is not structurally impoverished/enriched by arbitrary fixture receipts;
- recurring household ritual observance outside illness scenes, with real ritual-goods cost;
- bounded communal rite/feast contribution scene where participation/reputation competes with household stores;
- recurring port/market cycles linking merchant, sailor/porter, market trader, scribe/interpreter roles;
- delayed material trade commitments: silver is committed immediately and goods arrive only after engine-owned delay;
- recurring palace labor requests, with cognition only when institutional extraction conflicts with a seasonal household bottleneck;
- emergent craft-supply pressure from actual consumed workshop inputs rather than a hard-coded crisis date;
- reciprocal social credit for socially mediated resource supply instead of resource magic, free anonymous gifts, or invented fixed-price contracts;
- first consequential craft↔merchant exchange creates a persistent relationship and open obligation;
- later workshop shortage packet includes that prior obligation, causing Urtenu to avoid deepening dependence while stock remains usable;
- occupational output can later satisfy reciprocal social credit, clearing both the obligation and favor balance;
- all prior delayed-message, household-work, water-access, debt, obligation, ritual, replay-order, atomicity, and epistemic-containment rules remain active.

## Day-90 qualitative gate

The 90-day history contains **16 cognition trigger types** while cognition remains sparse at 21 decisions. Routine life dominates history rather than crisis:

- 720 routine consumption events;
- 192 occupation work cycles;
- 96 household labor-allocation events;
- 96 weekly baseline receipts;
- 24 routine household ritual observances;
- 12 port/market cycles;
- 4 messages sent and 4 delivered;
- 2 delayed trade commitments and 2 completed exchanges;
- 2 palace labor requests and 2 completed services;
- 3 minor-illness circumstances / 3 ritual responses;
- 2 workshop supply-pressure scenes;
- 1 communal feast contribution;
- 1 debt repayment;
- 1 outside-work chain;
- 1 water negotiation chain;
- 1 reciprocal social-credit return.

Two modeled seasonal phases are actually observed in the accepted slice: `cereal_harvest_and_threshing` through the early history and `dry_summer_storage_and_vines` from day 63 onward. Arhalbu rescheduled palace labor during the harvest bottleneck and later completed it; a later palace request in the lower-intensity season completed without needing cognition.

The strongest persistence chain is Urtenu↔Yabninu:

1. repeated metalworking consumes workshop inputs;
2. day 56 low metal creates a real supply-pressure decision;
3. Urtenu requests a bounded amount from Yabninu;
4. Yabninu supplies 0.6 metal as open reciprocal social credit;
5. the exchange creates a new `exchange_contact` relationship and open obligation;
6. by day 84, low metal recurs, but Urtenu remembers the obligation and chooses to stretch current stock rather than ask again;
7. by day 86, accumulated finished metalwork creates a voluntary return opportunity;
8. Urtenu returns 0.3 finished metalwork, fulfilling the obligation;
9. by day 90 both directed favor balances are zero and trust/respect are higher than at relationship creation.

No message-derived knowledge appears before delivery. No undelivered message has recipient knowledge. The accepted history contains no household-resource-shortfall scenes after neutral baseline calibration.

## Evidence / tests added for v004

- `MAP-011` — seasonal occupation workflow;
- `MAP-012` — household labor allocation;
- `MAP-013` — recurring household ritual;
- `MAP-014` — seasonal institutional labor conflict;
- `MAP-015` — recurring delayed port trade;
- `MAP-016` — reciprocal social credit and occupational-output return;
- `MAP-017` — neutral routine provisioning stability gate.

New regression coverage is in `tests/test_lifeways_realism.py`; total suite is 39 tests.

## Not yet claimed / current weaknesses

- exact historical agricultural calendar dates, production rates, wages, ration rates, trade prices/profits, corvée cadence, ritual calendar, or reciprocal-return equivalence;
- one full ordinary year across all modeled seasonal phases;
- 50–100 inspected character cognition decisions;
- generalized crop/livestock yield and storage-loss mechanics rather than the current stable provisioning baseline plus selected specialist production chains;
- deeper marriage, inheritance, birth/death, household fission/fusion, aging, apprenticeship completion, and migration;
- reusable multi-step dispute ladders across property, damaged goods, animals, inheritance, reputation, and institutional mediation;
- broader multilingual/literacy consequences and foreign-contact network development;
- generalized reputation propagation beyond directed relationships, favors, obligations, memories, and specific scene effects;
- observer UI;
- geopolitics/collapse systems;
- evidence that a new Self-Building Computer generation is needed.

## Guardrails

All fixture quantities/cadences remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates or events. Character cognition may use only sealed packet information available to that character at that time. Historical uncertainty, epistemic uncertainty, and runtime stochasticity remain distinct. Culture constrains institutions, roles, norms, obligations, and affordances; it does not generate civilization-wide personality stereotypes.

The governing principle remains: **The world is structured. The people are not scripted.**
