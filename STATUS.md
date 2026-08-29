# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-180 Ugarit v006 marriage/storage gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` remains the primary supplied historical/research foundation; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` remains the revised research-driven implementation plan; SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Current repository state, accepted evidence mappings, tests, canonical SQLite, and acceptance manifests govern implementation details beneath those authorities.

## Accepted strict runtime

Current canonical host-local DB: `state/ugarit_living_v006.sqlite`. v002-v005 remain prior accepted histories and must not be mutated.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario version: `0.4.0`
- schema version: **2**
- accepted day: **180**
- state hash: `d8f87ff19699e22b4f2ad00da5139c08a0a1bed9356a0661105b6d9807d8fdfb`
- events: **2,540**
- cognition: **59 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **48/48 passing**
- recorded-decision replay to day 180: **exact hash match**, 59 stored decisions applied, **0 new cognition calls**
- message temporal/containment violations: **0**
- resource-shortfall scenes/events: **0**

Acceptance evidence is summarized in `runs/ACCEPTED_DAY180_V006_MARRIAGE_STORAGE.md`.

## v006 additions

### Normalized marriage / kinship state

Schema v2 adds canonical `marriages` and `kinship_edges`. Existing fixture spouse relationships are normalized at day 0; schema-2 canonical hashing includes both tables. Schema-1 accepted histories keep the old canonical table set, and v005 still hashes exactly to `959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df` when opened by current code without migration.

The first generated marriage is Kothar (P16) and Šapšu (P10), produced by strict cognition on day 150 rather than prewritten as an outcome:

1. the communal gathering exposes a fixture-labeled discussion opportunity;
2. Kothar asks whether Šapšu is willing to discuss marriage;
3. Šapšu independently agrees only to discussion;
4. Bat-Rapiu proposes H-WIDOW residence plus continuing P16 support to her;
5. Attanu reviews and accepts because Šapšu's ritual/healing roles remain active;
6. Kothar gives separate final consent;
7. Šapšu gives separate final consent;
8. only then does the engine create the marriage, spouse/affinal kinship edges, household membership change, relationships/memories, and continuing-care obligation.

No dowry, bridewealth, marriage payment, property transfer, or universal Ugaritic residence rule is implied. `ASM-FIXTURE-019/020` own the pairing, timing, bounded residence options, and care-term representation.

After marriage:

- P10 moves from H-RITUAL to H-WIDOW as `married_in_adult`;
- P10 retains `ritual_assistant` / `healer_helper` roles;
- day-154 household labor allocation moves her work into H-WIDOW while H-RITUAL's named labor allocation becomes Attanu alone;
- P16↔P10 become spouses;
- P15↔P10 and P9↔P16 become affinal kin contacts;
- P16 has an active `continuing_kin_care` obligation toward P15;
- later P10 cognition packets contain normalized marriage/kinship and the care obligation, not only prose memories.

Final individual refusal is a terminal safe action for the marriage chain and is not overridden by mediation. Household terms may use the bounded informal mediation substrate; individual final consent may not.

### Seasonal agricultural surplus and storage

`ASM-FIXTURE-021` adds a separate post-day-140 surplus chain without changing neutral staple grain provisioning:

- relevant field workers generate `seasonal_produce` during the modeled grape/olive/field-preparation phase;
- exposed produce can lose a fixture 5% on the modeled storage-loss cadence;
- state-driven storage pressure appears only after exposed stock crosses the fixture threshold;
- `preserve_seasonal_surplus` converts bounded exposed produce to `stored_seasonal_goods` at a fixture 0.9 yield;
- preservation and loss events never modify staple `grain`.

Accepted strict results:

- Ilimilku preserves 0.4 exposed produce on day 154 and another 0.4 on day 180;
- Arhalbu preserves 0.4 on day 168;
- day-180 H-FARM holds 0.72 stored seasonal goods plus 0.3486 exposed produce;
- day-180 H-DEPEND holds 0.36 stored seasonal goods plus 0.1843 exposed produce;
- four explicit storage-loss events occur (H-FARM/H-DEPEND on days 150 and 180);
- no false household-resource-shortfall scenes are introduced.

The accepted slice now observes four modeled seasonal phases: cereal harvest/threshing, dry-summer storage/vines, grape/olive/field preparation, and the day-180 transition into early rains/sowing.

## Behavioral gate / persistence

The project has now crossed the Phase-5 target minimum of **50 inspected cognition decisions**: v006 contains 59 accepted decisions across **26 trigger types** while routine deterministic life still dominates history.

Major routine counts through day 180:

- 1,440 routine consumption events;
- 400 occupation work cycles;
- 200 household labor-allocation events;
- 200 weekly baseline receipts;
- 48 routine household ritual observances;
- 25 port/market cycles;
- 12 runtime minor-illness circumstances / 12 ritual responses.

Persistent earlier systems continue to matter:

- Pidduya's 16.5-silver household reserve remains active; Yabninu waits again on day 154 instead of violating it;
- Urtenu/Yabninu complete a third metal social-credit cycle by day 170; all three reciprocal obligations are fulfilled and both directed favor balances return to zero while trust/respect have increased;
- Arhalbu's new stored seasonal goods are visible before his day-175 palace-labor decision, where he chooses compliance rather than another deferral;
- marriage materially changes Šapšu's later illness packet: her high ritual commitment remains, but H-WIDOW has far fewer ritual goods than H-RITUAL, leading to a modest 0.2 household rite rather than an unconstrained specialist-scale response.

## Evidence / tests added for v006

- `CLM-GEN-007` — marriage can link households/property/residence/care while local terms vary;
- `CLM-GEN-008` — seasonal household production, processing, storage, and surplus can be consequential;
- `ASM-FIXTURE-019` — P16/P10 pairing and day-150 discussion opportunity;
- `ASM-FIXTURE-020` — bounded residence/care terms without universalizing Ugaritic marriage procedure;
- `ASM-FIXTURE-021` — separate seasonal surplus/storage quantities and loss calibration;
- `MAP-022` — typed marriage negotiation + normalized consequences;
- `MAP-023` — schema-versioned canonical hashing;
- `MAP-024` — separate seasonal surplus/storage chain.

New regression coverage is in `tests/test_marriage_agriculture.py`; total suite is 48 tests.

## Current weaknesses / not yet claimed

- household staple-food need/neutral receipt calibration is **not yet composition-responsive** when marriage changes household membership; v006 demonstrates labor/kin/care consequences but not demographic provisioning recalculation;
- the P16→P15 continuing-care obligation is canonical but has not yet generated an elder/support-demand situation or inheritance consequence;
- no dowry/bridewealth/property transfer is modeled for marriage;
- no new-household formation, divorce, birth, death, widowhood transition, or inheritance succession yet;
- agriculture currently models a separate surplus/storage chain, not crop-specific yields, livestock, tools/draft animals, weather variability, land tenure, or quantified historical production;
- strict v006 did not naturally require informal dispute mediation; the reusable mediation path remains regression-tested rather than forced into history;
- no full 360-day ordinary-year gate yet;
- broader multilingual/contracting/foreign-contact depth remains future work;
- no collapse/geopolitical layer should be added before ordinary-life systems remain stable over a full year.

## Guardrails

All fixture quantities/cadences remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates/events. Character cognition may use only sealed packet information available at that moment. Historical uncertainty, epistemic uncertainty, and runtime randomness remain distinct. Culture constrains institutions, roles, norms, obligations, and affordances; it does not create civilization-wide personality stereotypes.

The governing principle remains: **The world is structured. The people are not scripted.**
