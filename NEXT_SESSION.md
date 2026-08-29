# NEXT SESSION

Start from the accepted strict v006 day-180 checkpoint in `STATUS.md` and `runs/ACCEPTED_DAY180_V006_MARRIAGE_STORAGE.md`.

1. Verify Git/repository state, authority hashes, `state/current.json`, and host-local `state/ugarit_living_v006.sqlite` before changing behavior.
2. Run the full **48-test** suite and exact recorded-decision replay of v006 to day 180. Replay must apply **59** stored decisions, make **0** new cognition calls, and reproduce hash `d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb`.
3. Preserve v002-v006 as accepted histories. If scene-generation, schema, or fixture-baseline rules change, rebuild a fresh candidate from seed rather than mutating accepted DBs.
4. Highest-value next system: make **care/property consequences** active rather than passive hooks.
   - continuing elder/kin support requests and fulfillment;
   - remembered care affecting later property/inheritance preference where locally supported;
   - property-use disagreement and private negotiation before mediation;
   - inheritance/succession only with explicit evidence/fixture separation, not a universal Ugaritic rule.
5. Make household composition more materially legible without reintroducing arbitrary poverty drift.
   - design an explicitly engineered composition-responsive neutral provisioning method or another conservative representation;
   - prove conservation/stability before using it in strict history;
   - never smuggle dowry/bridewealth or household wealth transfer into marriage merely to create material consequences.
6. Deepen the **early-rains/sowing agricultural layer** from day 180 onward:
   - plowing/sowing labor bottlenecks;
   - tools/draft-animal access as bounded resources or obligations;
   - livestock care where evidence changes decisions;
   - weather/water pressure with historical rates left unspecified;
   - stored surplus influencing labor/trade/aid decisions;
   - keep neutral staple grain separate until a validated crop-production model can replace it safely.
7. Continue marriage/life-course mechanics cautiously:
   - second independent candidate only when state/evidence justify it;
   - new-household formation and residence alternatives;
   - aging, birth/death, widowhood, migration, apprenticeship/work progression;
   - final individual consent remains non-overridable by mediation.
8. Seek naturally arising disputes rather than manufacturing one. Good candidates: property use, care obligations, storage/tool access, trade terms, damaged goods, or competing household labor. Preserve the informal-first ladder and exact replay.
9. Deepen trade/information/language only where active rules need it: recurring counterparties, delayed/damaged cargo, scribal documentation, interpreter/language constraints, multiple network alternatives, provenance-preserving rumor.
10. The 50-decision minimum has been crossed. Next behavioral target is **75–100 inspected decisions plus the full 360-day ordinary-year gate**, with paired/counterfactual packet tests where useful. Never interpret model choice frequency as historical prevalence.
11. Do not add collapse/geopolitics, generic agent infrastructure, model APIs, microservices, a new database, or a new SBC generation without evidence that ordinary-life substrate or tooling actually requires it.
12. At every coherent accepted checkpoint, update evidence mappings, tests, protocol docs, `STATUS.md`, `NEXT_SESSION.md`, `state/current.json`, and an acceptance manifest. Exact replay with zero new cognition calls remains mandatory.

Current accepted v006 gate facts:

- day 180, seed 1701, scenario 0.4.0, schema 2;
- hash `d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb`;
- 2,540 events;
- 48/48 tests;
- 59 accepted cognition decisions / 0 rejected or pending;
- exact 59-decision replay / 0 new cognition;
- 26 trigger types;
- 400 occupation cycles / 200 household labor allocations / 48 household rituals / 25 port cycles;
- normalized marriage/kinship is canonical and schema-hashed;
- P16/P10 marriage concluded only after both households and both principals agreed;
- P10 moved to H-WIDOW while retaining ritual/healing roles;
- P16 retains active continuing-care obligation to P15;
- seasonal surplus/storage is separate from neutral staple grain;
- H-FARM and H-DEPEND both hold preserved seasonal goods;
- Yabninu's household reserve remains binding;
- three P7↔P3 reciprocal workshop-credit cycles are fulfilled;
- zero false shortfalls and zero message temporal/containment violations;
- current modeled phase is `early_rains_and_sowing`.

The governing principle remains: **The world is structured. The people are not scripted.**
