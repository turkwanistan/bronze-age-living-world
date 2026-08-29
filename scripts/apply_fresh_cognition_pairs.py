#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import argparse, json
from pathlib import Path
from bronze_world.db import WorldDB
from bronze_world.engine import WorldEngine
from bronze_world.cognition import compile_packet


def action_type(env):
    a=env.get('proposed_actions',[])
    return a[0].get('type') if a else None


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--packets',required=True); ap.add_argument('--decisions',required=True); ap.add_argument('--json-out',required=True)
    ns=ap.parse_args(); manifest=json.loads(Path(ns.packets).read_text()); decisions=json.loads(Path(ns.decisions).read_text())
    results={}
    for name,meta in manifest.items():
        env=json.loads(json.dumps(decisions[name])); env['decision_id']=f"VAL-V017-{name}"
        with WorldDB(meta['db']) as db:
            rid=db.one('SELECT run_id FROM runs LIMIT 1')['run_id']; eng=WorldEngine(db,rid)
            job=db.one('SELECT * FROM cognition_jobs WHERE job_id=?',(meta['job_id'],)); assert job and job['status']=='pending'
            packet=compile_packet(db,job['job_id'])
            before={r['resource_type']:float(r['amount']) for r in db.all("SELECT resource_type,amount FROM resource_stocks WHERE household_id=(SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL)",(env['actor_id'],))}
            vr=eng.submit_decision(job['job_id'],env)
            after={r['resource_type']:float(r['amount']) for r in db.all("SELECT resource_type,amount FROM resource_stocks WHERE household_id=(SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL)",(env['actor_id'],))}
            results[name]={
                'ok':vr.ok,'errors':vr.errors,'action_type':action_type(env),'packet_hash':job['packet_hash'],
                'household_resources_before':before,'household_resources_after':after,
                'accepted_jobs':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='accepted'",(rid,)) or 0),
                'rejected_jobs':int(db.scalar("SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status='rejected'",(rid,)) or 0),
                'negative_resources':int(db.scalar('SELECT COUNT(*) FROM resource_stocks WHERE amount < -1e-9') or 0),
            }
    pair_checks={
      'p10_resource_sensitive': results['p10_illness_adequate']['action_type']=='perform_ritual' and results['p10_illness_depleted']['action_type']=='perform_ritual' and abs(results['p10_illness_adequate']['household_resources_after']['ritual_goods']-0.8)<1e-9 and abs(results['p10_illness_depleted']['household_resources_after']['ritual_goods']-0.05)<1e-9,
      'p7_stock_sensitive': results['p7_recycling_buffered']['action_type']=='recycle_finished_metalwork' and results['p7_recycling_near_exhausted']['action_type']=='wait' and abs(results['p7_recycling_buffered']['household_resources_after']['finished_metalwork']-0.55)<1e-9 and abs(results['p7_recycling_near_exhausted']['household_resources_after']['finished_metalwork']-0.21)<1e-9,
      'p16_obligation_sensitive': results['p16_care_no_conflict']['action_type']=='fulfill_kin_care' and results['p16_care_recovery_conflict']['action_type']=='defer_kin_care',
      'property_funding_sensitive': results['p16_stewardship_funded']['action_type']=='accept_property_stewardship' and results['p16_stewardship_underfunded']['action_type']=='decline_property_stewardship',
      'shipping_epistemic_sensitive': results['p3_shipping_single_report']['action_type']=='send_message' and results['p3_shipping_discordant_reports']['action_type']=='wait',
      'all_decisions_valid': all(r['ok'] for r in results.values()),
      'no_rejections': all(r['rejected_jobs']==0 for r in results.values()),
      'no_negative_resources': all(r['negative_resources']==0 for r in results.values()),
    }
    out={'mode':'fresh_cognition_paired_validation','results':results,'pair_checks':pair_checks,'all_checks_pass':all(pair_checks.values())}
    Path(ns.json_out).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(out,indent=2,ensure_ascii=False))
    raise SystemExit(0 if out['all_checks_pass'] else 2)
if __name__=='__main__': main()
