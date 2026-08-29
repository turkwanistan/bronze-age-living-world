#!/usr/bin/env python3
"""Validate long-horizon relationship memory and recovery after a legitimate refusal.

Validation-only. Rebuilds the accepted v015 decision history under the current scenario,
then creates disposable day-463 branches. No validation branch becomes canonical state.
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB, canonical_json
from bronze_world.engine import WorldEngine
from bronze_world.fixture import init_fixture


def clean_sqlite(path: Path) -> None:
    for p in (path, Path(str(path)+"-wal"), Path(str(path)+"-shm")):
        if p.exists(): p.unlink()


def copy_sqlite(src: Path, dst: Path) -> None:
    clean_sqlite(dst); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)


def rebuild_current_scenario(root: Path, source: Path, out: Path, target_day: int = 462) -> dict:
    clean_sqlite(out)
    scenario=json.loads((root/'scenarios/ugarit_1350/scenario.json').read_text())
    with WorldDB(source) as src:
        source_run=src.one('SELECT * FROM runs ORDER BY created_at,run_id LIMIT 1')
        rows=src.all(
            "SELECT d.job_id,d.envelope_json,d.applied_day,d.rowid AS decision_rowid "
            "FROM decisions d JOIN cognition_jobs j USING(job_id) "
            "WHERE j.run_id=? AND d.validation_status='accepted' AND d.applied_day<=? "
            "ORDER BY d.applied_day,d.rowid", (source_run['run_id'],target_day))
        recorded={r['job_id']:json.loads(r['envelope_json']) for r in rows}
        order={r['job_id']:int(r['decision_rowid']) for r in rows}
        seed=int(source_run['rng_seed'])
    with WorldDB(out) as db:
        rid=init_fixture(db,root,seed,scenario_override=scenario); eng=WorldEngine(db,rid); applied=[]
        while True:
            pending=db.all("SELECT job_id,created_day,rowid AS job_rowid FROM cognition_jobs WHERE run_id=? AND status IN ('pending','rejected')",(rid,))
            eligible=[j for j in pending if int(j['created_day'])<=target_day]
            if eligible:
                missing=[j for j in eligible if j['job_id'] not in recorded]
                if missing: raise RuntimeError(f"unexpected_pre_v020_job:{[dict(x) for x in missing]}")
                job=min(eligible,key=lambda j:(order[j['job_id']],int(j['created_day']),int(j['job_rowid'])))
                vr=eng.submit_decision(job['job_id'],recorded[job['job_id']])
                if not vr.ok: raise RuntimeError(f"recorded_decision_rejected:{job['job_id']}:{vr.errors}")
                applied.append(job['job_id']); continue
            if eng.day>=target_day: break
            before=eng.day; eng.advance(target_day-before)
            if eng.day==before: raise RuntimeError(f"rebuild_no_progress:{before}")
        return {
            'scenario_version':scenario['scenario_version'],'day':eng.day,'recorded_decisions_applied':len(applied),
            'pending':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE status='pending'") or 0),
            'rejected':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE status='rejected'") or 0),
            'events':int(db.scalar("SELECT COUNT(*) FROM events") or 0),'state_hash':db.state_hash(rid),
        }


def resource_branch(base: Path, dest: Path, metal: float, envelope: dict, label: str) -> dict:
    copy_sqlite(base,dest)
    with WorldDB(dest) as db:
        rid=db.one('SELECT run_id FROM runs LIMIT 1')['run_id']; eng=WorldEngine(db,rid)
        with db.transaction() as con:
            con.execute('UPDATE runs SET current_day=463 WHERE run_id=?',(rid,))
            con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-MERCH' AND resource_type='metal'",(metal,))
            sid=f'SCENE-V020-{label}'
            place=con.execute("SELECT current_place_id FROM persons WHERE person_id='P3'").fetchone()[0]
            stakes={'requester_person_id':'P7','requester_household_id':'H-CRAFT','resource':'metal','amount':.12,
                    'reason':'Workshop requests 0.12 metal after the old scarcity refusal; all six earlier reciprocal obligations were repaid.',
                    'validation_control':'supplier_capacity_after_prior_refusal'}
            con.execute('INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)',(
                sid,rid,463,place,'economic','resource_request',canonical_json(stakes),canonical_json({'requested_metal':.12}),
                canonical_json({'prior_refusal_history':True}),canonical_json(['I-MARKET']),'open'))
            con.execute('INSERT INTO scene_participants VALUES (?,?,?)',(sid,'P3','decision_actor'))
            con.execute('INSERT INTO scene_participants VALUES (?,?,?)',(sid,'P7','requester'))
        jid=eng.enqueue_job(sid,'P3',['transfer_resource','refuse_proposal','communicate','enter_obligation','seek_mediation'])
        packet=compile_packet(db,jid)
        refusal=[m for m in packet['relevant_memories'] if m['created_day']==308 and 'Refused:' in m['summary'] and '0.15 raw metal' in m['summary']]
        before=dict(db.one("SELECT trust,respect,conflicts,favors_given,favors_owed FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'"))
        env=json.loads(json.dumps(envelope)); env['decision_id']=f'VAL-V020-{label}'
        vr=eng.submit_decision(jid,env)
        after=dict(db.one("SELECT trust,respect,conflicts,favors_given,favors_owed FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'"))
        return {
            'ok':vr.ok,'errors':vr.errors,'packet_hash':db.one('SELECT packet_hash FROM cognition_jobs WHERE job_id=?',(jid,))['packet_hash'],
            'refusal_memory_present':bool(refusal),'refusal_memory_day':refusal[0]['created_day'] if refusal else None,
            'relationship_before':before,'relationship_after':after,
            'merchant_metal_after':float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='metal'")),
            'craft_metal_after':float(db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'")),
            'active_reciprocal_exchange':int(db.scalar("SELECT COUNT(*) FROM obligations WHERE obligation_type='reciprocal_exchange' AND status='active'") or 0),
            'negative_resources':int(db.scalar('SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9') or 0),
        }


def canonical_low_cost_repair(v008: Path, v009: Path) -> dict:
    out={}
    for label,path in [('before',v008),('after',v009)]:
        with WorldDB(path) as db:
            out[label]={
                'p3_to_p7':dict(db.one("SELECT trust,respect,conflicts,relationship_type FROM relationships WHERE from_person_id='P3' AND to_person_id='P7'")),
                'p7_to_p3':dict(db.one("SELECT trust,respect,conflicts,relationship_type FROM relationships WHERE from_person_id='P7' AND to_person_id='P3'")),
                'introduction_events':int(db.scalar("SELECT COUNT(*) FROM events WHERE event_type='market_introduction_granted' AND day>=309") or 0),
            }
    return out


def run(root: Path, workdir: Path, decisions_path: Path, v015: Path, v008: Path, v009: Path) -> dict:
    decisions=json.loads(decisions_path.read_text()); workdir.mkdir(parents=True,exist_ok=True)
    base=workdir/'v020_base.sqlite'; compatibility=rebuild_current_scenario(root,v015,base)
    unchanged=resource_branch(base,workdir/'unchanged.sqlite',.15,decisions['unchanged_scarcity'],'UNCHANGED')
    recovered=resource_branch(base,workdir/'recovered.sqlite',.60,decisions['recovered_capacity'],'RECOVERED')
    repair=canonical_low_cost_repair(v008,v009)
    checks={
        'new_scenario_reuses_all_157_pre463_decisions':compatibility['recorded_decisions_applied']==157 and compatibility['events']==6608 and compatibility['pending']==0 and compatibility['rejected']==0,
        'old_refusal_memory_visible_in_both_day463_packets':unchanged['refusal_memory_present'] and recovered['refusal_memory_present'],
        'unchanged_scarcity_refuses_without_new_debt':unchanged['ok'] and abs(unchanged['merchant_metal_after']-.15)<1e-9 and unchanged['active_reciprocal_exchange']==0,
        'recovered_capacity_resumes_bounded_supply':recovered['ok'] and abs(recovered['merchant_metal_after']-.48)<1e-9 and recovered['active_reciprocal_exchange']==1,
        'no_negative_resources':unchanged['negative_resources']==0 and recovered['negative_resources']==0,
        'canonical_low_cost_cooperation_improved_relationship':repair['after']['p3_to_p7']['trust']>repair['before']['p3_to_p7']['trust'] and repair['after']['p3_to_p7']['respect']>repair['before']['p3_to_p7']['respect'] and repair['after']['p7_to_p3']['trust']>repair['before']['p7_to_p3']['trust'],
        'canonical_repair_preserved_conflict_history':repair['before']['p3_to_p7']['conflicts']==1 and repair['after']['p3_to_p7']['conflicts']==1 and repair['after']['p3_to_p7']['relationship_type']=='exchange_contact',
        'canonical_repair_was_actual_market_introduction':repair['after']['introduction_events']>=1,
    }
    return {'mode':'v020_relationship_memory_and_recovery_validation','compatibility':compatibility,'unchanged_scarcity':unchanged,'recovered_capacity':recovered,'canonical_low_cost_repair':repair,'checks':checks,'all_checks_pass':all(checks.values())}


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--workdir',required=True); ap.add_argument('--decisions',required=True); ap.add_argument('--v015',required=True); ap.add_argument('--v008',required=True); ap.add_argument('--v009',required=True); ap.add_argument('--json-out',required=True)
    ns=ap.parse_args(); result=run(Path(ns.root),Path(ns.workdir),Path(ns.decisions),Path(ns.v015),Path(ns.v008),Path(ns.v009))
    Path(ns.json_out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'checks':result['checks'],'all_checks_pass':result['all_checks_pass']},indent=2))
    raise SystemExit(0 if result['all_checks_pass'] else 2)
if __name__=='__main__': main()
