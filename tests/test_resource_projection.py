import json

from bronze_world.engine import WorldEngine


def _shortfall_scene_for(db, rid, household_id):
    return db.one(
        "SELECT * FROM scenes WHERE run_id=? AND trigger_type='household_resource_shortfall' "
        "AND json_extract(stakes_json,'$.current_grain') IS NOT NULL "
        "AND scene_id IN (SELECT scene_id FROM scene_participants sp JOIN household_memberships hm USING(person_id) "
        "WHERE hm.household_id=?) ORDER BY day,scene_id LIMIT 1",
        (rid, household_id),
    )


def test_low_stock_that_bridges_next_receipt_does_not_trigger(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    # At day 5, 1.0 abstract grain units cover days 6 and 7 for H-WIDOW
    # (0.48/day). The configured day-7 receipt of 2.5 then safely covers the
    # remainder of the one-cycle projection horizon through day 12.
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=5 WHERE run_id=?", (rid,))
        con.execute(
            "UPDATE resource_stocks SET amount=1.0 WHERE household_id='H-WIDOW' AND resource_type='grain'"
        )
    projection = eng._project_household_grain_security("H-WIDOW", 5)
    assert projection["next_receipt_day"] == 7
    assert projection["expected_receipt"] == 2.5
    assert projection["first_shortfall_day"] is None
    eng.detect_situations(5)
    assert _shortfall_scene_for(db, rid, "H-WIDOW") is None


def test_projected_shortfall_uses_receipt_amount_and_triggers(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    # The same low stock safely reaches day 7, but an intentionally tiny fixture
    # receipt cannot secure the following days. This proves the detector reasons
    # beyond an absolute threshold and actually uses expected receipt amount.
    with db.transaction() as con:
        con.execute("UPDATE runs SET current_day=5 WHERE run_id=?", (rid,))
        con.execute(
            "UPDATE resource_stocks SET amount=1.0 WHERE household_id='H-WIDOW' AND resource_type='grain'"
        )
        con.execute("UPDATE households SET fixture_weekly_receipt=0.1 WHERE household_id='H-WIDOW'")
    projection = eng._project_household_grain_security("H-WIDOW", 5)
    assert projection["first_shortfall_day"] == 8
    jobs = eng.detect_situations(5)
    assert jobs
    scene = _shortfall_scene_for(db, rid, "H-WIDOW")
    assert scene is not None
    stakes = json.loads(scene["stakes_json"])
    assert stakes["first_shortfall_day"] == 8
    assert stakes["expected_receipt"] == 0.1
    assert stakes["projection_horizon_day"] == 12


def test_projection_is_deterministic_for_same_state(world):
    db, rid = world
    eng = WorldEngine(db, rid)
    a = eng._project_household_grain_security("H-DEPEND", 13)
    b = eng._project_household_grain_security("H-DEPEND", 13)
    assert a == b
