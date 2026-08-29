# STATUS

**Checkpoint:** accepted permanent OptiPlex implementation; strict day-360 Ugarit v008 full ordinary-year gate accepted.

## Authority

- `bronze-age-simulation-encyclopedia.md` remains the primary supplied historical/research foundation; SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` remains the revised research-driven implementation plan; SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, evidence mappings, tests, canonical SQLite, and acceptance manifests govern implementation details beneath those authorities.

## Accepted strict runtime

Current canonical host-local DB: `state/ugarit_living_v008.sqlite`. v002-v007 remain prior accepted histories and must not be mutated.

- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario version: `0.6.0`
- schema version: **3**
- accepted day: **360**
- state hash: `66afa78360be1ba12b67639e844aee71079480d1df562df45f450e514796f6ce`
- events: **5,073**
- cognition: **106 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full tests: **58/58 passing**
- recorded-decision replay to day 360: **exact hash match**, 106 stored decisions, **0 new cognition calls**
- message delivery-before-arrival violations: **0**
- knowledge-before-delivery violations: **0**
- resource-shortfall scenes/events: **0**
- negative resource stocks: **0**
- overdue scheduled obligations: **0**
- global composition-neutral provisioning: **5.08/day**, exactly equal to the configured neutral baseline

Acceptance evidence is summarized in `runs/ACCEPTED_DAY360_V008_FULL_YEAR.md`.

## Full ordinary-year gate

v008 is the first accepted run to traverse a complete modeled 360-day year and return to the starting seasonal phase:

- day 0: cereal harvest/threshing, intensity 1.00;
- day 60: dry-summer storage/vines, 0.68;
- day 120: grape/olive/field preparation, 0.88;
- day 180: early rains/sowing, 0.98;
- day 240: wet-winter growth, 0.55;
- day 300: spring growth/weeding, 0.80;
- day 360: cereal harvest/threshing, 1.00.

Routine deterministic life still dominates the record: 2,880 consumption events, 816 occupation work cycles, 408 household labor allocations, 408 neutral weekly receipts, 96 routine household rituals, and 51 port/market cycles. Consequential cognition remains sparse at 106 accepted decisions across 32 trigger types.

## v008 additions and observed consequences

### Winter draft-team maintenance and reciprocal labor

`ASM-FIXTURE-025` extends the already-explicit H-FARM draft-team fixture into one bounded wet-winter maintenance episode. Two weekly winter condition cycles reduce abstract condition from 1.00 to 0.90. Ilimilku can either absorb the maintenance internally or ask Arhalbu to answer the remembered sowing favor through one practical labor day.

Strict history chooses the reciprocal path:

1. Ilimilku remembers the day-183 draft help and P13's outstanding social favor;
2. on day 252 he asks Arhalbu for one winter maintenance labor service;
3. Arhalbu independently accepts from his sealed packet;
4. the service completes on day 253, restoring condition to 1.00;
5. both P1↔P13 favor balances return to zero only after completion;
6. trust/respect rise modestly in both directions;
7. the resolved winter episode stops further automatic condition degradation for the remainder of that modeled winter.

Exact condition values, cadence, service duration, and household pairing are engineering fixtures, not historical animal-care rates or exchange values.

### Workshop social credit adapts to shrinking supply

The P7↔P3 workshop relationship reaches six fully repaid reciprocal metal cycles. v008 fixes two long-horizon problems:

- `ASM-FIXTURE-026` seals the originating support amount on new v008 reciprocal obligations and caps a later finished-metalwork return suggestion at the smaller originating amount. A 0.15 metal advance therefore suggests at most 0.15 finished metalwork rather than the legacy 0.30 fixture amount.
- Urtenu adapts request size as Yabninu's raw metal stock shrinks: 0.6 → 0.3 → 0.15 → a requested 0.12 deficit.

On day 308, Yabninu naturally refuses the 0.12 request because only 0.15 raw metal remains and there is no standing obligation to continue financing the workshop. This is the first strict naturally arising workshop/supplier refusal after six completed cooperative credit cycles. It produces modest bilateral relationship strain (`conflicts=1`) without destroying the exchange relationship.

The refusal remains causally visible: Urtenu's later day-322/336/350 packets retain the recent refusal/decision history and he repeatedly pauses rather than immediately re-requesting unchanged scarce stock. This packet-memory policy is an engineering containment rule, not a historical behavioral claim.

At day 360 P3↔P7 have no open reciprocal obligation or favor balance. Yabninu retains 0.15 raw metal; Urtenu remains supply-constrained at 0.03 metal rather than obtaining infinite fixture credit.

### Care / property persistence

Kothar fulfills six concrete continuing-care episodes for Bat-Rapiu over the accepted year. The task varies in winter (`winter_household_maintenance_and_errands`) rather than repeating one identical support task forever. Bat-Rapiu's day-214 `care_informed_priority` property preference remains active and non-binding. No ownership, inheritance, or resource transfer occurs, and the continuing-care obligation remains active.

### Earlier systems remain causal

- Pidduya's 16.5-silver household reserve remains active and repeatedly prevents Yabninu from committing new discretionary port capital.
- The P16/P10 marriage remains canonical; Šapšu stays resident in H-WIDOW while retaining ritual/healing roles.
- H-FARM/H-DEPEND seasonal surplus and stored goods remain separate from staple grain.
- Arhalbu's sowing draft-access favor is fully reciprocated in winter rather than becoming a priced debt.
- Palace labor continues to reschedule only across high-intensity agricultural bottlenecks and complete when conditions permit.
- Information messages still obey delayed delivery and character knowledge containment.

## Evidence / tests added for v008

- `CLM-GEN-011` — winter weather/animal care/agricultural-asset maintenance can create household labor demands, without supplying a Ugaritic cadence or condition rate;
- `ASM-FIXTURE-025` — bounded draft-team winter-maintenance/favor fixture;
- `ASM-FIXTURE-026` — conservative reciprocal-return cap for smaller originating support;
- `MAP-029` — winter reciprocal labor;
- `MAP-030` — reciprocal-return cap;
- `MAP-031` — recent conflict/refusal memory retention in sealed packets;
- regression coverage in `tests/test_v008_winter_reciprocity.py`;
- total suite: **58 tests**.

## Current weaknesses / not yet claimed

- neutral staple provisioning is still an engineering stability substrate rather than a crop-yield economy;
- agriculture does not yet model crop-specific yields, seed stocks, quantified land tenure, broad tool inventories, weather distributions, herd demographics, births/deaths, fodder balances, or disease;
- only one draft-team maintenance episode is modeled; this is not a general livestock simulator;
- the workshop now has a genuine supply bottleneck but only one known metal supplier in the strict packet; recycling, alternate suppliers, substitute materials, and broader market routes are not yet implemented;
- Bat-Rapiu's property preference remains non-binding; there is no succession procedure, inheritance transfer, death trigger, or universal Ugaritic inheritance rule;
- no second generated marriage/household-formation transition, birth, death, widowhood transition, migration, or divorce yet;
- language/interpreter constraints and alternate foreign trade routes remain shallow;
- runtime illness frequency remains an explicit unhistorical fixture used to exercise response logic;
- completing one ordinary year demonstrates stability for this seed and decision history, not historical prevalence or statistical validation across populations/seeds;
- collapse/geopolitics remains intentionally out of scope until richer ordinary networks and shocks are ready.

## Guardrails

All fixture quantities/cadences remain explicit `ASM-FIXTURE-*` abstractions and must not be presented as historical rates/events. Character cognition may use only sealed packet information available at that moment. Historical uncertainty, epistemic uncertainty, runtime randomness, and engineering calibration remain distinct. Culture constrains institutions, roles, norms, obligations, and affordances; it does not create civilization-wide personality stereotypes.

**The world is structured. The people are not scripted.**
