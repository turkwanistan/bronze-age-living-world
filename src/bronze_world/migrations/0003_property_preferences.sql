CREATE TABLE IF NOT EXISTS property_preferences (
    preference_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    household_id TEXT NOT NULL REFERENCES households(household_id),
    holder_person_id TEXT NOT NULL REFERENCES persons(person_id),
    beneficiary_person_id TEXT REFERENCES persons(person_id),
    preference_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    start_day INTEGER NOT NULL,
    end_day INTEGER,
    status TEXT NOT NULL,
    basis_json TEXT NOT NULL DEFAULT '{}',
    provenance_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_property_preferences_run_status ON property_preferences(run_id,status,household_id);

INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', '3');
