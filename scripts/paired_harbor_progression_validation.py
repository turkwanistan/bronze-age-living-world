#!/usr/bin/env python3
"""Paired v015 harbor-progression counterfactual from the same pre-decision state."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.replay import replay_recorded_decisions


def _pending(db, trigger, actor):
    return db.one(
        "SELECT j.* FROM cognition_jobs j JOIN scenes s USING(scene_id) "
        "WHERE j.status='pending' AND s.trigger_type=? AND j.actor_person_id=? ORDER BY j.rowid LIMIT 1",
        (trigger, actor),
    )


def _source_envelope(db, trigger, actor, day):
    row=db.one(
        "SELECT d.envelope_json FROM decisions d JOIN cognition_jobs j USING(job_id) JOIN scenes s USING(scene_id) "
        "WHERE d.validation_status='accepted' AND s.trigger_type=? AND j.actor_person_id=? AND d.applied_day=? ORDER BY d.rowid LIMIT 1",
        (trigger,actor,day),
    )
    return json.loads(row['envelope_json'])


def _summarize(path: Path):
    with WorldDB(path) as db:
        rid=db.one('SELECT run_id FROM runs LIMIT 1')['run_id']
        roles=[dict(r) for r in db.all(
            "SELECT r.name,pr.start_day,pr.end_day FROM person_roles pr JOIN roles r USING(role_id) "
            "WHERE pr.person_id='P11' ORDER BY pr.start_day,r.name"
        )]
        membership=dict(db.one("SELECT household_id,membership_role,since_day,until_day FROM household_memberships WHERE person_id='P11' AND until_day IS NULL"))
        legal=db.scalar("SELECT legal_status FROM persons WHERE person_id='P11'")
        work=[dict(r) for r in db.all("SELECT day,payload_json FROM events WHERE run_id=? AND event_type='occupation_work_cycle' AND actor_ids_json LIKE '%P11%' AND day>=460 ORDER BY day,event_seq",(rid,))]
        return {
            'day':int(db.scalar('SELECT current_day FROM runs WHERE run_id=?',(rid,))),
            'legal_status':legal,
            'membership':membership,
            'roles':roles,
            'post460_work':work,
            'negative_resources':int(db.scalar('SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9') or 0),
            'rejected_jobs':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='rejected'",(rid,)) or 0),
            'pending_jobs':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='pending'",(rid,)) or 0),
            'open_scenes':int(db.scalar("SELECT COUNT(*) FROM scenes WHERE run_id=? AND status='open'",(rid,)) or 0),
            'state_hash':db.state_hash(rid),
        }


def run(root: Path, source_db: Path, workdir: Path):
    workdir.mkdir(parents=True,exist_ok=True)
    base=workdir/'base_day459.sqlite'
    accept=workdir/'accept.sqlite'
    refuse=workdir/'refuse.sqlite'
    for p in [base,accept,refuse]:
        for q in [p,Path(str(p)+'-wal'),Path(str(p)+'-shm')]:
            if q.exists(): q.unlink()
    replay_recorded_decisions(root,source_db,base,target_day=459)
    shutil.copy2(base,accept); shutil.copy2(base,refuse)

    with WorldDB(source_db) as src:
        req_env=_source_envelope(src,'harbor_role_progression_review','P11',460)
        acc_env=_source_envelope(src,'harbor_role_progression_request','P12',460)

    for path,mode in [(accept,'accept'),(refuse,'refuse')]:
        with WorldDB(path) as db:
            rid=db.one('SELECT run_id FROM runs LIMIT 1')['run_id']; eng=WorldEngine(db,rid)
            eng.advance(1)
            j=_pending(db,'harbor_role_progression_review','P11'); assert j
            env=json.loads(json.dumps(req_env)); env['decision_id']=f'CF-{mode}-P11-REQUEST'
            r=eng.submit_decision(j['job_id'],env); assert r.ok,r.errors
            j=_pending(db,'harbor_role_progression_request','P12'); assert j
            if mode=='accept':
                env=json.loads(json.dumps(acc_env)); env['decision_id']='CF-accept-P12-REVIEW'
            else:
                env={
                    'decision_id':'CF-refuse-P12-REVIEW','actor_id':'P12',
                    'selected_intent':'retain the existing harbor household division of labor for now',
                    'proposed_actions':[{'type':'refuse_proposal','reason':'Keep the current porter+sailor division for this counterfactual; no legal or household change follows.'}],
                    'decisive_knowledge_or_belief_ids':['K-LOCAL-WORK-STATUS-001-P12'],
                    'decision_basis_tags':['paired_counterfactual','household_work_division'],
                    'declared_uncertainty':'This is an explicit validation branch, not a historical claim about P12.'
                }
            r=eng.submit_decision(j['job_id'],env); assert r.ok,r.errors
            eng.advance(2)
            # Resolve any unrelated seed-1701 day-460/day-462 jobs using source accepted policy.
            while True:
                pending=db.all("SELECT j.*,s.trigger_type FROM cognition_jobs j JOIN scenes s USING(scene_id) WHERE j.status='pending' ORDER BY j.created_day,j.rowid")
                if not pending: break
                j=pending[0]
                src_env=_source_envelope(src if False else db, '', '', 0) if False else None
                # The canonical seed-1701 source has Talmiyanu illness day460 and Yabninu trade wait day462.
                with WorldDB(source_db) as source:
                    row=source.one("SELECT d.envelope_json FROM decisions d JOIN cognition_jobs cj USING(job_id) JOIN scenes s USING(scene_id) WHERE d.validation_status='accepted' AND cj.actor_person_id=? AND s.trigger_type=? AND d.applied_day=? ORDER BY d.rowid LIMIT 1",(j['actor_person_id'],j['trigger_type'],j['created_day']))
                    if not row: raise RuntimeError(f'unexpected pending {j["actor_person_id"]} {j["trigger_type"]} day {j["created_day"]}')
                    env=json.loads(row['envelope_json']); env['decision_id']=f'CF-{mode}-{j["job_id"]}'
                r=eng.submit_decision(j['job_id'],env); assert r.ok,r.errors
                if eng.day < 462: eng.advance(462-eng.day)

    a=_summarize(accept); b=_summarize(refuse)
    invariants={
        'legal_status_same':a['legal_status']==b['legal_status']=='free_laborer',
        'household_membership_same':a['membership']==b['membership'],
        'no_negative_resources':a['negative_resources']==0 and b['negative_resources']==0,
        'no_rejected_pending_open':all(x==0 for x in [a['rejected_jobs'],a['pending_jobs'],a['open_scenes'],b['rejected_jobs'],b['pending_jobs'],b['open_scenes']]),
        'accept_has_harbor_coordinator':any(r['name']=='harbor_coordinator' and r['end_day'] is None for r in a['roles']),
        'refuse_keeps_porter':any(r['name']=='porter' and r['end_day'] is None for r in b['roles']),
        'refuse_has_no_harbor_coordinator':not any(r['name']=='harbor_coordinator' for r in b['roles']),
    }
    return {'mode':'paired_harbor_progression_counterfactual','source_db':str(source_db),'base_day':459,'target_day':462,'accept_branch':a,'refuse_branch':b,'invariants':invariants,'all_invariants_pass':all(invariants.values())}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--source-db',required=True); ap.add_argument('--workdir',required=True); ap.add_argument('--json-out')
    ns=ap.parse_args(); result=run(Path(ns.root),Path(ns.source_db),Path(ns.workdir)); text=json.dumps(result,indent=2,ensure_ascii=False)
    if ns.json_out: Path(ns.json_out).write_text(text+'\n',encoding='utf-8')
    print(text); raise SystemExit(0 if result['all_invariants_pass'] else 2)
if __name__=='__main__': main()
