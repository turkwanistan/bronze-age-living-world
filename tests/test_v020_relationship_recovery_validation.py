from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_v020_relationship_recovery_validation_reproduces():
    needed=[ROOT/'state/ugarit_living_v015.sqlite',ROOT/'state/ugarit_living_v008.sqlite',ROOT/'state/ugarit_living_v009.sqlite']
    if not all(p.exists() for p in needed): pytest.skip('accepted source DB unavailable')
    scratch=Path(tempfile.mkdtemp(prefix='.v020-recovery-test-',dir=ROOT))
    try:
        out=scratch/'results.json'; env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'
        subprocess.run([
            sys.executable,str(ROOT/'scripts/relationship_recovery_validation.py'),
            '--root',str(ROOT),'--workdir',str(scratch/'branches'),
            '--decisions',str(ROOT/'runs/VALIDATION_V020_RELATIONSHIP_RECOVERY_DECISIONS.json'),
            '--v015',str(needed[0]),'--v008',str(needed[1]),'--v009',str(needed[2]),
            '--json-out',str(out)
        ],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
        r=json.loads(out.read_text())
        assert r['all_checks_pass'] is True
        assert r['compatibility']['recorded_decisions_applied']==157
        assert r['compatibility']['events']==6608
        assert r['unchanged_scarcity']['refusal_memory_present'] is True
        assert r['recovered_capacity']['refusal_memory_present'] is True
        assert all(r['checks'].values())
    finally:
        shutil.rmtree(scratch,ignore_errors=True)


def test_v020_frozen_results_capture_repair_without_erasure():
    r=json.loads((ROOT/'runs/VALIDATION_V020_RELATIONSHIP_RECOVERY_RESULTS.json').read_text())
    assert r['all_checks_pass'] is True
    assert r['unchanged_scarcity']['merchant_metal_after']==pytest.approx(.15)
    assert r['recovered_capacity']['merchant_metal_after']==pytest.approx(.48)
    before=r['canonical_low_cost_repair']['before']['p3_to_p7']
    after=r['canonical_low_cost_repair']['after']['p3_to_p7']
    assert after['trust']>before['trust'] and after['respect']>before['respect']
    assert before['conflicts']==after['conflicts']==1
    assert after['relationship_type']=='exchange_contact'
