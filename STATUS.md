# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; first strict 60-day Ugarit gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` preserved exactly; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` preserved exactly; SHA-256 `2e713f1d1b72b1c58bc532de261a86ca00834aecd84645a95f9624e57bba766d`.
- Current permanent repository, canonical SQLite state, tests, and accepted evidence govern implementation details after those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v002.sqlite`.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- current/accepted day: **60**
- state hash: `2b59046401f398c24604eee4242e12865690a64749811b6c56d31c5c3eb0f504`
- events: **577**
- cognition: **8 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **27/27 passing**
- recorded-decision replay to day 60: **exact hash match**, 8 stored decisions applied, **0 new cognition calls**

Acceptance evidence is summarized in `runs/ACCEPTED_DAY60.md`.

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
- fail-closed typed action validation including epistemic leakage, route availability, resource control, and atomic application;
- delayed engine-owned message delivery and recipient knowledge only on delivery;
- typed `send_message` cognition action with engine-selected route/delay and provenance;
- merchant/harbor information-uncertainty chain using Yabninu, Abdi-Rashap, and Dagan-beli without specifying a historical shipment outcome;
- forward-looking `RULE-RESOURCE-RUNWAY-001`, replacing the former absolute grain threshold with projection over current stock, configured daily need, receipt timing, and receipt amount;
- regressions for safe low-stock bridging, genuine projected shortfall, deterministic projection, delayed-message containment, route validation, replay, and authority integrity;
- exact replay from seed + accepted stored cognition without re-querying ChatGPT.

## Day-60 qualitative gate

The accepted run contains no `household_resource_shortfall` scenes. Cognition remained sparse: 8 jobs over 60 days. Situation triggers include merchant information uncertainty, delivered inquiries, contradictory/incomplete reports, reciprocal obligation, debt repayment, and minor illness. Message-derived knowledge has zero pre-delivery temporal violations.

The old day-56 candidate DB remains diagnostic evidence only. Its identity/hash and the intentionally unresolved `JOB-576143bba3e7ae07` are preserved in `artifacts/diagnostic/day56_candidate/README.md`; the binary was not rewritten or transferred through Base64.

## Not yet claimed

- historically calibrated household resource rates/quantities;
- Ugarit-specific ordinary debt/legal procedure resolution beyond bounded fixture mechanics;
- final verified ordinary-name pool by date/social context;
- broad situational diversity across water access, household work disagreement, feast/status reciprocity, palace labor requests, and other non-crisis life;
- 50–100 inspected character cognition decisions;
- observer UI;
- geopolitics/collapse systems;
- evidence that a new Self-Building Computer generation is needed.

## Guardrails

All fixture quantities remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates. Character cognition may use only sealed packet information available to that character at that time. Historical uncertainty, epistemic uncertainty, and runtime stochasticity remain distinct. Culture constrains institutions/roles/affordances; it does not generate civilization-wide personality stereotypes.
