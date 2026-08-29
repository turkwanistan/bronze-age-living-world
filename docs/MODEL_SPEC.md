# Model Specification (V0.1)

This is a lightweight ODD-inspired specification. It is intentionally narrower than the final project.

## Purpose

Test whether a small Ugaritic community can produce coherent ordinary social history before scaling population, geopolitics, crisis systems, or UI.

## Entities

- person
- household
- relationship
- place and route
- institution
- role
- material resource stock
- debt / obligation
- proposition / knowledge / memory
- message
- scene
- cognition job
- decision / typed action
- append-only event
- research source / historical claim / model assumption / evidence link
- run / scenario / simulation version / snapshot

## Time and space

- Simulation time is integer **day** for V0.1.
- Place is a simple graph, not GIS.
- Route travel time and institutional reach constrain contact and action.

## Process scheduling

Each simulated day runs, in order:

1. validate monotonic time;
2. apply routine household consumption and occupation-linked routine production/receipts;
3. mature due obligations/debts;
4. deliver due messages;
5. sample only declared runtime circumstances from the seeded RNG;
6. detect consequential situations;
7. enqueue cognition jobs without resolving them;
8. append canonical events in the same transaction as state changes;
9. advance run day.

## Interaction rules

Routine processes never require ChatGPT. Cognition is escalated when goals conflict, relationships or norms are at stake, information is ambiguous, negotiation is needed, or ritual/social interpretation materially affects action.

## Institutions in the first fixture

Only institutions needed by the micro-community exist initially:

- neighborhood well/access regime;
- local shrine/ritual specialist network;
- market/merchant-credit interface;
- palace administrative/requisition interface.

These are minimal procedural constraints, not a complete reconstruction of the Ugaritic state.

## Cognition escalation

The engine creates a `scene`, then a `cognition_job` with a packet compiled for one actor. A packet may contain only admissible current material state, actor traits/roles, relevant relationships, known propositions, relevant memories, norms/institutions, and typed action affordances.

## Stochastic processes

V0.1 permits low-frequency seeded routine circumstances (for example minor illness or message delay) only when the scenario declares the process. RNG never chooses whether a person betrays, marries, forgives, or violates a norm.

## Initialization

The Ugarit fixture initializes 8 households and 16 important people across farming, merchant, scribal, craft, ritual, harbor, dependent-labor, and widowed/elder positions. Display names are simulation identities; where an attested-name pool is used, that does **not** claim the simulated person is the historical bearer of the name.

Material quantities in the first fixture are abstract calibration units. They are scenario assumptions and must not be cited as historical measures.

## External inputs

- supplied encyclopedia;
- explicit supplemental research entered into `research/evidence-index/`;
- scenario values;
- RNG seed;
- recorded validated cognition decisions.

## Observations / evaluation targets

- resource conservation and no negative stocks;
- household differentiation;
- distinct role schedules;
- spatial/institutional constraints;
- information containment;
- relationship/obligation causality;
- religion as a causal decision input;
- replay determinism;
- cognition validation rejection rate and reasons;
- ordinary-life / constant-crisis ratio;
- causal trace completeness.

## Traceability contract

Every active historically specific rule should be traceable as:

`source → historical claim → interpretation/model assumption → rule/parameter → code → test → observable`

Current mappings live in `research/evidence-index/mappings.jsonl`. Uncalibrated fixture mechanics are explicitly tagged `FIXTURE_ASSUMPTION`, never silently promoted to historical fact.
