PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS marriages (
    marriage_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    person_a_id TEXT NOT NULL REFERENCES persons(person_id),
    person_b_id TEXT NOT NULL REFERENCES persons(person_id),
    start_day INTEGER NOT NULL CHECK(start_day >= 0),
    end_day INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    residence_household_id TEXT REFERENCES households(household_id),
    terms_json TEXT NOT NULL DEFAULT '{}',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    CHECK(person_a_id <> person_b_id),
    CHECK(end_day IS NULL OR end_day >= start_day),
    UNIQUE(run_id, person_a_id, person_b_id, start_day)
);

CREATE TABLE IF NOT EXISTS kinship_edges (
    kinship_edge_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    person_a_id TEXT NOT NULL REFERENCES persons(person_id),
    person_b_id TEXT NOT NULL REFERENCES persons(person_id),
    kinship_type TEXT NOT NULL,
    start_day INTEGER NOT NULL CHECK(start_day >= 0),
    end_day INTEGER,
    provenance_json TEXT NOT NULL DEFAULT '{}',
    CHECK(person_a_id <> person_b_id),
    CHECK(end_day IS NULL OR end_day >= start_day),
    UNIQUE(run_id, person_a_id, person_b_id, kinship_type, start_day)
);

INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', '2');
