PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', '1');

CREATE TABLE simulation_versions (
    simulation_version_id TEXT PRIMARY KEY,
    code_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    cognition_protocol_version TEXT NOT NULL,
    evidence_model_version TEXT NOT NULL
);

CREATE TABLE scenarios (
    scenario_id TEXT PRIMARY KEY,
    scenario_version TEXT NOT NULL,
    year_bce INTEGER NOT NULL,
    local_period_label TEXT NOT NULL,
    config_json TEXT NOT NULL
);

CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    parent_run_id TEXT REFERENCES runs(run_id),
    parent_snapshot_or_event TEXT,
    scenario_id TEXT NOT NULL REFERENCES scenarios(scenario_id),
    scenario_version TEXT NOT NULL,
    evidence_model_version TEXT NOT NULL,
    simulation_code_version TEXT NOT NULL,
    rng_seed INTEGER NOT NULL,
    cognition_protocol_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    current_day INTEGER NOT NULL DEFAULT 0 CHECK(current_day >= 0),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE TABLE research_sources (
    source_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    locator TEXT,
    sha256 TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE historical_claims (
    claim_id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    geography TEXT,
    date_range TEXT,
    social_scope TEXT,
    evidence_grade TEXT NOT NULL CHECK(evidence_grade IN ('A','B','C','D')),
    uncertainty_note TEXT
);

CREATE TABLE model_assumptions (
    assumption_id TEXT PRIMARY KEY,
    assumption_text TEXT NOT NULL,
    kind TEXT NOT NULL,
    confidence TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE evidence_links (
    evidence_link_id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES research_sources(source_id),
    claim_id TEXT REFERENCES historical_claims(claim_id),
    assumption_id TEXT REFERENCES model_assumptions(assumption_id),
    rule_id TEXT,
    note TEXT
);

CREATE TABLE places (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    place_type TEXT NOT NULL,
    parent_place_id TEXT REFERENCES places(place_id),
    attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    from_place_id TEXT NOT NULL REFERENCES places(place_id),
    to_place_id TEXT NOT NULL REFERENCES places(place_id),
    travel_days INTEGER NOT NULL CHECK(travel_days >= 0),
    mode TEXT NOT NULL,
    accessible INTEGER NOT NULL DEFAULT 1 CHECK(accessible IN (0,1)),
    seasonality_json TEXT NOT NULL DEFAULT '{}',
    disruption_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(from_place_id, to_place_id, mode)
);

CREATE TABLE institutions (
    institution_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    institution_type TEXT NOT NULL,
    place_id TEXT REFERENCES places(place_id),
    jurisdiction_json TEXT NOT NULL DEFAULT '{}',
    procedures_json TEXT NOT NULL DEFAULT '{}',
    obligations_json TEXT NOT NULL DEFAULT '{}',
    authority_json TEXT NOT NULL DEFAULT '{}',
    sanctions_json TEXT NOT NULL DEFAULT '{}',
    access_rules_json TEXT NOT NULL DEFAULT '{}',
    effective_reach_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE households (
    household_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    home_place_id TEXT NOT NULL REFERENCES places(place_id),
    headship_json TEXT NOT NULL DEFAULT '{}',
    property_rule_json TEXT NOT NULL DEFAULT '{}',
    care_expectations_json TEXT NOT NULL DEFAULT '{}',
    ritual_obligations_json TEXT NOT NULL DEFAULT '{}',
    status_json TEXT NOT NULL DEFAULT '{}',
    fixture_daily_food_need REAL NOT NULL CHECK(fixture_daily_food_need >= 0),
    fixture_weekly_receipt REAL NOT NULL DEFAULT 0,
    fixture_notice TEXT NOT NULL
);

CREATE TABLE persons (
    person_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    name_provenance TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 0),
    sex TEXT,
    life_stage TEXT NOT NULL,
    alive INTEGER NOT NULL DEFAULT 1 CHECK(alive IN (0,1)),
    available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1)),
    current_place_id TEXT NOT NULL REFERENCES places(place_id),
    legal_status TEXT NOT NULL,
    status_json TEXT NOT NULL DEFAULT '{}',
    beliefs_json TEXT NOT NULL DEFAULT '{}',
    goals_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE character_traits (
    person_id TEXT NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    trait_name TEXT NOT NULL,
    value REAL NOT NULL CHECK(value >= 0 AND value <= 1),
    provenance TEXT NOT NULL,
    PRIMARY KEY(person_id, trait_name)
);

CREATE TABLE household_memberships (
    household_id TEXT NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
    person_id TEXT NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    membership_role TEXT NOT NULL,
    since_day INTEGER NOT NULL DEFAULT 0,
    until_day INTEGER,
    PRIMARY KEY(household_id, person_id, since_day)
);

CREATE TABLE roles (
    role_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_family TEXT NOT NULL,
    institution_id TEXT REFERENCES institutions(institution_id),
    attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE person_roles (
    person_id TEXT NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    priority INTEGER NOT NULL DEFAULT 1,
    start_day INTEGER NOT NULL DEFAULT 0,
    end_day INTEGER,
    PRIMARY KEY(person_id, role_id, start_day)
);

CREATE TABLE relationships (
    relationship_id TEXT PRIMARY KEY,
    from_person_id TEXT NOT NULL REFERENCES persons(person_id),
    to_person_id TEXT NOT NULL REFERENCES persons(person_id),
    relationship_type TEXT NOT NULL,
    kin_degree TEXT,
    affection REAL NOT NULL DEFAULT 0.5 CHECK(affection BETWEEN 0 AND 1),
    trust REAL NOT NULL DEFAULT 0.5 CHECK(trust BETWEEN 0 AND 1),
    fear REAL NOT NULL DEFAULT 0 CHECK(fear BETWEEN 0 AND 1),
    respect REAL NOT NULL DEFAULT 0.5 CHECK(respect BETWEEN 0 AND 1),
    status_difference REAL NOT NULL DEFAULT 0,
    favors_given REAL NOT NULL DEFAULT 0,
    favors_owed REAL NOT NULL DEFAULT 0,
    conflicts INTEGER NOT NULL DEFAULT 0 CHECK(conflicts >= 0),
    attributes_json TEXT NOT NULL DEFAULT '{}',
    last_contact_day INTEGER,
    UNIQUE(from_person_id, to_person_id)
);

CREATE TABLE resource_stocks (
    household_id TEXT NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),
    unit_label TEXT NOT NULL,
    assumption_id TEXT REFERENCES model_assumptions(assumption_id),
    PRIMARY KEY(household_id, resource_type)
);

CREATE TABLE debts (
    debt_id TEXT PRIMARY KEY,
    debtor_household_id TEXT NOT NULL REFERENCES households(household_id),
    creditor_household_id TEXT NOT NULL REFERENCES households(household_id),
    resource_type TEXT NOT NULL,
    principal REAL NOT NULL CHECK(principal > 0),
    outstanding REAL NOT NULL CHECK(outstanding >= 0),
    due_day INTEGER,
    status TEXT NOT NULL DEFAULT 'open',
    terms_json TEXT NOT NULL DEFAULT '{}',
    CHECK(debtor_household_id <> creditor_household_id)
);

CREATE TABLE obligations (
    obligation_id TEXT PRIMARY KEY,
    obligor_person_id TEXT REFERENCES persons(person_id),
    obligor_household_id TEXT REFERENCES households(household_id),
    beneficiary_person_id TEXT REFERENCES persons(person_id),
    beneficiary_household_id TEXT REFERENCES households(household_id),
    obligation_type TEXT NOT NULL,
    description TEXT NOT NULL,
    due_day INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    provenance_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE propositions (
    proposition_id TEXT PRIMARY KEY,
    canonical_text TEXT NOT NULL,
    truth_status TEXT NOT NULL CHECK(truth_status IN ('true','false','unknown','simulation_contingent')),
    canonical_fact_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE knowledge (
    knowledge_id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    proposition_id TEXT NOT NULL REFERENCES propositions(proposition_id),
    learned_day INTEGER NOT NULL,
    source_kind TEXT NOT NULL,
    source_id TEXT,
    transmission_chain_json TEXT NOT NULL DEFAULT '[]',
    epistemic_mode TEXT NOT NULL CHECK(epistemic_mode IN ('direct','hearsay','inference','belief','rumor')),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    secrecy TEXT NOT NULL DEFAULT 'ordinary',
    superseded_by TEXT REFERENCES knowledge(knowledge_id),
    UNIQUE(person_id, proposition_id, learned_day, source_kind)
);

CREATE TABLE memories (
    memory_id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    memory_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    event_id TEXT,
    created_day INTEGER NOT NULL,
    emotional_weight REAL NOT NULL DEFAULT 0.5 CHECK(emotional_weight BETWEEN 0 AND 1),
    salience REAL NOT NULL DEFAULT 0.5 CHECK(salience BETWEEN 0 AND 1),
    relationship_relevance REAL NOT NULL DEFAULT 0 CHECK(relationship_relevance BETWEEN 0 AND 1),
    goal_relevance REAL NOT NULL DEFAULT 0 CHECK(goal_relevance BETWEEN 0 AND 1),
    provenance_json TEXT NOT NULL DEFAULT '{}'
);

CREATE VIRTUAL TABLE memory_fts USING fts5(memory_id UNINDEXED, person_id UNINDEXED, summary);

CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memory_fts(memory_id, person_id, summary) VALUES (new.memory_id, new.person_id, new.summary);
END;
CREATE TRIGGER memories_ad AFTER DELETE ON memories BEGIN
    DELETE FROM memory_fts WHERE memory_id = old.memory_id;
END;
CREATE TRIGGER memories_au AFTER UPDATE ON memories BEGIN
    DELETE FROM memory_fts WHERE memory_id = old.memory_id;
    INSERT INTO memory_fts(memory_id, person_id, summary) VALUES (new.memory_id, new.person_id, new.summary);
END;

CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    originator_person_id TEXT NOT NULL REFERENCES persons(person_id),
    recipient_person_id TEXT NOT NULL REFERENCES persons(person_id),
    proposition_id TEXT REFERENCES propositions(proposition_id),
    actual_content TEXT NOT NULL,
    received_content TEXT,
    language TEXT NOT NULL,
    sender_intent TEXT,
    messenger_person_id TEXT REFERENCES persons(person_id),
    route_id TEXT REFERENCES routes(route_id),
    departure_day INTEGER NOT NULL,
    arrival_day INTEGER NOT NULL CHECK(arrival_day >= departure_day),
    delivered_day INTEGER CHECK(delivered_day IS NULL OR delivered_day >= departure_day),
    distortion_json TEXT NOT NULL DEFAULT '{}',
    secrecy TEXT NOT NULL DEFAULT 'ordinary'
);

CREATE TABLE scenes (
    scene_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    day INTEGER NOT NULL,
    place_id TEXT NOT NULL REFERENCES places(place_id),
    scene_family TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    stakes_json TEXT NOT NULL DEFAULT '{}',
    material_constraints_json TEXT NOT NULL DEFAULT '{}',
    social_constraints_json TEXT NOT NULL DEFAULT '{}',
    institution_ids_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE scene_participants (
    scene_id TEXT NOT NULL REFERENCES scenes(scene_id) ON DELETE CASCADE,
    person_id TEXT NOT NULL REFERENCES persons(person_id),
    participant_role TEXT NOT NULL,
    PRIMARY KEY(scene_id, person_id)
);

CREATE TABLE cognition_jobs (
    job_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    scene_id TEXT NOT NULL REFERENCES scenes(scene_id),
    actor_person_id TEXT NOT NULL REFERENCES persons(person_id),
    protocol_version TEXT NOT NULL,
    packet_json TEXT NOT NULL,
    packet_hash TEXT NOT NULL,
    allowed_actions_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_day INTEGER NOT NULL,
    correction_attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE decisions (
    decision_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES cognition_jobs(job_id),
    actor_person_id TEXT NOT NULL REFERENCES persons(person_id),
    envelope_json TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    validation_errors_json TEXT NOT NULL DEFAULT '[]',
    submitted_day INTEGER NOT NULL,
    applied_day INTEGER
);

CREATE TABLE actions (
    action_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES decisions(decision_id),
    ordinal INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    validation_error TEXT,
    UNIQUE(decision_id, ordinal)
);

CREATE TABLE events (
    event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    day INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    scene_id TEXT REFERENCES scenes(scene_id),
    decision_id TEXT REFERENCES decisions(decision_id),
    actor_ids_json TEXT NOT NULL DEFAULT '[]',
    causing_event_ids_json TEXT NOT NULL DEFAULT '[]',
    knowledge_or_belief_ids_json TEXT NOT NULL DEFAULT '[]',
    model_rule_or_assumption_ids_json TEXT NOT NULL DEFAULT '[]',
    material_deltas_json TEXT NOT NULL DEFAULT '{}',
    relationship_deltas_json TEXT NOT NULL DEFAULT '{}',
    institutional_deltas_json TEXT NOT NULL DEFAULT '{}',
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE snapshots (
    snapshot_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    day INTEGER NOT NULL,
    event_seq INTEGER,
    state_hash TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_events_run_day ON events(run_id, day, event_seq);
CREATE INDEX idx_knowledge_person ON knowledge(person_id, learned_day);
CREATE INDEX idx_memory_person ON memories(person_id, created_day);
CREATE INDEX idx_jobs_status ON cognition_jobs(run_id, status, created_day);
CREATE INDEX idx_scenes_run_day ON scenes(run_id, day);
CREATE INDEX idx_messages_arrival ON messages(arrival_day, delivered_day);
