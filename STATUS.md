# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-60 Ugarit v003 ordinary-social gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` preserved exactly; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` preserved exactly; SHA-256 `2e713f1d1b72b1c58bc532de261a86ca00834aecd84645a95f9624e57bba766d`.
- Current permanent repository, canonical SQLite state, tests, and accepted evidence govern implementation details after those authorities.

## Accepted strict runtime

Current canonical DB: `state/ugarit_living_v003.sqlite`. The earlier accepted `state/ugarit_living_v002.sqlite` remains an immutable baseline history; v003 was rebuilt from seed after scene-generation changes.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- current/accepted day: **60**
- state hash: `96994dcc063475fb2cc449d933d71510b6f99e6af23563bbfcbf393be7a9ce8c`
- events: **593**
- cognition: **12 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **30/30 passing**
- recorded-decision replay to day 60: **exact hash match**, 12 stored decisions applied, **0 new cognition calls**

Acceptance evidence is summarized in `runs/ACCEPTED_DAY60_V003_SOCIAL.md`. The prior gate remains in `runs/ACCEPTED_DAY60.md`.

## Implemented

- exact authority copies and authority SHA checking;
- historical-fidelity/evidence/model/cognition protocol documents;
- source/claim/assumption/rule/test evidence mappings;
- Ugarit research backlog and 12 behavioral evaluation situations;
- SQLite canonical schema including FTS5 memory;
- 8 households / 16 named important people with heterogeneous roles, status, relationships, beliefs, goals, and individual dispositions;
- places, routes, four initial institutions, household materials, debt, obligations, knowledge, memories, messages, scenes, cognition jobs, decisions, actions, and causal events;
- deterministic routine engine using explicitly abstract fixture quantities;
- strict advancement that halts at unresolved/rejected cognition;
- sealed temporal character packets;
- fail-closed typed action validation including epistemic leakage, route availability, resource control, scene/target constraints, and atomic application;
- delayed engine-owned message delivery and recipient knowledge only on delivery;
- typed `send_message` cognition action with engine-selected route/delay and provenance;
- merchant/harbor information-uncertainty chain using Yabninu, Abdi-Rashap, and Dagan-beli without specifying a historical shipment outcome;
- forward-looking `RULE-RESOURCE-RUNWAY-001`, replacing the former absolute grain threshold with projection over current stock, configured daily need, receipt timing, and receipt amount;
- household work negotiation: P16 can request household approval for a bounded fixture opportunity; acceptance schedules later engine-owned completion, resource receipt, memories, and relationship consequences;
- unequal water-access negotiation: a shared-access household can request a bounded accommodation from the scene-designated private-access neighbor; grants create temporary `I-WATER`-linked permission, favor/relationship effects, memories, and deterministic expiry;
- exact recorded replay now preserves **source decision application order**, including multiple cognition decisions on the same day and possible same-day follow-ups;
- regressions for resource runway, delayed-message containment, route validation, ordinary social chains, replay ordering, replay exactness, and authority integrity.

## Day-60 qualitative gate

The accepted v003 run contains no `household_resource_shortfall` scenes. Cognition remains sparse at 12 decisions across 60 days while situation diversity expands to 10 trigger types. New work and water chains each occur once and leave persistent material/social/autobiographical consequences rather than flavor-only events.

The work chain records request → household decision → scheduled commitment → next-day completion/resource receipt. The water chain records pressure → request → grant → favor/relationship change → deterministic expiry. Later character packets reflect these memories and relationship changes. Unrelated P14 and P13 packets remained byte-identical to the previous accepted history at their cognition boundaries, supporting containment.

The old pre-runway day-56 candidate remains diagnostic evidence only. Its identity/hash and intentionally unresolved `JOB-576143bba3e7ae07` are preserved in `artifacts/diagnostic/day56_candidate/README.md`; its binary was never rewritten or transferred through Base64.

## Not yet claimed / current weaknesses

- historically calibrated household resource rates, work compensation, travel speeds, or water-access duration;
- Ugarit-specific ordinary debt/legal/property/water procedure beyond bounded evidence-linked fixture mechanics;
- generalized emergent situation generation: the new work/day-14 and water/day-18 situations are currently deterministic benchmark fixtures;
- final verified ordinary-name pool by date/social context;
- broad ordinary-life diversity across feast/status reciprocity, palace labor/resource requests, craft/work complications, household disputes, market exchange, kin/marriage issues, and other non-crisis life;
- 50–100 inspected character cognition decisions;
- richer reputation propagation beyond directed relationship/favor state and memories;
- observer UI;
- geopolitics/collapse systems;
- evidence that a new Self-Building Computer generation is needed.

## Guardrails

All fixture quantities and benchmark circumstances remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates or events. Character cognition may use only sealed packet information available to that character at that time. Historical uncertainty, epistemic uncertainty, and runtime stochasticity remain distinct. Culture constrains institutions/roles/affordances; it does not generate civilization-wide personality stereotypes.
