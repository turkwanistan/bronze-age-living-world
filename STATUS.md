# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-240 Ugarit v007 care/property/sowing gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` remains the primary supplied historical/research foundation; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` remains the revised implementation plan; SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, evidence mappings, tests, canonical SQLite, and acceptance manifests govern implementation details beneath those authorities.

## Accepted strict runtime

Current canonical host-local DB: `state/ugarit_living_v007.sqlite`. v002-v006 remain prior accepted histories and must not be mutated.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario version: `0.5.0`
- schema version: **3**
- accepted day: **240**
- state hash: `7cd79256a5affcff0b65b8c98f22be5078e46ab0bd2b3e0ce014e778f4363f86`
- events: **3,412**
- cognition: **80 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **53/53 passing**
- recorded-decision replay to day 240: **exact hash match**, 80 stored decisions, **0 new cognition calls**
- message temporal/containment violations: **0**
- resource-shortfall scenes/events: **0**
- trigger types observed: **30**

Acceptance evidence: `runs/ACCEPTED_DAY240_V007_CARE_SOWING.md`.

## v007 additions

### Replay and schema compatibility

Recorded replay now initializes from the source database's sealed scenario configuration rather than whatever scenario happens to be newest in the repository. Canonical behavior follows `runs.schema_version`; physical SQLite migrations may be newer without silently changing an accepted run's canonical hash surface or packet serialization.

Regression coverage proves the accepted v006 schema-2 day-180 history still rebuilds exactly under current v007 code with its original hash `d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb`.

### Composition-neutral household provisioning

`ASM-FIXTURE-022` makes neutral routine provisioning follow current household composition without introducing historical ration claims. Each living current member carries the per-person share implied by their day-0 fixture household. Daily neutral consumption and weekly neutral receipt move together.

After Šapšu's day-150 move:

- H-RITUAL effective daily need/receipt: **0.25 / 1.75 weekly**;
- H-WIDOW effective daily need/receipt: **0.73 / 5.11 weekly**;
- global effective daily neutral need remains exactly **5.08**, equal to the original total;
- no artificial household shortfall appears.

### Active kin care and property preference

The accepted P16→P15 continuing-care term now generates concrete support episodes under `ASM-FIXTURE-023`.

Strict history:

- day 184: Kothar fulfills the first bounded household/property support episode;
- day 214: Kothar fulfills the second;
- Bat-Rapiu then receives her own sealed `property_preference_review` packet;
- she records canonical preference `PREF-96dc12714e107631`, favoring P16 under `care_informed_priority` / `household_property_if_later_negotiated`.

The preference is deliberately **non-binding**. No property transfers, no inheritance executes, and the original continuing-care obligation remains active. This is living household strategy informed by remembered care, not a claimed Ugaritic inheritance rule.

### Early-rains sowing and draft access

`ASM-FIXTURE-024` makes the early-rains/sowing bottleneck materially and socially causal while keeping all quantities explicit fixtures.

Strict history:

- day 182: H-DEPEND has only 0.05 modeled sowing progress and lacks direct fixture draft access;
- Arhalbu asks Ilimilku for one bounded service;
- Ilimilku grants it after seeing the real household opportunity cost;
- day 183 service completion gives H-DEPEND **+0.10 sowing progress** and costs H-FARM **−0.05 sowing progress**;
- P13→P1 records one favor owed and trust/respect improve;
- by day 240 H-DEPEND has 0.55 modeled sowing progress and H-FARM 1.75.

A refusal→informal mediation→review path for the same draft request is regression-tested but was not forced into strict history.

### Seasonal institutional behavior

At day 210 the agricultural intensity is **0.98**. Arhalbu has recently relied on borrowed draft capacity and chooses to move his palace labor obligation to day 240 rather than abandon the narrow sowing window. On day 240 the modeled phase becomes `wet_winter_growth`, intensity **0.55**, and the palace service completes deterministically. No palace-labor obligation remains open.

### Persistent trade/craft constraints

- Pidduya's 16.5-silver household reserve remains binding through repeated day-182/day-210/day-238 port opportunities; Yabninu does not violate it.
- Urtenu/Yabninu complete the **fourth** full metal social-credit cycle by day 212.
- On day 224 Urtenu sees Yabninu's visible metal has fallen to 0.6 and reduces his next request from 0.6 to **0.3**, rather than asking to exhaust the supplier.
- Yabninu grants the reduced fifth credit while retaining 0.3 metal.
- The fifth reciprocal obligation is intentionally still active at the day-240 checkpoint; Urtenu has already chosen to wait rather than stack another request.

## Behavioral / ordinary-life gate

The strict history now contains **80 inspected accepted cognition decisions** across **30 trigger types**. Deterministic routine life remains dominant:

- 544 occupation work cycles;
- 272 household labor allocations;
- 64 routine household ritual observances;
- 34 port/market cycles;
- no false shortfalls;
- no rejected/pending cognition;
- no knowledge learned before message arrival.

## Current weaknesses / not yet claimed

- `property_preferences` are preferences only; no generalized property-use negotiation, succession execution, testament, inheritance share, death-triggered transfer, or legal adjudication exists yet.
- Continuing care currently uses one bounded fixture support kind and 30-day cadence; more varied care needs require additional evidence/engineering work.
- Sowing progress and draft-team access are engineering abstractions, not crop yield, animal ownership, plowing-rate, land-tenure, or Ugaritic livestock claims.
- The P13→P1 draft favor is remembered but does not yet have a reciprocal-return situation.
- Livestock lifecycle, weather variability, tool wear/repair, seed stocks, land parcels, and crop-specific production are not yet modeled.
- No birth, death, divorce, widowhood transition, migration, or generalized household fission/formation system yet.
- No full 360-day ordinary-year acceptance gate yet.
- Broader multilingual contracting, damaged cargo, interpreter constraints, and network alternatives remain future work.
- Collapse/geopolitics remains intentionally deferred until ordinary society is stable for a full modeled year.

## Guardrails

All fixture quantities/cadences remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates/events. Character cognition uses only sealed packet information available at that moment. Historical uncertainty, epistemic uncertainty, and runtime randomness remain distinct. Culture constrains institutions, roles, obligations, and affordances; it does not generate civilization-wide personality stereotypes.

**The world is structured. The people are not scripted.**
