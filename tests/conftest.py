from pathlib import Path
import pytest
from bronze_world.db import WorldDB
from bronze_world.fixture import init_fixture

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def world(tmp_path):
    db=WorldDB(tmp_path/"world.sqlite")
    run_id=init_fixture(db,ROOT,1350)
    try: yield db,run_id
    finally: db.close()
