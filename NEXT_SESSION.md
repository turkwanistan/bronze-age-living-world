# NEXT SESSION

Start from the accepted strict v004 day-90 checkpoint in `STATUS.md` and `runs/ACCEPTED_DAY90_V004_REALISM.md`.

1. Verify Git/repository state, authority hashes, `state/current.json`, and host-local `state/ugarit_living_v004.sqlite` before changing behavior.
2. Run the full **39-test** suite and exact recorded-decision replay of v004 to day 90. Replay must apply 21 stored decisions, make 0 new cognition calls, and reproduce hash `973f348742a5da1db23264b1485cd4e583ae951229976b40f25100f1bdd29890`.
3. Preserve v002, v003, and v004 as accepted histories. If scene-generation or fixture-baseline rules change, rebuild a fresh candidate from seed rather than mutating an accepted DB.
4. Continue the research-driven ordinary-life plan rather than adding isolated benchmark events. Highest-value next systems:
   - **household/kin disagreement:** resource priorities, outside work, care, property use, marriage/household strategy, apprenticeship, or support obligations;
   - **reusable dispute ladders:** private negotiation → kin/patron mediation → compensation/obligation → ritual/oath/official procedure only where locally supported;
   - **life-course mechanics:** marriage, household fission/fusion, inheritance/property succession, birth/death, aging, apprenticeship progression, migration;
   - **agricultural/material depth:** crop/livestock work, storage loss, tools, water/weather pressure, household production outputs and seasonal bottlenecks without inventing quantitative historical rates;
   - **trade/information depth:** recurring counterparties, damaged/delayed cargo, trusted brokerage, scribal/language mediation, multiple network alternatives, and provenance-preserving rumors;
   - **religious/social calendar depth:** feast invitations, participation memory, specialist consultation, household disagreement over cost/interpretation, and seasonal/crop/livestock concerns.
5. Generalize state-driven situation eligibility. v004 now has emergent repeated workshop scarcity, recurring trade, recurring ritual, recurring palace labor, and seasonal escalation. Continue moving away from one-time fixed-day benchmark scenes while preserving deterministic replay and explicit assumptions.
6. Preserve baseline stability. `ASM-FIXTURE-014` intentionally makes routine weekly provisioning neutral against configured daily need; do not reintroduce guaranteed poverty/wealth drift merely to manufacture decisions. Material pressure should come from explicit modeled causes.
7. Test **persistent consequences**, not just immediate action validity. Prior aid, debt, water favors, occupational output, trade completion, institutional service, feast participation, refusals, and obligations should alter later packets/choices where relevant while unrelated characters remain contained.
8. Move toward the Phase-5 behavioral gate of **50–100 inspected cognition decisions** and then a full ordinary-year gate. Use paired/counterfactual packets where useful; never interpret model choice frequency as historical prevalence.
9. Deepen Ugarit research only when it changes an active rule. Priority uncertainties: ordinary debt/property procedure, institutional labor/service, household production, feast/status behavior, local dispute resolution, marriage/inheritance, port contracting, multilingual mediation, and ordinary names/social context.
10. Add observer/inspection tooling only when it helps evaluate simulation quality. Do not add generic agent infrastructure, model APIs, microservices, a new database, or a new SBC generation without a demonstrated reusable substrate deficiency.
11. At each coherent accepted checkpoint, update evidence mappings, tests, `STATUS.md`, `NEXT_SESSION.md`, `state/current.json`, and a new acceptance manifest. Exact replay with zero new cognition calls remains mandatory.

Current accepted v004 gate facts:

- day 90, seed 1701, scenario 0.2.0;
- state hash `973f348742a5da1db23264b1485cd4e583ae951229976b40f25100f1bdd29890`;
- 1,225 canonical events;
- 39/39 tests passing;
- 21 accepted cognition decisions, 0 rejected/pending;
- exact replay with 21 stored decisions and 0 new cognition calls;
- 0 resource-shortfall scenes;
- 0 message temporal/containment violations;
- 16 situation trigger types;
- 192 occupation cycles / 96 household labor allocations / 24 routine household rituals / 12 port cycles;
- two delayed trade exchanges completed;
- palace labor can conflict with harvest and later complete;
- craft scarcity emerges from consumed inputs;
- reciprocal social credit survives into later cognition and can be cleared by occupational output;
- observed seasonal transition: harvest/threshing → dry-summer storage/vines.

The governing principle remains: **The world is structured. The people are not scripted.**
