# Bronze Age Living World — Implementation Plan

**Project:** Bronze Age Living World  
**Canonical repository target:** `/home/mcp/projects/projects/bronze-age-living-world`  
**Primary historical authority supplied with this plan:** `bronze-age-simulation-encyclopedia.md`  
**Primary creative/reasoning engine:** ChatGPT in the active chat session  
**Primary development/runtime environment:** Optiplex via `Optiplex_MCP`  
**Capability experimentation / reusable tooling substrate:** `Optiplex_Lab` + Self-Building Computer (SBC)  
**Initial historical focus:** Ugarit-centered international Late Bronze Age world, approximately 1350 BCE  
**Core objective:** Build a persistent, evidence-constrained artificial society in which historically situated people live, remember, negotiate, worship, trade, marry, feud, cooperate, migrate, govern, exploit, care for one another, and respond to changing circumstances — with larger historical outcomes emerging from their accumulated interactions.

---

# 1. Vision

This project is not primarily a collapse simulator, a strategy game, a statistical model with generated dialogue, or a collection of historical chatbots.

It is an attempt to build a **living anthropological simulation of Bronze Age society**.

The system should make it possible to follow:

- a merchant household across three generations;
- a widow fighting relatives over inheritance;
- an Ugaritic scribe mediating between multiple languages and institutions;
- a Hittite governor balancing imperial demands with local survival;
- a farmer deciding whether to hide grain from an official;
- a priest whose interpretation of an omen changes a political decision;
- a Cypriot sailor whose delayed ship causes rumors in several ports;
- a foreign craft worker whose apprentice carries a technique into another community;
- an elite marriage that changes diplomatic relationships;
- a bound laborer whose family tries to redeem or protect them;
- a migrant household negotiating belonging in a suspicious host community;
- a ruler whose personal anxieties, household politics, religious obligations, prestige concerns, limited information, and material constraints combine into consequential policy.

The goal is not to make every person “historically accurate” in an unknowable psychological sense.

The goal is to build **historically constrained social worlds in which recognizable human individuality operates inside Bronze Age structures of choice**.

A believable character is not made Bronze Age by archaic dialogue. A character becomes historically situated because the things that matter to them, the people who can constrain them, the institutions they can use, the risks they fear, the gods and ancestors they understand, the information they possess, the property they can control, and the consequences of violating expectations are appropriate to their place, period, status, household, occupation, and history.

The uploaded encyclopedia is the starting historical knowledge base. Its central methodological commitments should remain foundational:

- there is no universal Bronze Age personality;
- households and relationship networks are often more important than atomized individual preference;
- culture should alter expectations, incentives, obligations, and sanctions rather than dictate personality;
- evidence quality varies radically by region and source type;
- uncertainty must remain visible;
- environmental shocks affect people through social institutions;
- trade, migration, diplomacy, religion, household life, law, and status are deeply interconnected;
- ordinary people must matter as much as rulers;
- large-scale historical change should emerge from lower-level interactions rather than be scripted as inevitable.

---

# 2. The central experimental question

The broad question is:

> **What kinds of social histories emerge when historically constrained Bronze Age people with persistent personalities, memories, relationships, institutions, beliefs, and material circumstances are allowed to live together over years and generations?**

Subquestions include:

- How do household obligations alter apparently rational economic choices?
- How do reputation, reciprocity, and patronage change trade and political behavior?
- How does information distortion change diplomacy, migration, and conflict?
- How does religious reasoning alter material decisions under uncertainty?
- How do cross-cultural encounters produce trust, misunderstanding, brokerage, imitation, hostility, marriage, and hybrid practice?
- How do individuals violate cultural expectations, and what happens when they do?
- How do institutional pressures reach ordinary households?
- How do household responses aggregate upward into institutional change?
- How do crises interact with preexisting personal relationships?
- Which institutions are resilient because people believe in them, rely on them, or reproduce them?
- Which institutions fail when specialist networks, trust networks, or household cooperation disappear?
- What kinds of memories become family stories or collective traditions?
- How do people adapt after institutions fail?
- How much of a later archaeological pattern could arise from very different lived histories?
- When multiple historically plausible institutional models exist, which ones create different social signatures?

A later research layer can run many alternative worlds, but **the first priority is depth of social life, not simulation count**.

---

# 3. Non-goals

## 3.1 Not Civilization-with-LLMs

Do not reduce cultures to factions with numerical bonuses or national traits.

State-level aggregates may exist, but they must be consequences of actual institutions, resources, households, and social networks.

## 3.2 Not a national-personality simulator

Never encode civilization-wide personality shortcuts such as “Hittite = pragmatic” or “Mycenaean = aggressive.”

Individuals vary. Culture controls social pressure, institutions, opportunities, concepts, and expected behavior.

## 3.3 Not a narrative generator pretending to simulate

Generated prose cannot substitute for canonical state.

If an agent says they give ten measures of barley, the transaction must occur in canonical state or be rejected. If someone dies, marries, owes a favor, acquires property, changes office, becomes injured, migrates, learns information, or sends a message, that must become structured state.

## 3.4 Not deterministic historical reenactment

The system must not force Ugarit to be destroyed, Hatti to collapse, a specific “Sea Peoples” story, historical rulers to make known historical choices, or every known war to occur.

Historical conditions may be initialized from evidence. The simulated future belongs to the simulation.

## 3.5 Not a perfect digital twin

We do not know enough. Unknowns should become uncertainty switches or competing models, not silently invented truth.

## 3.6 Not a full-world model on day one

Do not attempt 3300–1000 BCE globally. Begin with one deeply modeled social ecosystem and expand outward through actual interactions.

---

# 4. Starting world: Ugarit and the international system, c. 1350 BCE

The first serious world should begin around **1350 BCE**, before the Late Bronze Age transformations.

This period gives the experiment:

- a functioning international diplomatic system;
- Great King diplomacy;
- dynastic marriage;
- Hittite imperial/vassal politics;
- Egyptian imperial influence in the Levant;
- Ugaritic multilingual scribal culture;
- Cypriot/Alashiyan copper and maritime exchange;
- Babylonia and rising Assyria;
- Mitanni under pressure;
- multiple Canaanite/Syrian polities;
- Aegean/Mycenaean maritime connections;
- elite gift exchange;
- household agriculture;
- merchants and credit;
- military obligations;
- religious institutions;
- migration and foreign communities;
- multiple overlapping legal and social systems.

## 4.1 Deep simulation zone

V1 should model **Ugarit and its hinterland** in the greatest resolution.

Potential components:

- royal household;
- palace administration;
- scribal offices;
- merchant houses;
- harbor community;
- sailors;
- caravan traders;
- craft specialists;
- metal-related commerce;
- farmers;
- herders;
- dependent labor;
- enslaved/bound people where evidence supports them;
- religious specialists;
- local shrines;
- urban neighborhoods;
- rural villages;
- soldiers/guards;
- interpreters;
- foreign merchants and envoys;
- migrant households.

## 4.2 Persistent external social nodes

The initial world should include lower-resolution but persistent people and institutions representing Hatti, Egypt, Alashiya/Cyprus, neighboring Canaan/Syria, and selected Babylonia/Assyria/Mitanni/Mycenaean contacts.

The world expands **through contact**, not because a roadmap says every civilization deserves equal code.

---

# 5. The anthropological fidelity program

Deep cultural research is not pre-production flavor work. It is a **required implementation workstream**.

Before a culture, role, institution, or major practice receives high-resolution simulation, the project should build an evidence-backed dossier.

The uploaded encyclopedia is the baseline. Fresh targeted research should deepen it.

## 5.1 Research standards

Prioritize:

1. primary texts/translations where responsibly available;
2. archaeological site reports and material syntheses;
3. specialist monographs and peer-reviewed research;
4. bioarchaeology, isotopes, ancient DNA, archaeobotany, zooarchaeology, paleoclimate, residue/provenance work;
5. specialist encyclopedias/reference works;
6. cautious comparative anthropology where local evidence is weak.

Avoid building behavior from pop-history stereotypes, unsourced summaries, modern national narratives, later myths treated as direct testimony, or one spectacular elite source generalized to everyone.

## 5.2 Every cultural dossier should cover

### Geography and ecology
Water, soils, rainfall, crops, herding, seasonal constraints, transport, ports, topography, and resource bottlenecks.

### Political organization
Offices, ruler relationships, local authorities, territorial reach, taxation/tribute, military obligation, succession, vassalage, and patronage.

### Household and kinship
Household composition, marriage, residence, inheritance, care, fostering, divorce, widowhood, property transmission, headship, and lineage importance.

### Gender and life course
Legal rights, work, property, ritual roles, marriage expectations, mobility, childhood, apprenticeship, elder authority, and variation by status.

### Class/status/dependence
Elite, local notable, common household, dependent worker, slave/bound labor, foreigner, migrant, patron/client, specialist.

### Occupations
For every important role: daily work, seasonal rhythm, required skills, material dependencies, social leverage, vulnerabilities, interaction network, status, and routes of advancement/decline.

### Economy
Household subsistence, institutional redistribution, markets, credit, taxation, tribute, labor obligations, weights, commodities, property, debt, and trade.

### Religion
Household cult, temples, gods/ancestors, ritual calendars, divination, purity, omen systems, healing, funerary obligations, political legitimacy, and uncertainty about ordinary belief.

### Law and conflict resolution
Informal negotiation, kin mediation, patron intervention, compensation, courts, oath/divination, feud/retaliation, flight, and status-dependent access.

### Language and information
Spoken languages, scripts, literacy, interpreters, message formats, travel delays, information institutions, and likely misunderstanding points.

### Emotional/social situations attested in sources
Collect evidence of affection, grief, anger, status anxiety, insult, obligation, jealousy, fear, loneliness, generosity, neglect, piety, ritual anxiety, bargaining, resentment, patronage, and betrayal. Use these to build a repertoire of situations, not population stereotypes.

### Cross-cultural behavior
Foreigners, diaspora merchants, intermarriage, envoys, mercenaries, captives, language brokerage, adoption of practices, prestige imports, foreign gods, legal jurisdiction, and ambiguity where evidence is absent.

### Evidence gaps
Explicitly document what we do not know, competing reconstructions, archive bias, and which behaviors require cautious invention.

---

# 6. Research artifacts

Recommended repository structure:

```text
research/
├── evidence-index/
│   ├── sources.jsonl
│   └── claims.jsonl
├── cultures/
│   ├── ugarit/
│   ├── hatti/
│   ├── egypt/
│   ├── alashiya/
│   ├── canaan/
│   ├── babylonia/
│   ├── assyria/
│   ├── mitanni/
│   └── mycenaean/
├── roles/
├── institutions/
└── cross-cultural/
```

Every important historical parameter should preserve value/distribution, geography, date range, social scope, evidence grade A–D, source IDs, competing models, confidence notes, and review date.

---

# 7. Character architecture

A persistent named person is a structured entity, not a giant prose biography.

## 7.1 Identity/body
Age, health, injuries, disability, nutrition, reproductive history, place of birth, and migration history.

## 7.2 Social identity
Household, lineage, settlement, language proficiency, legal status, political allegiance, cult affiliations, occupations, patrons, dependents, status dimensions, and perceived foreignness.

## 7.3 Material position
Land, herds, food, tools, workshops, metal, prestige goods, debt, credit, property claims, transport, weapons, and literacy access.

## 7.4 Persistent dispositions
Individual variation such as risk tolerance, future orientation, reciprocity sensitivity, status sensitivity, aggression threshold, forgiveness, sociability, novelty seeking, mobility comfort, deference, entrepreneurial tendency, ritual commitment, omen sensitivity, family loyalty, localism/cosmopolitanism, empathy, and envy.

Do not overfit these into rigid psychometrics. They are priors and explanatory state.

## 7.5 Beliefs
Cosmology, gods/ancestors, ritual obligations, trusted specialists, taboos, illness explanations, political legitimacy, remembered omens, rumors, and confidence.

## 7.6 Goals
Immediate survival/dependent care; medium-term harvest, debt, marriage, work, service, disputes; long-term household continuity, children, status, land, office, freedom, reputation, lineage legacy, migration/return.

Goals should conflict.

---

# 8. Households are first-class agents

Households store members, kin structure, headship, property rules, marriage strategy, inheritance, care expectations, workforce, dependents, bound labor, land, herds, food, workshops, debts, creditors, patrons, ritual obligations, neighbors, water access, food security, prestige, and political obligations.

Households make collective decisions while allowing internal disagreement.

Examples:

- marriage;
- migration;
- borrowing;
- selling livestock;
- hiding property;
- elder care;
- apprenticeship;
- inheritance;
- sheltering migrants;
- redeeming dependent kin.

---

# 9. Relationship ledger

Relationships should be causal.

For every meaningful directed relationship preserve:

```text
relationship_type
kin_degree
affection
trust
fear
respect
status_difference
favors_given
favors_owed
property_ties
ritual_ties
shared_work
conflicts
shared_secrets
marriage_links
patronage
last_contact
important_shared_events
```

Avoid one generic friendship score. A person may love but distrust a sibling, fear and respect a patron, dislike but owe a merchant, or resent a parent while remaining dutiful.

---

# 10. Reputation, gossip, reciprocity, and social pressure

Reputations are propositions circulating through networks: generous, reliable, oath-breaker, brave, skilled, corrupt, unlucky, favored by a god, neglectful child, dangerous debtor, honorable foreigner, and so on.

Different networks can believe different things about the same person.

Gifts and favors create culturally scaled expectations: famine aid, marriage gifts, testimony, herd access, military support, funeral attendance, elder care, caravan capital, ritual service, diplomatic gifts.

Represent norms as expected behavior + enforcement probability + sanction type + internalization + audience + status applicability.

Potential sanctions include gossip, ridicule, marriage damage, credit refusal, refusal of aid, compensation, exclusion, patron withdrawal, courts, divine fear, and violence.

Agents may violate norms when other pressures dominate.

---

# 11. Knowledge and epistemic containment

Distinguish:

1. canonical world truth;
2. what a person knows;
3. what a person believes;
4. what a person heard;
5. what a person misremembers;
6. what a person suspects;
7. what a person cannot know.

## 11.1 Database, not lifetime prompt

Use SQLite for persistent knowledge. Text is the current working-memory packet.

## 11.2 Knowledge records

Store character, proposition, learned time, source, transmission chain, direct/hearsay/inference, confidence, secrecy, supersession, and optional canonical-fact link.

## 11.3 Memory types

- episodic;
- semantic;
- social;
- institutional;
- cultural;
- rumor;
- autobiographical summary.

## 11.4 Context compiler

When ChatGPT inhabits a character, retrieve only relevant admissible memory.

Start with **SQLite structured query + FTS5 + recency + salience + relationship relevance**.

Do not begin with a vector DB. Add embeddings only if retrieval quality proves inadequate.

## 11.5 Knowledge firewall

ChatGPT should not receive unrestricted DB access while inhabiting an agent.

A character-scoped cognition packet should contain only their current scene, material state, roles, cultural expectations, relevant traits, relationships, memories, beliefs, rumors, and known information.

Every consequential response should identify which knowledge/beliefs it relied upon. Validate those IDs against the packet. Reject/regenerate leaked decisions.

## 11.6 Internet containment

Web research occurs in explicit research/calibration work. Do **not** browse the web while ChatGPT is inhabiting an in-world character.

## 11.7 Future-history leakage

The base model may know later history. Mitigate with packet-only reasoning, reason validation, explicit prohibition on future historical facts, simulation-specific divergence, and optional blind identifiers for sensitive experiments.

Do not overengineer cryptographic isolation in V1.

---

# 12. Memory dynamics

Characters should change.

Store memory salience: emotional weight, recency, relationship relevance, goal relevance, rehearsal, identity significance, trauma/significance.

Canonical event truth remains immutable; personal interpretation can diverge.

Do not delete history when characters forget. Reduce retrieval probability.

After major experiences or bounded intervals, allow derived reflection:

> After losing a caravan, Pidus became more cautious about maritime credit and more focused on household grain security.

Store reflection as derived state with provenance.

Households transmit stories about famines, feuds, migrations, betrayals, generosity, cult obligations, property claims, and ancestors. Children inherit stories, not perfect logs.

---

# 13. Cognition model

ChatGPT is the cognitive/social reasoning engine. Optiplex decides **when cognition is necessary**.

Routine field work, eating, sleeping, aging, and predictable movement do not require ChatGPT.

Escalate to cognition when goals conflict, relationships are at stake, norms may be violated, negotiation occurs, information is ambiguous, cross-cultural/religious interpretation matters, or decisions have consequential stakes.

Use cognitive tiers:

- Tier 0: statistical/background population;
- Tier 1: persistent household;
- Tier 2: named persistent character;
- Tier 3: focus character receiving full ChatGPT cognition.

People can be promoted when history touches them.

---

# 14. Scene engine

The primary AI unit is the **scene**.

A scene has time/place, participants, per-participant knowledge views, trigger, stakes, available institutions, material constraints, social constraints, goals, resolution, consequences, and optional dialogue artifact.

Scene families:

- household: marriage, inheritance, elder care, divorce, food allocation, migration;
- economic: loans, partnerships, prices, debt collection, failed shipments;
- legal: property, compensation, testimony, theft, mediation;
- religious: divination, illness, omens, purification, festivals;
- political: tribute, tax, office, succession, factions, levy;
- diplomatic: gifts, envoys, marriage diplomacy, military assistance, treaties;
- cross-cultural: translation, foreign ritual, intermarriage, migrant integration, merchant disputes;
- crisis: crop failure, epidemic, raids, storms, refugees, requisition, revolt, archive destruction.

---

# 15. Multi-agent interaction workflow

For important scenes, do not have an omniscient narrator simply choose the outcome.

Example marriage negotiation:

1. compile Household A;
2. compile Character A view;
3. compile Household B;
4. compile Character B view;
5. reason separately from each perspective;
6. produce proposal;
7. pass only communicated content to counterpart;
8. generate response;
9. repeat bounded exchanges;
10. apply explicit agreement/actions;
11. update property, obligations, relationships, reputation, and memories.

For councils, generate private positions first where useful, then public contributions under locally appropriate speaking/authority rules.

---

# 16. Material world simulation

AI decisions need a reality they cannot talk around.

Optiplex owns:

- time/calendar/season;
- agriculture;
- herds;
- food/storage;
- craft production;
- bronze/metal supply and recycling;
- trade/ships/caravans;
- property/debt;
- health/disease at appropriate abstraction;
- travel;
- military logistics;
- physical destruction.

The system should model logistics before tactical battle detail.

---

# 17. Religion as a decision system

Religion cannot be decorative.

An agent under uncertainty may classify a problem as practical/social/supernatural/mixed, choose a trusted specialist, perform ritual/divination, receive an interpreted result, update beliefs, and act.

Ritual consumes time/resources and may coordinate groups.

Characters can disagree about gods, ritual correctness, specialist trustworthiness, omens, and whether practical action should accompany ritual.

---

# 18. Language and translation

Use clear modern English for display, not fake archaic English.

Model graded proficiency: native, fluent, functional, limited, formulaic, none.

Interpreters should become important brokers.

Writing access depends on region, institution, profession, status, script, and training. A person may dictate without being literate.

Misunderstanding becomes more likely under low proficiency, concept mismatch, long oral transmission, political incentives, and weak memory.

---

# 19. Information network

Messages are simulation objects with originator, actual content, language, sender intent, messenger, route, departure, arrival estimate, interception, recipient, received content, distortion, and secrecy.

News travels through messengers, merchants, sailors, soldiers, migrants, relatives, and officials.

This enables stale information, rumor cascades, asymmetric knowledge, brokerage, deception, and diplomatic misunderstanding.

---

# 20. Cross-cultural interaction as a first-class system

Important channels:

- trade;
- ports;
- caravans;
- diplomatic missions;
- dynastic marriage;
- mercenary service;
- conquest/vassalage;
- hostages;
- migration/refugees;
- craft apprenticeship;
- religious borrowing;
- mixed households;
- interpreters;
- captives.

Do not use generic `cultural_influence += 1`. Cultural change should happen through people and relationships.

---

# 21. Personality does not equal random flavor

Personality should matter when incentives conflict.

Decision packets should surface relevant tensions such as survival, household welfare, status/reputation, reciprocity, ritual security, material gain, autonomy, affection, legal risk, supernatural risk, social shame, and retaliation risk.

Do not turn this into a rigid utility maximizer. Use it to frame what matters to the person.

---

# 22. Randomness

RNG creates circumstances: rainfall, storms, accidents, biological uncertainty, disease transmission, some combat outcomes, conception/birth uncertainty, ambiguous divination, minor encounter timing.

RNG should not decide social destiny through arbitrary “betrayal chance,” “marriage failure chance,” or “collapse probability.”

---

# 23. Persistence, canonical state, and database design

Use SQLite initially and make it the **single authoritative persistent state**.

Do not allow a second canonical history to emerge in `events.jsonl`, Markdown chronicles, observer pages, summaries, or `state/current.json`. Those are derived exports/views of the database.

## 23.1 Current state plus append-only event history

Do not build a complicated pure event-sourcing architecture.

Use:

- ordinary current-state tables for fast simulation;
- append-only structured event records;
- atomic transactions that update current state and append the corresponding event together;
- periodic snapshots for recovery, inspection, and branching.

Every consequential event should preserve, where applicable:

```text
event_id
run_id
time
scene_id
decision_id
actor_ids
causing_event_ids
knowledge_or_belief_ids
model_rule_or_assumption_ids
material_deltas
relationship_deltas
institutional_deltas
```

This causal spine is what later makes questions such as “why did this happen?” answerable from actual history rather than reconstructed narrative.

## 23.2 Suggested V1 domains

Start with only the domains needed by the first executable social slice:

```text
runs
scenarios
persons
character_traits
households
household_memberships
relationships
relationship_events
places
routes
institutions
roles
properties
resource_stocks
debts
obligations
contracts
marriages
kinship_edges
patronage_edges
beliefs
knowledge
memories
reputations
rumors
messages
scenes
scene_participants
cognition_jobs
decisions
actions
events
historical_claims
model_assumptions
research_sources
evidence_links
simulation_versions
```

Do not create every conceivable normalized table before it is needed. Stable high-value concepts should be normalized. Unstable experimental attributes may temporarily use versioned structured JSON fields until their shape stabilizes.

Every material change should still become a structured event: transfer, marriage, debt, default, birth, death, injury, migration, message, property transfer, favor, ritual, office, levy, household split, etc.

## 23.3 Branchable and reproducible runs

Every run should preserve:

```text
run_id
parent_run_id (optional)
parent_snapshot_or_event (optional)
scenario_version
evidence_model_version
simulation_code_version
rng_seed
cognition_protocol_version
schema_version
created_at
```

A branch means: restore a recorded snapshot/state boundary, create a new `run_id`, change a declared assumption/input/decision, and continue. Do not build a special database-branching subsystem.

Replay must reuse recorded validated cognition decisions rather than silently re-querying ChatGPT. A separate explicit **re-reason** experiment may request new cognition, but that creates a new run.

---

# 24. Recommended technical stack

Keep V1 boring and reliable.

- **Python 3.12** core.
- **SQLite** persistence with FTS5 and migrations.
- **FastAPI** or similarly minimal HTTP layer only when a durable observer service is useful.
- simple browser observer, adding TypeScript only where useful.
- `pytest` tests.
- Pydantic/dataclasses for schemas.
- project-local CLI for simulation control and cognition-job exchange.

Do not begin with Postgres, distributed agents, Kafka, Kubernetes, vector DB, graph DB, local LLM orchestration, generic agent frameworks, or microservices.

The outside research reviewed for this revision strengthens the need for transparent model specification, reproducibility, and longitudinal LLM-agent evaluation. It does **not** justify changing this stack.

## 24.1 Canonical repository layout

```text
bronze-age-living-world/
├── START_HERE.md
├── STATUS.md
├── NEXT_SESSION.md
├── README.md
├── plan.md
├── bronze-age-simulation-encyclopedia.md
├── docs/
│   ├── MODEL_SPEC.md
│   ├── HISTORICAL_FIDELITY.md
│   ├── COGNITION_PROTOCOL.md
│   └── EVIDENCE_MODEL.md
├── research/
│   ├── evidence-index/
│   ├── cultures/
│   ├── roles/
│   ├── institutions/
│   ├── situations/
│   └── cross-cultural/
├── src/bronze_world/
├── scenarios/ugarit_1350/
├── state/
├── runs/
├── snapshots/
├── chronicles/
├── artifacts/
├── history/
├── tests/
└── pyproject.toml
```

`history/` may contain JSONL/event exports for inspection, but SQLite remains canonical. `state/`, chronicles, and observer artifacts must likewise be generated from canonical state or carry explicit derived-state status.

---

# 25. Evidence-to-model architecture

The encyclopedia already requires dated, geographic, socially scoped evidence with explicit uncertainty. Make that requirement executable rather than documentary.

## 25.1 Separate six layers

Represent separately:

1. `research_source`
2. `historical_claim`
3. `model_assumption`
4. `model_parameter_or_rule`
5. `scenario_value`
6. `runtime_sample`

A source supports a claim.

A claim may permit multiple competing modeling assumptions.

A scenario explicitly chooses or weights those assumptions.

A run samples concrete values from that scenario.

Never silently convert scholarly uncertainty into code.

## 25.2 Three different kinds of uncertainty

Never collapse these into one generic confidence variable.

### Historical/model uncertainty

What modern researchers do not know.

Example: the exact institutional form or prevalence of a practice.

### In-world epistemic uncertainty

What a specific simulated person does not know.

Example: whether a ship survived its voyage.

### Runtime stochastic uncertainty

What outcome has not yet been sampled by the simulation.

Example: whether a storm strikes the ship.

## 25.3 Model specification

Create `docs/MODEL_SPEC.md` using a lightweight ODD-inspired structure:

- purpose and research questions;
- entities;
- state variables;
- temporal and spatial scales;
- process scheduling;
- interaction rules;
- institutions;
- cognition escalation;
- stochastic processes;
- initialization;
- external inputs;
- submodels;
- observations/evaluation targets.

Include an explicit mapping:

> `source → claim → interpretation/assumption → parameter/rule → code → test → observable`

This is a transparency discipline, not a reason to adopt an external ABM framework.

---

# 26. Spatial and institutional substrate

The encyclopedia repeatedly makes geography, information delay, uneven state reach, ecological windows, and institutional access causal. Therefore a minimal spatial/institutional layer belongs in the first executable world rather than a later geopolitical phase.

## 26.1 Place graph

Use a simple graph, not GIS.

Potential V1 places:

- household;
- street/neighborhood;
- field;
- village;
- market;
- harbor;
- workshop;
- shrine/temple;
- palace/administrative office;
- adjudication/meeting location.

Routes preserve approximate travel time, mode, accessibility, seasonality, and disruption.

This constrains:

- who can meet;
- who can observe an event;
- work attendance;
- trade;
- state/institutional reach;
- ritual attendance;
- migration;
- message delay.

## 26.2 Institutions

A minimal institution should carry only what scenes need:

```text
type
location_or_jurisdiction
members_and_office_holders
resources
procedures
obligations
authority
available_sanctions
access_rules
effective_spatial_reach
```

Do not model an entire Ugaritic state before ordinary people need it. Build the institutions the first population actually encounters.

---

# 27. ChatGPT and Optiplex responsibilities

## ChatGPT

- research synthesis;
- cultural/role/situation dossier creation;
- historically constrained cognition;
- scene decisions;
- negotiation and dialogue where useful;
- reflection;
- social interpretation;
- diagnosing weird behavior;
- deciding which research gap matters next;
- generating chronicles/digests from canonical history;
- implementation/development through MCP.

ChatGPT is **not** the authoritative database, scheduler, transaction processor, or hidden source of world facts.

## Optiplex software

- canonical world state;
- database;
- run provenance;
- time/environment/resources;
- travel/economy/demography;
- scene detection;
- cognition-job creation;
- action validation;
- event application;
- memory storage;
- knowledge provenance;
- context compilation;
- tests;
- observer UI;
- persistence/replay/branching;
- historical research provenance.

## 27.1 Pull-based cognition boundary

Do not assume Optiplex can autonomously summon the active ChatGPT conversation.

The engine advances deterministic/routine processes until it encounters consequential situations. It then stores structured `cognition_job` records.

During a simulation session, ChatGPT:

1. requests pending cognition jobs through the project workflow;
2. receives bounded character-scoped packets;
3. reasons only from those packets and declared project rules;
4. submits structured proposed decisions/actions;
5. asks the engine to validate/apply them;
6. continues to a bounded scene/session budget.

No dedicated model API, local LLM orchestrator, agent framework, or permanent MCP expansion is required for V1.

---

# 28. Structured cognition and action protocol

A cognition packet should contain only information admissible and useful for the current decision:

- scene/time/place;
- actor identity and current body/state;
- household situation;
- social/status/legal position;
- relevant roles and institutions;
- goals and active tensions;
- persistent dispositions relevant to the decision;
- material resources and constraints;
- relevant relationships;
- admissible memories;
- admissible knowledge/beliefs/rumors;
- ritual/religious considerations;
- known norms and probable sanctions;
- language/communication constraints;
- available structured actions or affordances.

The response envelope should contain roughly:

```text
decision_id
actor_id
selected_intent
proposed_actions[]
optional_communicated_content
decisive_knowledge_or_belief_ids[]
concise_decision_basis_tags_or_summary
declared_uncertainty
```

Do **not** require hidden chain-of-thought.

Do not force citations for every emotion or preference. Require IDs for decisive factual premises when provenance matters.

## 28.1 Action grammar

The LLM cannot invent arbitrary state transitions.

Actions are typed simulation operations such as:

- transfer resource;
- offer/request favor;
- communicate proposition;
- travel;
- accept/refuse proposal;
- enter/modify obligation;
- borrow/lend;
- marry/divorce where available;
- seek mediation/adjudication;
- perform ritual/divination;
- work/assign labor;
- conceal/disclose information;
- migrate/shelter;
- appoint/remove where authority exists.

The grammar expands only when a real scene requires a new reusable action family.

## 28.2 Validation

Before an action becomes canonical, the engine checks as applicable:

- actor is alive, available, and physically capable;
- location/reachability;
- time cost;
- resource ownership/control;
- material conservation;
- contractual/debt consistency;
- institutional/legal availability;
- role/status authority;
- required information actually known by the actor;
- language/communication feasibility;
- household/property restrictions;
- target validity;
- action-specific preconditions.

Rejected actions may be returned for a bounded correction attempt.

Only validated actions create canonical events.

---

# 29. Character change and long-horizon coherence

Characters should evolve, but not reset or drift arbitrarily.

Separate roughly three time horizons.

## Durable identity

Examples:

- basic dispositions;
- formative loyalties;
- deeply established ritual commitments;
- long-term aspirations;
- identity-defining relationships.

These can change, but substantial change requires accumulated causal history.

## Medium-term adaptation

Examples:

- trust changes;
- financial caution;
- resentment;
- fear;
- patron loyalty;
- migration ambition;
- changing ritual dependence.

## Short-term state

Examples:

- hunger;
- fatigue;
- anger;
- grief;
- acute fear;
- immediate ritual anxiety.

Derived reflections must point back to canonical experiences. They may reinterpret history but cannot invent new historical events.

Permanent longitudinal evaluation should detect:

- unexplained personality reversal;
- relationship resets;
- forgotten durable obligations;
- unsupported religious conversion/reversal;
- agents converging toward one generic voice/personality;
- role/status amnesia.

---

# 30. Research workstream

Deep historical research remains a required implementation workstream, but make it **demand-driven**.

Do not finish exhaustive dossiers for every connected civilization before the first people live.

For the first executable slice, deeply research only what active mechanics require:

- Ugaritic household life;
- 6–10 core social positions;
- 3–5 institutions;
- property/debt/obligations;
- seasonal labor and subsistence;
- religion/divination;
- reputation/reciprocity/patronage;
- language/information;
- status/dependence;
- modest foreign contact.

Other regions initially receive **interface dossiers** containing only the facts required by actual contacts. Deepen them when contact becomes persistent.

## 30.1 Behavioral-situation library

Replace “20 role cards” as the primary research gate with a more useful test corpus of approximately 30–50 historically grounded situations.

Examples:

- loan request after poor harvest;
- marriage negotiation;
- inheritance challenge;
- elder-care dispute;
- favor not reciprocated;
- foreign merchant credit problem;
- uncertain illness and ritual response;
- interpreter caught between parties;
- official requisition during a labor bottleneck;
- contradictory shipping news;
- dependent worker seeking patron protection;
- household argument over migration;
- contested property claim;
- feast invitation with status implications;
- rumor about war or a missing shipment.

Each situation records:

```text
historical_basis
place_and_date_scope
social_scope
evidence_grade
uncertainty
participants_and_interests
relevant_norms_and_institutions
plausible_action_space
known_failure_or_stereotype_traps
```

These artifacts become both historical research outputs and cognition benchmarks.

---

# 31. Simulation session workflow

Fresh ChatGPT session:

1. project preflight;
2. read `START_HERE.md`;
3. read `NEXT_SESSION.md`;
4. read `state/current.json` if present;
5. read `STATUS.md`;
6. read latest chronicle/session summary when useful;
7. verify DB/runtime/run manifest;
8. identify pending cognition jobs and research gaps;
9. resume from repository/live authority.

Repository/live state overrides old chat memory.

Simulation loop:

1. advance routine/background world deterministically;
2. detect consequential situations;
3. rank scene importance;
4. enqueue cognition jobs;
5. compile character-scoped packets;
6. perform ChatGPT cognition for a bounded batch;
7. validate proposed actions and factual premises;
8. apply accepted consequences transactionally;
9. propagate memories/messages/reputations/secondary scenes;
10. continue to the session scene budget;
11. checkpoint canonical state and run provenance.

Early sessions should use consequential scene count rather than huge fictional time jumps.

Periodically audit some scenes that were **not** escalated to ChatGPT to ensure the scheduler is not suppressing consequential social behavior.

---

# 32. End-of-session artifacts

Every material simulation/development session should leave an exact resumable state.

Simulation sessions should produce, as appropriate:

- canonical DB update;
- run/version manifest;
- readable chronicle derived from events;
- 3–8 lives worth following once the population is large enough;
- important relationship changes;
- rumor-vs-truth cases;
- material pulse;
- institutional pulse;
- cross-cultural encounters when active;
- surprises/emergent behavior;
- historical/model uncertainty notes;
- cognition/validation anomalies;
- exact continuation state.

Chronicles and summaries are generated views, never canonical state.

---

# 33. Observer experience

Do **not** make a polished observer UI a prerequisite for proving the social simulation.

During early phases, a CLI plus Markdown/JSON causal traces and compact debug pages are sufficient.

After the first living-world proof, build a read-oriented observer with:

- current date;
- timeline/events;
- important characters;
- households;
- places/journeys;
- stressed households/resources;
- rumors and information paths;
- births/deaths/marriages;
- institutions;
- chronicle;
- causal “why?” traces.

Character pages should expose life history, household, role, possessions, relationships, beliefs, memories, goals, scenes, messages, and timeline.

Household pages should expose genealogy, property, obligations, internal tensions, marriage ties, patrons, debt, status, and transmitted stories.

Later add relationship exploration and simulated archives for letters, contracts, court records, merchant ledgers, diplomatic correspondence, and divination records. Clearly label them as **simulated artifacts**, never historical documents.

---

# 34. Revised implementation phases

The central sequencing change is deliberate: **prove a tiny end-to-end living society before building broad horizontal kernels or scaling population/geopolitics.**

## Phase 0 — Authority, experiment contract, and reproducibility

Create repository and preserve `plan.md` plus `bronze-age-simulation-encyclopedia.md` as supplied authority documents.

Create:

- `START_HERE.md`;
- `STATUS.md`;
- `NEXT_SESSION.md`;
- `docs/MODEL_SPEC.md`;
- `docs/HISTORICAL_FIDELITY.md`;
- `docs/COGNITION_PROTOCOL.md`;
- `docs/EVIDENCE_MODEL.md`.

Implement the minimal run/scenario/version manifest and define canonical-versus-derived data.

**Gate:**

- a fresh session can correctly explain project authority, purpose, safeguards, cognition boundary, evidence doctrine, canonical-state rules, and next step;
- a trivial seeded non-LLM fixture run can be exactly replayed.

## Phase 1 — Ugarit evidence-to-model kernel

Deepen only the research required by the first executable slice.

Create:

- initial Ugaritic core-role/social-position cards;
- first institutional cards;
- seasonal/ecological constraints;
- first property/debt/obligation rules;
- first ritual/belief rules;
- first information/language rules;
- behavioral-situation library;
- evidence-to-model mappings.

Create narrower interface dossiers for foreign contacts only where the first slice requires them.

**Gate:** every active historically specific rule is traceable to evidence, an explicitly labeled modeling assumption, or a declared uncertainty distribution/model choice. No high-impact Grade-D proposition silently becomes a default.

## Phase 2 — Canonical state, place graph, and invariants

Implement the minimal database plus current-state/event transaction pattern.

Implement:

- people;
- households;
- relationships;
- places/routes;
- minimal institutions;
- roles;
- resources/property;
- obligations/debt;
- events/actions;
- run provenance.

Add deterministic fixture populations and invariants:

- no impossible negative resources;
- balanced/conserved transfers where appropriate;
- valid ownership/control;
- debt counterpart consistency;
- valid household membership;
- valid relationship/kin targets;
- monotonic time;
- no action by dead/unavailable agents;
- travel consumes time;
- messages cannot arrive before departure;
- state update plus event append is atomic.

**Gate:** a fixture world executes and exactly replays several weeks of routine non-LLM history.

## Phase 3 — Micro social/material world

Create approximately **6–10 households with roughly 12–20 important named people**.

Model only enough material/social reality for choices to have consequences:

- seasonal calendar;
- labor;
- food/storage;
- basic property;
- debts/obligations;
- household needs;
- occupations;
- basic ritual costs;
- reputation;
- favors;
- household disagreement;
- minimal institutional obligations.

### Research-driven ordinary-life realism substrate

Before adding more isolated event templates, make ordinary Ugaritic life generate situations from recurring systems. The simulation should treat the following as the Phase-3 realism priority, because the encyclopedia repeatedly identifies household organization, multiplex labor, seasonal ecology, reciprocity, ritual obligation, slow information, and mixed household/palace/market exchange as the structures that make Bronze Age choices consequential.

1. **Seasonal labor calendar.** Give the Ugaritic micro-world an explicit, evidence-labeled Mediterranean agricultural cycle. Exact day alignment and fixture quantities remain modeling assumptions, but work priorities must change across cereal harvest/threshing, dry-season storage/vine work, grape/olive and field preparation, sowing/early rains, winter maintenance, and spring weeding/livestock work. Ecological bottlenecks should change the cost of outside work, corvée, travel, illness, and household labor loss.
2. **Occupation workflows, not job labels.** Every important role should generate recurring work, dependencies, and failure modes. Farmers need labor/field access; textile workers require fiber and produce labor-intensive goods; metalworkers require metal/fuel and can recycle; merchants depend on credit, partners, weights, routes, and information; sailors depend on vessels, crews, weather, cargo, and harbor news; scribes/interpreters mediate records, contracts, correspondence, and languages; ritual/healing specialists depend on trust, offerings, ingredients, and correct procedure.
3. **Household labor allocation.** Treat the household as the primary production, care, property, ritual, and reputation unit. Multiple roles compete for the same people. Outside work, illness, dependent care, palace labor, craft quotas, harvest, and travel should therefore create opportunity costs rather than independent events.
4. **Reciprocity/reputation/patronage propagation.** Resource aid, water access, work help, testimony, introductions, ritual service, feast participation, and credit accommodation must leave remembered social balances that can affect later willingness to help, terms of exchange, mediation, and household strategy.
5. **Recurring household and communal religion.** Religion is not restricted to illness scenes. Household observance, seasonal rites, offerings, feast/festival participation, specialist consultation, dreams/omens, birth/health/crop/livestock concerns, and disagreement over ritual interpretation/cost should compete with practical responses and consume real fixture resources.
6. **Port/market activity as a recurring system.** Ugarit should continuously produce harbor work, cargo handling, market exchange, accounting, credit, information brokerage, visiting contacts, and delayed reports. Trade opportunities should emerge from actual merchant/sailor/scribe relationships and material/information state rather than a generic market score.
7. **Institutional extraction as an opportunity cost.** Palace/estate labor and resource requests should intersect with seasonal household work. State reach is not automatic: requests can be complied with, negotiated, delayed, evaded, mediated, or remembered as burdens depending on actor status and available institutions.
8. **Dispute ladders.** Reusable conflicts over water, work, debt, property, damaged goods, animals, inheritance, and reputation should move through private negotiation, kin/patron mediation, compensation, ritual/oath mechanisms, or officials as locally supported. Do not spawn a modern court for every disagreement.

Implementation order for this substrate:

`seasonal calendar → recurring occupation cycles → household labor conflicts → material craft/textile dependencies → household/communal ritual calendar → port/market cycles → institutional labor pressure → reusable dispute/favor consequences`

The engine should escalate only consequential conflicts to ChatGPT. Routine work, ordinary household observance, predictable craft progress, and non-contentious institutional activity remain deterministic canonical simulation.

No full geopolitics.

**Gate:** 30–90 ordinary simulated days run without resource magic, impossible schedules, constant crisis, uniform households, or meaningless occupations—and naturally generate situations that require judgment.

## Phase 4 — Epistemic and memory layer

Add:

- canonical propositions/world truth;
- character knowledge;
- belief;
- hearsay;
- rumor;
- secrecy;
- confidence;
- provenance/transmission;
- messages;
- memory salience;
- retrieval/forgetting;
- derived autobiographical reflections.

Start with SQLite structured query + FTS5 + recency + salience + relationship/goal relevance.

Do not add embeddings unless retrieval failures demonstrate the need.

**Gate:** adversarial tests prove private facts do not leak, information requires a transmission path, delayed/distorted information matters, rumors can diverge from truth, and every character receives only admissible state.

## Phase 5 — Cognition protocol and behavioral benchmark

Implement the pull-based cognition-job workflow, bounded character packets, structured decision envelope, typed action grammar, and validation.

Before scaling the world, run at least **50–100 inspected decisions** drawn from the behavioral-situation library.

Use paired/counterfactual tests such as:

- household obligation present vs removed;
- same personality under different institutions;
- same event with different knowledge;
- same culture with different individual dispositions;
- similar disposition at different status positions;
- religion causally active vs removed;
- patron/favor relationship present vs absent.

Add adversarial tests for:

- modern individualist defaults;
- civilization stereotypes;
- future-history leakage;
- omniscience;
- unsupported factual invention;
- role confusion;
- persona drift;
- relationship discontinuity;
- unexplained religious/goal reversals.

Repeat a subset across several cognition runs to measure instability, but never interpret LLM choice frequency as a historical probability distribution.

**Gate:** ChatGPT produces heterogeneous, socially situated, structurally valid choices; invalid outputs are caught by the engine rather than entering history.

## Phase 6 — First end-to-end living-world proof

Run the complete loop:

> `background simulation → consequential scene → scoped cognition → validation → event application → memory/reputation propagation → later consequence`

Use the micro-world for an ordinary 30–90-day period.

Produce:

- causal traces;
- household histories;
- character biographies;
- relationship changes;
- rumor-vs-truth examples;
- material/institution interactions;
- ordinary-life chronicle.

**Primary acceptance question:**

> Do these people already feel worth following, and can the system explain why consequential events occurred from canonical history?

If no, improve this slice before scaling population or infrastructure.

## Phase 7 — First canonical Ugaritic year

Expand to approximately **20–40 households** with named persistent agents plus lower-resolution background residents.

Add only the life-course/material mechanisms needed for an ordinary year:

- birth/death risk at appropriate abstraction;
- age/life stage;
- marriage;
- household formation/splitting;
- apprenticeship;
- seasonal work;
- property/inheritance;
- recurring ritual calendar;
- ordinary illness/injury;
- ongoing debt;
- migration.

The first year must also demonstrate that the Phase-3 realism substrate scales across the entire calendar rather than merely producing benchmark scenes. Specifically verify:

- agricultural labor intensity changes household decisions by season;
- specialist work visibly depends on inputs, clients, institutional access, and transport;
- textile and craft production does not appear from nowhere;
- household ritual consumes resources and creates remembered obligations/participation;
- communal feasts convert surplus/contribution into status, reciprocity, and memory;
- merchant/sailor/scribe activity creates recurring trade and information chains;
- palace labor/resource extraction sometimes collides with household work and has opportunity costs;
- favors and refusals recur in later decisions rather than disappearing after one scene;
- ordinary conversation/memory disproportionately concerns work, weather, animals, food, family, debt, neighbors, ritual, travel news, property, reputation, and invitations;
- normal society remains stable enough that war/collapse is not required to make biographies interesting.

**Gate:** one ordinary year creates coherent distinct biographies, relationship histories, household strategies, marriage/disputes, debt/favors, reputation changes, religious decisions, social mobility/decline, and believable institutional pressure without needing war or catastrophe to remain interesting.

This is the **first canonical milestone**.

## Phase 8 — Durable observer

Build the persistent observer only after the living-world proof has earned it.

Prioritize timeline, character, household, relationship/knowledge trace, journeys, institutions, material stress, and causal “why?” inspection before visual polish.

## Phase 9 — Ugaritic port and cross-cultural contact

Expand outward through actual contact.

Add persistent lower-resolution agents/nodes from:

- Hatti;
- Alashiya/Cyprus;
- Egypt;
- neighboring Syrian/Canaanite communities.

Add:

- graded language proficiency;
- interpreters;
- foreign legal/status ambiguity;
- maritime routes;
- foreign credit/trade;
- visiting sailors/merchants/envoys;
- migration;
- mixed households where appropriate;
- foreign ritual exposure;
- information from abroad.

Build the port as interacting occupational and institutional workflows, not merely foreign-agent presence:

- vessel preparation, loading/unloading, storage, porter labor, and seasonal sailing constraints;
- cargo ownership/control, merchant capital, credit, weighed-metal payment, seals/records, and trusted counterparties;
- shipowners/merchants/sailors/porters/market traders/scribes/interpreters with partially overlapping information;
- freight or cargo delay, damaged goods, missing partners, route rumors, customs/administrative demands, and disputed terms;
- multilingual written/oral mediation where language proficiency and literacy matter;
- imported prestige goods versus bulk provisioning as different logistics problems;
- recurring foreign contacts that can become trusted partners, patrons, debtors, marriage links, rivals, or rumor sources;
- explicit trade-network alternatives so one disrupted contact does not automatically collapse commerce.

**Gate:** unscripted trust, misunderstanding, brokerage, mixed partnerships, intermarriage where plausible, borrowing, conflict, patronage, and cultural transmission arise through actual people/relationships—never a generic `cultural_influence += 1` score.

## Phase 10 — Political and international layer

Add:

- royal household;
- palace factions;
- offices;
- tribute;
- vassal obligations;
- diplomatic gifts/parity;
- dynastic marriage;
- military obligations;
- logistics;
- uneven coercive/state reach.

Politics must propagate both directions:

> `ruler/institution → household consequences`

and

> `household/network adaptation → institutional capacity → political constraint`

**Gate:** international decisions are traceable downward into ordinary lives, while accumulated household/network behavior can constrain institutions upward.

## Phase 11 — Multi-year histories and controlled branches

Run 5-, 10-, and eventually 20-year histories.

Use branches to test:

- competing institutional assumptions;
- alternative uncertain priors;
- different environmental sequences;
- explicit user interventions;
- alternative agent decisions.

Track which outcomes are robust versus contingent.

**Gate:** long histories do not suffer personality collapse, relationship resets, runaway wealth, universal famine, institutional immortality, constant drama, or unexplained state discontinuities.

## Phase 12 — Historical stress and transformation

Only after ordinary society works, introduce historically plausible interacting stressors:

- rainfall variation;
- crop failure;
- trade disruption;
- shipping loss;
- political extraction;
- succession disputes;
- warfare/raiding;
- migration;
- disease;
- local earthquakes/destruction;
- specialist loss.

Never implement `collapse_probability`.

Some institutions should fail, some adapt, and some communities should continue through political breakdown.

## Phase 13 — Archaeological residue and research-grade comparison

Generate consequences visible to later researchers:

- settlement change;
- household inequality;
- storage patterns;
- burial patterns;
- mobility signatures;
- diet;
- craft debris/specialization;
- trade-good distribution;
- destruction/abandonment;
- archival production/loss;
- specialist disappearance.

Compare simulated residues against archaeological/textual observables.

Treat equifinality as a central research question: different lived histories may create similar archaeological patterns.

Only here consider repeated parameter inference or techniques such as Approximate Bayesian Computation.

---

# 35. Anthropological and simulation quality gates

Maintain permanent evaluation suites for:

- **diversity of life:** elite woman, farmer, official, foreign merchant, scribe, sailor, priest, migrant, dependent, soldier, artisan when those roles exist in the active world;
- **same culture/different personality:** multiple Ugaritic merchants or farmers should not feel interchangeable;
- **same disposition/different structure:** similar people under different institutions/status constraints should often choose differently;
- **household causality:** changing/removing household obligations alters some decisions;
- **religion causality:** removing religious cognition/ritual authority changes some decisions or schedules;
- **status causality:** ruler, bound worker, merchant, widow, official do not share identical action sets;
- **information causality:** different knowledge changes outcomes;
- **relationship causality:** old favors, betrayals, marriages, care, and patronage change later action;
- **history causality:** old events can matter without living in every prompt;
- **spatial causality:** distance, route, and co-presence affect contact, work, authority, and information;
- **institutional causality:** procedures/access enable, constrain, or prohibit actions;
- **longitudinal coherence:** meaningful personality/trust/belief/goal changes require causal history;
- **cultural contact:** foreign interaction can produce cooperation, misunderstanding, hostility, borrowing, brokerage, and mixed identity;
- **ordinary-life test:** a peaceful decade remains compelling;
- **counterfactual-model test:** changing a major uncertain historical assumption can change outcomes without code changes;
- **archaeological test:** eventually, compelling narratives must also produce plausible residues.

If the simulation is only interesting when disasters occur, the social model is too shallow.

---

# 36. Evaluation without fake precision

Do not assign a single “historical realism score.”

Use:

- structural/invariant tests;
- behavioral fixtures;
- paired counterfactual tests;
- distributional checks;
- source-grounded review;
- adversarial review;
- repeated-run stability checks;
- long-horizon coherence checks;
- human review;
- later archaeological-observable comparison.

Adversarial questions:

- Is this modern behavior in costume?
- Is this a stereotype?
- Is this person omniscient?
- Did the model invent a fact?
- Is archive bias treated as reality?
- Is religion decorative?
- Is class merely a label?
- Are geography and institutional reach actually causal?
- Are ordinary people only reacting to elites rather than generating history themselves?
- Did an LLM-generated sentence bypass structured state validation?
- Did a character change substantially without a causal history?
- Is an uncertain scholarly reconstruction being treated as settled truth?

A simulation that *sounds* realistic can still be structurally or historically wrong. Plausible prose is never itself an acceptance gate.

---

# 37. Self-Building Computer integration

This remains a normal product project first.

Use `Optiplex_MCP` for repository, implementation, tests, services, browser, persistence, Git, and project-local tooling.

Use `Optiplex_Lab` / SBC only for **reusable capability gaps** demonstrated by project evidence.

Possible future gaps:

- character-scoped memory/context compiler;
- simulation behavior auditor;
- social-causality trace summarizer;
- epistemic-leakage auditor;
- long-horizon relationship/persona consistency auditor;
- historical-evidence provenance validator;
- temporal chronicle/replay verifier.

These are hypotheses, not preapproved generations or tooling work.

Decision ladder:

1. Can project code solve it?
2. Does an existing SBC capability solve it?
3. Is the deficiency recurring and generalizable?
4. If yes, use Capability Forge.
5. Promotion only through evidence gates.
6. Do not expand permanent MCP tools.
7. Do not create an SBC generation by cadence.

Evaluate the already-promoted `simulation-behavior-auditor-r1` for reuse before building another behavior auditor.

---

# 38. Keep it wild without overengineering

Do not initially build:

- generic simulation-platform abstractions;
- distributed agent infrastructure;
- Kafka/Kubernetes;
- vector or graph databases;
- dedicated local-model orchestration;
- multiple autonomous AI APIs;
- real-time autonomous cognition;
- thousands of full LLM agents;
- elaborate ontology languages;
- perfect security/cryptographic isolation;
- 3D worlds;
- polished game UI;
- tactical warfare simulation;
- global 3300–1000 BCE simulation;
- formal Bayesian calibration;
- automatic archaeology inference.

Build Python + SQLite + structured models + place/institution graph + scene/cognition jobs + character packets + ChatGPT decisions + typed validated actions + deterministic consequences + simple observer/debugging.

The project succeeds when **interesting people begin doing surprising but understandable things whose consequences remain in the world**.

---

# 39. Research expansion roadmap

After the Ugarit-centered system proves itself:

- **Hittite frontier:** governors, villages, Kaska interaction, tribute/raiding/negotiation;
- **Egypt:** a Deir el-Medina-like deeply documented community, property, work/rations, oracles, family life;
- **Old Assyrian merchant world:** Ashur/Kaneš family firms, tin/textile/silver, caravan credit, diaspora identity;
- **Mycenaean palace:** obligations, textile labor, land, specialists, palace dependence, knowledge loss;
- **Steppe/BMAC contact:** pastoralists, farmers, marriage, horses, crafts, cultural transmission;
- **Shang:** lineages, ancestor politics, oracle divination, campaign/harvest labor conflicts.

Reuse architecture; specialize evidence, institutions, ecology, social pressures, and uncertainty.

---

# 40. Wild experiments enabled later

- blind-history mode;
- counterfactual institutional assumptions;
- archaeologist mode;
- lineage biography mode;
- diaspora mode;
- religion-as-real-decision-authority experiments;
- scribal/knowledge-collapse experiments;
- rumor propagation experiments;
- explicit user interventions labeled experimental;
- alternate-decision branches from the same snapshot;
- re-reason runs using the same admissible packet but a new cognition result.

---

# 41. Milestones

## Milestone A — Living-world gate

> **A small Ugaritic community of roughly 6–10 households can live through an ordinary seasonal period. Its important people occupy different social and material positions, remember what happened, know different things, disagree within households, care about relationships and reputation, take religion seriously without acting identically, work inside material/institutional constraints, and make consequential decisions through ChatGPT. Every consequence is persisted and causally traceable. After 30–90 days, several lives are interesting enough that an observer voluntarily wants to know what happens next.**

If this fails, improve the social world before scaling.

## Milestone B — First canonical year

> **A Ugaritic neighborhood of approximately 20–40 households lives through one ordinary simulated year. Named people have distinct personalities, roles, memories, beliefs, property, relationships and household obligations. ChatGPT resolves consequential scenes. Optiplex persists every validated consequence. At year end, coherent biographies and relationship histories exist that were not prewritten.**

This is the first canonical product milestone.

## Milestone C — Ugaritic port/community

> **A Ugaritic port/community of roughly 50–100 named persistent agents plus background population lives for five years with recurring institutions, merchant networks, foreign visitors, marriage, religion, property, debt, work, gossip, migration, and disputes.**

It should produce at least five storylines worth voluntarily following.

## Milestone D — International anthropological laboratory

> **Ugaritic, Hittite, Egyptian, Cypriot and neighboring Levantine people interact under distinct cultural/institutional constraints, with language, status, information delay, diplomacy, trade and household consequences all active.**

At this point the system becomes the intended international anthropological laboratory.

---

# 42. Definition of “anthropological simulated masterpiece”

The project reaches its intended quality when the user can ask:

> Why does this merchant distrust that official?

And the answer is not a trait score. It is a traceable history of aid withheld, marriage ties, favors, competence, politics, and shared business.

When the user can ask:

> Why didn't the king send troops?

And the answer includes uncertain information, ritual calendar, grain, rival kin, vassal reliability, diplomacy, logistics, remembered failure, and adviser relationships.

When the user can ask:

> Why did this practice spread?

And the answer traces marriages, apprenticeships, migration, patronage, prestige, mixed households, and specific transmission paths.

When the user can ask:

> What caused this institution to fail?

And the answer traces years of household adaptation, debt, specialist loss, mistrust, migration, elite choices, material bottlenecks, and information failure.

When the user can ask:

> Is that explanation historically established or only one plausible model?

And the system can distinguish sources, historical claims, explicit assumptions, run-specific values, and simulated outcomes.

At that point the simulation is not numbers or generated dialogue with Bronze Age labels.

It is a **society with history and inspectable evidence boundaries**.

---

# 43. Immediate implementation instructions for a fresh session

The session receiving this plan and `bronze-age-simulation-encyclopedia.md` should:

1. read both files completely before implementation;
2. inspect `Optiplex_MCP`, the project environment, and relevant SBC state;
3. create `/home/mcp/projects/projects/bronze-age-living-world` as a new Git repository if it does not already exist;
4. preserve these two files as project authority inputs;
5. create `START_HERE.md`, `STATUS.md`, `NEXT_SESSION.md`, and the model/evidence/cognition authority docs from Phase 0;
6. define canonical-vs-derived state and run provenance before building simulation features;
7. turn the encyclopedia into an explicit **demand-driven Ugarit research backlog**;
8. create the first evidence-to-model mappings and behavioral-situation library;
9. implement the minimal schema/place/institution substrate and deterministic fixture world;
10. proceed directly toward the 6–10-household end-to-end living-world gate rather than building the full simulation horizontally;
11. add tests/invariants before the first ChatGPT cognition loop;
12. implement cognition as queued project jobs with character-scoped packets and validated typed actions;
13. keep design project-local unless a genuine reusable SBC capability gap appears;
14. stop/checkpoint only at clean accepted milestones with exact handoff state.

The first implementation sessions should favor **historical traceability, end-to-end social behavior, and anthropological richness**, not feature count or infrastructure breadth.

---

# 44. Fresh-session implementation prompt

```text
You are beginning implementation of Bronze Age Living World.

Primary project:
"/home/mcp/projects/projects/bronze-age-living-world"

I am providing:
1. "plan.md"
2. "bronze-age-simulation-encyclopedia.md"

Read BOTH files completely before implementation. Do not skim or rely on this prompt as a substitute.

Authority:
- The encyclopedia is the primary supplied historical/research foundation.
- plan.md is the implementation/architecture plan.
- Once the repository exists, current repository state, live runtime state, tests, accepted evidence, and explicit project authority files override stale assumptions from this prompt or prior ChatGPT conversations.

Environment:
- Use Optiplex_MCP extensively for normal repository inspection, implementation, tests, services, browser verification, persistence, and Git.
- Use Optiplex_Lab / Self-Building Computer only if a genuine reusable capability gap appears. Check existing SBC capabilities before forging a new one.
- Do not modify the frozen permanent Optiplex_MCP tool surface.
- Do not create a new SBC generation by cadence.

Core architecture:
- ChatGPT is the bounded cognitive/social reasoning engine for consequential scenes.
- Optiplex software is the canonical material/social world, scheduler, validator, persistence layer, and replay authority.
- SQLite is the authoritative state; chronicles/JSONL/current summaries are derived views.
- Cognition is pull-based: the engine queues cognition jobs, ChatGPT receives character-scoped packets, returns typed proposed actions, and the engine validates/applies them.
- Do not introduce a separate model API, generic agent framework, vector DB, graph DB, distributed-agent architecture, or microservices unless demonstrated evidence later requires it.

The project must prioritize:
- deep anthropological and historical grounding;
- explicit source → claim → assumption → rule/parameter provenance;
- heterogeneous individuals rather than civilization stereotypes;
- household, kinship, class, gender, profession, legal status, religion, reputation, reciprocity, patronage, language, migration, and cross-cultural interaction;
- persistent memories and relationships;
- character-scoped knowledge and information provenance;
- consequential AI decisions rather than RNG-driven social destiny;
- explicit separation of historical/model uncertainty, character uncertainty, and runtime stochasticity;
- typed action validation before anything becomes canonical state;
- reproducible/branchable runs with fixed seeds and recorded cognition decisions;
- ordinary emergent life before collapse/crisis;
- simple, robust architecture rather than unnecessary infrastructure.

Do not overengineer containment. Use character-scoped DB retrieval, packet-only cognition, knowledge provenance, action validation, and leakage tests first. Do not use internet research while inhabiting a simulation character; web research belongs only in explicit research/calibration work.

Begin by:
1. inspecting the live environment, Git/project state, and relevant SBC state;
2. preserving any existing work if the repo already exists;
3. establishing Phase 0 authority/model/evidence/cognition documents and run provenance;
4. turning the supplied research into a demand-driven Ugarit backlog;
5. building the first evidence-to-model mappings and behavioral-situation library;
6. implementing the minimum schema, invariants, place graph, institutions, and deterministic fixture needed by the first slice;
7. proceeding vertically toward Milestone A rather than implementing every horizontal subsystem first.

The first serious decision gate is:

A Ugaritic micro-community of roughly 6–10 households and ~12–20 important named people can live through 30–90 ordinary simulated days. People have distinct social/material positions, households, relationships, beliefs, memories, obligations, imperfect information, work and institutional constraints. Consequential scenes are queued for ChatGPT cognition. ChatGPT returns only structured proposed actions from character-scoped knowledge. Optiplex validates and persists every consequence. Several lives become interesting enough to follow, and important outcomes can be explained from canonical causal history.

If that does not work, improve the social/research/cognition model before scaling population, UI, geopolitics, or infrastructure.

Work iteratively, test aggressively, preserve evidence, run adversarial leakage/persona/modernity checks, and leave every material session at a clean resumable checkpoint.
```

---

# 45. Research notes informing the architecture

The supplied encyclopedia remains the historical authority. External simulation/agent research is architectural guidance only.

Useful patterns include:

- **Generative Agents** (Park et al., 2023): stored experiences, dynamic retrieval, reflection, planning, and persistent social behavior — useful inspiration for memory, not historical validation: https://arxiv.org/abs/2304.03442
- Archaeological agent-based modeling commonly treats households as meaningful agents under environmental/social constraints.
- **Rouse & Weeks (2011)** used ABM to investigate specialization/social inequality in Bronze Age southeastern Arabia: https://doi.org/10.1016/j.jas.2011.02.023
- Recent Bronze Age socio-ecological ABM work at Resuloğlu Höyük examines long-run human land use, climate, population, and landscape interaction: https://doi.org/10.1016/j.ecolmodel.2025.111346
- The **ODD** model-description tradition and **ODD+2D** extension are useful for transparent mapping between empirical evidence, model design, assumptions, and reproducibility. Borrow the specification discipline; do not migrate frameworks merely to comply with it: https://jasss.soc.surrey.ac.uk/23/2/7.html
- Recent LLM social-simulation research continues to identify reproducibility, behavioral calibration, long-horizon identity consistency, and validation as material problems. Therefore the project should test persona drift, repeat decisions under controlled conditions, record cognition decisions for replay, and never interpret LLM response frequency as historical prevalence. Example 2026 longitudinal consistency work: https://aclanthology.org/2026.acl-long.1336/

These references provide architectural/testing inspiration. They do **not** override historically specific evidence in `bronze-age-simulation-encyclopedia.md`.

---

# 46. Final operating philosophy

**The world is structured. The people are not scripted.**

The historical evidence provides constraints, practices, institutions, concepts, uncertainty, and social possibilities.

Optiplex provides scarcity, distance, bodies, seasons, property, information, institutions, consequences, persistence, validation, and history.

ChatGPT provides bounded judgment, personality expression, interpretation, negotiation, adaptation, and social intelligence when deterministic/routine logic is insufficient.

The simulation should continually ask:

> Given who this person is, who depends on them, who they love or resent, what they owe, what they believe, what they actually know, what their society and institutions expect, what they possess, where they are, what they fear, and what has happened to them — what do they do now?

Then the proposed action must be possible in the world.

Then the rest of society has to live with the validated consequence.

That is the project.
