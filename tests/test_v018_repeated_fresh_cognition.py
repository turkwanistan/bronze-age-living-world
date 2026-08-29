from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_v018_repeated_same_packet_validation_reproduces(tmp_path: Path, request):
    source = ROOT / 'state' / 'ugarit_living_v015.sqlite'
    property_source = ROOT / 'state' / 'ugarit_living_v014.sqlite'
    attempts = ROOT / 'runs' / 'VALIDATION_V018_REPEATED_FRESH_DECISIONS.json'
    if not source.exists() or not property_source.exists():
        pytest.skip('accepted v014/v015 DB unavailable')
    scratch_root = ROOT / '.pytest-v018-repeated'
    request.addfinalizer(lambda: shutil.rmtree(scratch_root, ignore_errors=True))
    workdir = scratch_root / tmp_path.name
    out = workdir / 'results.json'
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    subprocess.run([
        sys.executable, str(ROOT/'scripts'/'repeated_fresh_cognition_validation.py'),
        '--source-db', str(source), '--property-source-db', str(property_source),
        '--attempts', str(attempts), '--root', str(ROOT), '--workdir', str(workdir/'branches'),
        '--json-out', str(out),
    ], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    data=json.loads(out.read_text())
    assert data['total_attempts']==18
    assert data['packet_count']==6
    assert data['all_checks_pass'] is True
    assert data['checks']['all_18_decisions_valid'] is True
    assert data['checks']['identical_packet_hash_within_each_packet'] is True
    assert data['checks']['p7_control_stronger_than_within_packet_noise'] is True
    assert data['checks']['p3_discordant_reports_remain_epistemically_conservative'] is True
    assert data['variable_action_family_packets']==['p3_shipping_discordant_reports']


def test_v018_frozen_results_match_expected_stability_shape():
    data=json.loads((ROOT/'runs'/'VALIDATION_V018_REPEATED_FRESH_RESULTS.json').read_text())
    assert data['total_attempts']==18 and data['all_checks_pass']
    assert data['packet_summaries']['p10_illness_adequate']['action_family_counts']=={'perform_ritual':3}
    assert data['packet_summaries']['p10_illness_depleted']['action_family_counts']=={'perform_ritual':3}
    assert data['packet_summaries']['p7_recycling_buffered']['action_family_counts']=={'recycle_finished_metalwork':3}
    assert data['packet_summaries']['p7_recycling_near_exhausted']['action_family_counts']=={'wait':3}
    assert data['packet_summaries']['p3_shipping_single_report']['action_family_counts']=={'send_message':3}
    assert data['packet_summaries']['p3_shipping_discordant_reports']['action_family_counts']=={'send_message':1,'wait':2}
