#!/usr/bin/env python3
"""Repeated fresh-cognition validation for social/relationship-heavy packets.

Validation-only. Builds disposable branches from accepted state. Frequencies are model
configuration diagnostics, never historical behavior probabilities.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parent))

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB, canonical_json
from bronze_world.engine import WorldEngine
from bronze_world.replay import replay_recorded_decisions
from build_fresh_cognition_pairs import build as build_v017_pairs


def clean_sqlite(p: Path):
    for x in (p,Path(str(p)+'-wal'),Path(str(p)+'-shm')):
        if x.exists(): x.unlink()


def copy_sqlite(src: Path,dst: Path):
    clean_sqlite(dst); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)


def household_resources(db: WorldDB, actor: str):
    hid=db.scalar("SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL",(actor,))
    return {r['resource_type']:float(r['amount']) for r in db.all("SELECT resource_type,amount FROM resource_stocks WHERE household_id=? ORDER BY resource_type",(hid,))}


def relationship(db: WorldDB,a: str,b: str):
    r=db.one("SELECT relationship_type,trust,respect,conflicts,favors_given,favors_owed FROM relationships WHERE from_person_id=? AND to_person_id=?",(a,b))
    return dict(r) if r else None


def build_p3_request_pair(root: Path, workdir: Path, v008_source: Path):
    base=workdir/'p3_base307.sqlite'; clean_sqlite(base)
    replay_recorded_decisions(root,v008_source,base,target_day=307)
    out={}
    for variant,stock in (("abundant",0.60),("last_reserve",0.15)):
        p=workdir/f'p3_workshop_request_{variant}.sqlite'; copy_sqlite(base,p)
        with WorldDB(p) as db:
            rid=db.one("SELECT run_id FROM runs LIMIT 1")['run_id']
            with db.transaction() as con:
                con.execute("UPDATE runs SET current_day=308 WHERE run_id=?",(rid,))
                con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-MERCH' AND resource_type='metal'",(stock,))
                sid=f'SCENE-V019-P3-WORKSHOP-{variant}'
                place=con.execute("SELECT current_place_id FROM persons WHERE person_id='P3'").fetchone()[0]
                stakes={
                    'amount':0.12,'resource':'metal','requester_household_id':'H-CRAFT','requester_person_id':'P7',
                    'request_event_id':None,
                    'reason':'The workshop has 0.03 metal and needs 0.12 more for one calibrated master-work cycle; all six prior reciprocal obligations were fulfilled.',
                    'validation_control':'supplier_metal_reserve_only',
                }
                con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                    sid,rid,308,place,'economic','resource_request',canonical_json(stakes),'{}',
                    canonical_json({'trusted_counterparty':True,'six_prior_returns_fulfilled':True,'household_reserve_matters':True}),
                    canonical_json(['I-MARKET']),'open'))
                con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,'P3','decision_actor'))
                con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,'P7','requester'))
            eng=WorldEngine(db,rid)
            jid=eng.enqueue_job(sid,'P3',['transfer_resource','communicate','refuse_proposal','enter_obligation','seek_mediation'])
            pkt=compile_packet(db,jid)
            out[f'p3_workshop_request_{variant}']={'db':str(p),'job_id':jid,'packet':pkt}
    return out


def build_bases(root: Path, workdir: Path, v015: Path, v014: Path, v008: Path):
    all_v017=build_v017_pairs(v015,v014,root,workdir/'v017_bases')
    keep={k:all_v017[k] for k in (
        'p16_care_no_conflict','p16_care_recovery_conflict',
        'p16_stewardship_funded','p16_stewardship_underfunded')}
    keep.update(build_p3_request_pair(root,workdir/'p3_bases',v008))
    return keep


def action_family(env):
    acts=env.get('proposed_actions',[])
    return acts[0].get('type','none') if acts else 'none'


def run_validation(root: Path, workdir: Path, attempts_path: Path, v015: Path, v014: Path, v008: Path):
    doc=json.loads(attempts_path.read_text()); attempts=doc['packets']; bases=build_bases(root,workdir/'bases',v015,v014,v008)
    results={}; summaries={}
    for name,envs in attempts.items():
        meta=bases[name]; base=Path(meta['db']); jid=meta['job_id']; rows=[]; expected_hash=None
        for idx,raw in enumerate(envs,1):
            dst=workdir/'attempts'/f'{name}__{idx}.sqlite'; copy_sqlite(base,dst)
            env=json.loads(json.dumps(raw)); env['decision_id']=f'VAL-V019-{name}-A{idx}'
            with WorldDB(dst) as db:
                job=db.one("SELECT * FROM cognition_jobs WHERE job_id=?",(jid,)); assert job and job['status']=='pending'
                pkt=compile_packet(db,jid)
                expected_hash=expected_hash or job['packet_hash']; assert job['packet_hash']==expected_hash
                before=household_resources(db,env['actor_id'])
                rel_before=relationship(db,'P3','P7') if env['actor_id']=='P3' else None
                eng=WorldEngine(db,job['run_id']); vr=eng.submit_decision(jid,env)
                after=household_resources(db,env['actor_id'])
                rel_after=relationship(db,'P3','P7') if env['actor_id']=='P3' else None
                rows.append({
                    'attempt':idx,'ok':vr.ok,'errors':vr.errors,'action_family':action_family(env),
                    'packet_hash':job['packet_hash'],'resources_before':before,'resources_after':after,
                    'relationship_before':rel_before,'relationship_after':rel_after,
                    'active_care_obligations':int(db.scalar("SELECT COUNT(*) FROM obligations WHERE status='active' AND obligation_type='continuing_kin_care'") or 0),
                    'active_property_stewardship':int(db.scalar("SELECT COUNT(*) FROM obligations WHERE status='active' AND obligation_type='household_property_stewardship'") or 0),
                    'active_reciprocal_exchange':int(db.scalar("SELECT COUNT(*) FROM obligations WHERE status='active' AND obligation_type='reciprocal_exchange'") or 0),
                    'rejected_jobs':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE status='rejected'") or 0),
                    'negative_resources':int(db.scalar("SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9") or 0),
                    'selected_intent':env.get('selected_intent'),'declared_uncertainty':env.get('declared_uncertainty'),
                })
        results[name]=rows; counts=Counter(r['action_family'] for r in rows)
        summaries[name]={'packet_hash':expected_hash,'action_family_counts':dict(sorted(counts.items())),'all_valid':all(r['ok'] for r in rows)}
    flat=[r for x in results.values() for r in x]
    checks={
        'all_18_valid':len(flat)==18 and all(r['ok'] for r in flat),
        'zero_rejections':all(r['rejected_jobs']==0 for r in flat),
        'zero_negative_resources':all(r['negative_resources']==0 for r in flat),
        'identical_packet_hash_within_group':all(len({r['packet_hash'] for r in xs})==1 for xs in results.values()),
        'care_no_conflict_consistently_fulfills':set(r['action_family'] for r in results['p16_care_no_conflict'])=={'fulfill_kin_care'},
        'care_recovery_conflict_consistently_defers':set(r['action_family'] for r in results['p16_care_recovery_conflict'])=={'defer_kin_care'},
        'care_obligation_survives_all_branches':all(r['active_care_obligations']>=1 for n in ('p16_care_no_conflict','p16_care_recovery_conflict') for r in results[n]),
        'funded_stewardship_accepts':set(r['action_family'] for r in results['p16_stewardship_funded'])=={'accept_property_stewardship'},
        'underfunded_stewardship_declines':set(r['action_family'] for r in results['p16_stewardship_underfunded'])=={'decline_property_stewardship'},
        'abundant_supplier_consistently_transfers':set(r['action_family'] for r in results['p3_workshop_request_abundant'])=={'transfer_resource'},
        'last_reserve_supplier_consistently_refuses':set(r['action_family'] for r in results['p3_workshop_request_last_reserve'])=={'refuse_proposal'},
        'supplier_control_dominates_same_relationship_history':summaries['p3_workshop_request_abundant']['action_family_counts']=={'transfer_resource':3} and summaries['p3_workshop_request_last_reserve']['action_family_counts']=={'refuse_proposal':3},
    }
    # Material/relationship consequences for P3 pair.
    checks['abundant_transfer_moves_only_requested_metal']=all(abs(r['resources_before']['metal']-0.60)<1e-9 and abs(r['resources_after']['metal']-0.48)<1e-9 for r in results['p3_workshop_request_abundant'])
    checks['scarce_refusal_preserves_last_reserve']=all(abs(r['resources_before']['metal']-0.15)<1e-9 and abs(r['resources_after']['metal']-0.15)<1e-9 for r in results['p3_workshop_request_last_reserve'])
    checks['funded_stewardship_materializes_reserve']=all(r['active_property_stewardship']==1 and abs(r['resources_after'].get('property_maintenance_reserve',0)-0.40)<1e-9 and abs(r['resources_after']['silver']-2.80)<1e-9 for r in results['p16_stewardship_funded'])
    checks['underfunded_stewardship_creates_nothing']=all(r['active_property_stewardship']==0 and 'property_maintenance_reserve' not in r['resources_after'] and abs(r['resources_after']['silver']-0.20)<1e-9 for r in results['p16_stewardship_underfunded'])
    checks['abundant_transfer_preserves_exchange_relationship']=all(r['active_reciprocal_exchange']==1 and r['relationship_after']['relationship_type']=='exchange_contact' and r['relationship_after']['conflicts']==0 and abs(r['relationship_after']['favors_given']-1.0)<1e-9 for r in results['p3_workshop_request_abundant'])
    checks['scarce_refusal_strains_but_preserves_relationship']=all(r['active_reciprocal_exchange']==0 and r['relationship_after']['relationship_type']=='exchange_contact' and r['relationship_after']['conflicts']==1 and abs(r['relationship_after']['trust']-(r['relationship_before']['trust']-0.02))<1e-9 and abs(r['relationship_after']['respect']-r['relationship_before']['respect'])<1e-9 for r in results['p3_workshop_request_last_reserve'])
    out={'mode':'social_relationship_repeated_fresh_cognition_validation','attempts_per_packet':3,'packet_count':6,'total_attempts':len(flat),'results':results,'packet_summaries':summaries,'checks':checks,'all_checks_pass':all(checks.values()),'interpretation_notice':'Repeated choices diagnose this cognition configuration only; they are not historical probabilities.'}
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--workdir',required=True); ap.add_argument('--attempts',required=True); ap.add_argument('--v015',default='state/ugarit_living_v015.sqlite'); ap.add_argument('--v014',default='state/ugarit_living_v014.sqlite'); ap.add_argument('--v008',default='state/ugarit_living_v008.sqlite'); ap.add_argument('--json-out',required=True)
    ns=ap.parse_args(); root=Path(ns.root); out=run_validation(root,Path(ns.workdir),Path(ns.attempts),Path(ns.v015),Path(ns.v014),Path(ns.v008)); Path(ns.json_out).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({'total_attempts':out['total_attempts'],'packet_summaries':out['packet_summaries'],'checks':out['checks'],'all_checks_pass':out['all_checks_pass']},indent=2)); raise SystemExit(0 if out['all_checks_pass'] else 2)
if __name__=='__main__': main()
