from __future__ import annotations

import json
from typing import Any

from .db import WorldDB


def scenario_config(db: WorldDB, run_id: str) -> dict[str, Any]:
    row = db.one(
        "SELECT s.config_json FROM scenarios s JOIN runs r ON r.scenario_id=s.scenario_id "
        "WHERE r.run_id=? AND s.scenario_version=r.scenario_version LIMIT 1",
        (run_id,),
    )
    return json.loads(row[0]) if row else {}


def scenario_has_assumption(db: WorldDB, run_id: str, assumption_id: str) -> bool:
    return assumption_id in set(scenario_config(db, run_id).get("active_assumptions", []))


def effective_household_provisioning(db: WorldDB, run_id: str, household_id: str) -> dict[str, float | str]:
    """Return the neutral fixture provisioning burden for the household's current composition.

    Before ASM-FIXTURE-022, accepted histories use the configured household constants.
    With ASM-FIXTURE-022 active, each living current member carries the neutral per-person
    share implied by their day-0 household. This moves baseline burden/receipt with people
    while keeping the global no-shock provisioning total conserved.
    """
    row = db.one(
        "SELECT fixture_daily_food_need,fixture_weekly_receipt FROM households WHERE household_id=?",
        (household_id,),
    )
    if not row:
        raise KeyError(household_id)
    if not scenario_has_assumption(db, run_id, "ASM-FIXTURE-022"):
        return {
            "daily_need": float(row["fixture_daily_food_need"]),
            "weekly_receipt": float(row["fixture_weekly_receipt"]),
            "mode": "fixed_household_fixture",
        }

    members = db.all(
        "SELECT p.person_id FROM persons p JOIN household_memberships hm USING(person_id) "
        "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 ORDER BY p.person_id",
        (household_id,),
    )
    daily = 0.0
    for member in members:
        origin = db.one(
            "SELECT hm.household_id,h.fixture_daily_food_need,"
            "(SELECT COUNT(*) FROM household_memberships hm2 WHERE hm2.household_id=hm.household_id AND hm2.since_day=0) AS initial_count "
            "FROM household_memberships hm JOIN households h USING(household_id) "
            "WHERE hm.person_id=? AND hm.since_day=0 ORDER BY hm.household_id LIMIT 1",
            (member["person_id"],),
        )
        if not origin or int(origin["initial_count"] or 0) <= 0:
            continue
        daily += float(origin["fixture_daily_food_need"]) / int(origin["initial_count"])
    return {
        "daily_need": daily,
        "weekly_receipt": daily * 7.0,
        "mode": "composition_neutral_per_person_share",
    }
