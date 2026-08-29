from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_v019_social_repeated_validation_reproduces(tmp_path: Path):
    needed=[ROOT/'state/ugarit_living_v015.sqlite',ROOT/'state/ugarit_living_v014.sqlite',ROOT/'state/ugarit_living_v008.sqlite']
    if not all(p.exists() for p in needed): pytest.skip('accepted source DB unavailable')
    work=ROOT/'.pytest-v019-social'/tmp_path.name; out=work/'results.json'; work.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'
    subprocess.run([sys.executable,str(ROOT/'scripts/social_repeated_fresh_cognition_validation.py'),'--root',str(ROOT),'--workdir',str(work/'branches'),'--attempts',str(ROOT/'runs/VALIDATION_V019_SOCIAL_REPEATED_DECISIONS.json'),'--v015',str(needed[0]),'--v014',str(needed[1]),'--v008',str(needed[2]),'--json-out',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    r=json.loads(out.read_text())
    assert r['total_attempts']==18 and r['packet_count']==6 and r['all_checks_pass']
    assert all(r['checks'].values())


def test_v019_frozen_social_shape():
    r=json.loads((ROOT/'runs/VALIDATION_V019_SOCIAL_REPEATED_RESULTS.json').read_text())
    assert r['all_checks_pass'] and r['total_attempts']==18
    s=r['packet_summaries']
    assert s['p16_care_no_conflict']['action_family_counts']=={'fulfill_kin_care':3}
    assert s['p16_care_recovery_conflict']['action_family_counts']=={'defer_kin_care':3}
    assert s['p16_stewardship_funded']['action_family_counts']=={'accept_property_stewardship':3}
    assert s['p16_stewardship_underfunded']['action_family_counts']=={'decline_property_stewardship':3}
    assert s['p3_workshop_request_abundant']['action_family_counts']=={'transfer_resource':3}
    assert s['p3_workshop_request_last_reserve']['action_family_counts']=={'refuse_proposal':3}
    assert r['checks']['scarce_refusal_strains_but_preserves_relationship']
