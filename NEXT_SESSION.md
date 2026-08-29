# NEXT SESSION

Start from the accepted strict v005 day-140 checkpoint in `STATUS.md` and `runs/ACCEPTED_DAY140_V005_HOUSEHOLD_LIFECYCLE.md`.

1. Verify Git/repository state, authority hashes, `state/current.json`, and host-local `state/ugarit_living_v005.sqlite`.
2. Run the full **43-test** suite and exact recorded-decision replay to day 140. Required gate: 40 stored decisions, 0 new cognition calls, hash `959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df`.
3. Preserve v002-v005 accepted histories. If scene generation, fixture initialization, role workflows or canonical assumptions change, build a fresh v006 candidate from seed instead of mutating v005.

## Highest-value next development

### 1. Marriage / household formation / property strategy

Build the next life-course layer without assuming one universal patrilocal or inheritance model. Use evidence-labeled alternatives and household-specific circumstances. Needed capabilities:

- marriage/partnership proposal as negotiation between people and affected households;
- household membership change, property/resource contributions and obligations as canonical consequences;
- support for staying, joining, fissioning or other locally plausible household arrangements without making one model default destiny;
- widowhood/remarriage/property-claim implications only where evidence supports the rule;
- inheritance/property succession first as bounded household/property claims, not a complete universal legal code.

### 2. Naturally generated disputes over actual state

Keep `I-MEDIATION` abstract unless local research supports a named procedure. Generate disagreements from real state rather than fixed drama:

- scarce workshop or household input allocation;
- damaged/missing goods;
- water/property use;
- debt/favor performance;
- labor commitments;
- inheritance/property claims;
- marriage/household strategy;
- reputation/testimony.

Do **not** force a refusal merely so mediation appears in strict history. Let actor choices determine whether a disagreement settles privately or escalates.

### 3. Agriculture / livestock / storage depth

Replace more of the stable provisioning abstraction with explicit causal household production while maintaining a stable no-shock baseline:

- crop stages tied to the existing calendar;
- household labor allocated to field, vine/olive, livestock, processing and storage work;
- tools/animals/water/weather affecting output qualitatively before attempting historical quantitative calibration;
- storage and spoilage as explicit state;
- avoid reintroducing guaranteed poverty drift.

### 4. Port / trade / multilingual information depth

- multiple recurring counterparties rather than one supplier/contact path;
- damaged/delayed cargo and alternate network routes;
- market purchase vs reciprocal credit vs patron support as different choices;
- scribe/interpreter involvement when records/language matter;
- literacy/language constraints in packets;
- reserve renegotiation when household capital or obligations materially change.

### 5. Continue toward behavioral and ordinary-year gates

- reach **50–100 inspected cognition decisions** without raising cognition merely for the metric;
- continue strict time toward a full 360-day ordinary year;
- audit character differentiation, repeated-context behavior, memory causality, relationship/conflict consequences and household strategies;
- use paired/counterfactual packet tests where useful; never treat LLM decision frequency as historical prevalence.

## Current accepted v005 facts

- day 140 / seed 1701 / scenario 0.3.0;
- hash `959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df`;
- 1,966 canonical events;
- 43/43 tests passing;
- 40 accepted cognition decisions / 0 rejected / 0 pending / 0 open scenes;
- exact replay with 40 decisions and 0 new cognition;
- 0 resource-shortfall scenes;
- 0 message temporal violations;
- household reserve accepted day 91 and visibly binds Yabninu at day 126;
- Niqmepa progressed day 91 from apprentice to attached recognized craft worker;
- informal refusal→mediation ladder is regression-tested but was not invoked in strict history;
- Urtenu/Yabninu have completed two reciprocal workshop-credit cycles and opened a third at day 140;
- Arhalbu deferred during the intensity-1.00 harvest bottleneck but accepted palace service during the later intensity-0.88 processing/field-preparation phase;
- seasonal rescheduling now searches the full modeled calendar for a genuinely lower-intensity phase.

Do not add generic agent infrastructure, new databases, model APIs, microservices, or a new SBC generation without a demonstrated reusable deficiency.

The governing principle remains: **The world is structured. The people are not scripted.**
