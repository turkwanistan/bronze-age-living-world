
def test_fixture_population(world):
    db,_=world
    assert db.scalar("SELECT COUNT(*) FROM households")==8
    assert db.scalar("SELECT COUNT(*) FROM persons")==16
    assert db.scalar("SELECT COUNT(DISTINCT legal_status) FROM persons")>=5
    assert db.scalar("SELECT COUNT(DISTINCT role_family) FROM roles")>=7


def test_fixture_contains_unequal_water_access(world):
    db,_=world
    rows=[r[0] for r in db.all("SELECT status_json FROM households")]
    assert any('private' in r for r in rows)
    assert any('shared' in r for r in rows)


def test_traits_are_individual_not_culture_defaults(world):
    db,_=world
    vals=[r[0] for r in db.all("SELECT value FROM character_traits WHERE trait_name='risk_tolerance' ORDER BY person_id")]
    assert len(vals)>=8
    assert len(set(vals))>=8


def test_private_shipping_information_is_scoped(world):
    db,_=world
    knowers={r[0] for r in db.all("SELECT person_id FROM knowledge WHERE proposition_id='PROP-SHIP-001'")}
    assert knowers=={"P3","P11"}
