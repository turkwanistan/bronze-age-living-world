#!/usr/bin/env python3
"""Build disposable paired validation branches and sealed cognition packets for v017.

No branch is canonical. Each pair starts from accepted v015 day 462 and changes one
declared control variable before sealing a new validation-only scene.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import argparse, json, shutil
from bronze_world.cognition import compile_packet
from bronze_world.db import WorldDB, canonical_json
from bronze_world.engine import WorldEngine
from bronze_world.lifeways import calendar_context
from bronze_world.fixture import init_fixture
from bronze_world.replay import replay_recorded_decisions


def _clean(path: Path):
    for p in (path, Path(str(path)+"-wal"), Path(str(path)+"-shm")):
        if p.exists(): p.unlink()


def _copy(source: Path, dest: Path):
    _clean(dest); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,dest)


def _scene(db, eng, *, scene_id, actor, family, trigger, stakes, material, social, institutions, allowed):
    run_id=eng.run_id; day=eng.day
    place=db.scalar("SELECT current_place_id FROM persons WHERE person_id=?",(actor,))
    with db.transaction() as con:
        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
            scene_id,run_id,day,place,family,trigger,canonical_json(stakes),canonical_json(material),canonical_json(social),canonical_json(institutions),"open"))
        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(scene_id,actor,"decision_actor"))
    jid=eng.enqueue_job(scene_id,actor,allowed)
    return compile_packet(db,jid)


def build(source: Path, property_source: Path, root: Path, workdir: Path):
    packets={}
    # Pair 1: same P10 minor illness, only H-WIDOW ritual stock differs.
    for variant,stock in (("adequate",1.00),("depleted",0.05)):
        path=workdir/f"p10_illness_{variant}.sqlite"; _copy(source,path)
        with WorldDB(path) as db:
            rid=db.one("SELECT run_id FROM runs LIMIT 1")["run_id"]; eng=WorldEngine(db,rid)
            with db.transaction() as con:
                con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-WIDOW' AND resource_type='ritual_goods'",(stock,))
            pkt=_scene(db,eng,scene_id=f"SCENE-V017-P10-ILLNESS-{variant}",actor="P10",family="religious",trigger="minor_illness",
                stakes={"health_uncertainty":"minor","validation_control":"ritual_goods_stock_only"},material={"time":"ordinary day"},
                social={"ritual_and_practical_responses_both_possible":True},institutions=[],
                allowed=["perform_ritual","communicate","travel","refuse_proposal"])
            packets[f"p10_illness_{variant}"]={"db":str(path),"job_id":pkt['job_id'],"packet":pkt}

    # Pair 2: same P7 no-lot recycling choice, only finished-output stock differs.
    for variant,finished in (("buffered",0.75),("near_exhausted",0.21)):
        path=workdir/f"p7_recycling_{variant}.sqlite"; _copy(source,path)
        with WorldDB(path) as db:
            rid=db.one("SELECT run_id FROM runs LIMIT 1")["run_id"]; eng=WorldEngine(db,rid)
            with db.transaction() as con:
                con.execute("UPDATE resource_stocks SET amount=0.03 WHERE household_id='H-CRAFT' AND resource_type='metal'")
                con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'",(finished,))
            kid=db.scalar("SELECT knowledge_id FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-NONE-001' AND learned_day<=? ORDER BY learned_day DESC LIMIT 1",(eng.day,))
            assert kid
            stakes={"situation_id":"SIT-V017-RECYCLE","no_lot_knowledge_id":kid,"current_metal":0.03,
                    "finished_metalwork_available":finished,"recycle_input_finished_metalwork":0.20,"recycle_output_metal":0.12,
                    "validation_control":"finished_metalwork_stock_only",
                    "fixture_notice":"v017 validation-only pair using existing recycling mechanics."}
            pkt=_scene(db,eng,scene_id=f"SCENE-V017-P7-RECYCLE-{variant}",actor="P7",family="economic",trigger="market_unavailable_recycling_choice",
                stakes=stakes,material={"market_lot_available":False,"recycling_destroys_finished_output":True},
                social={"market_relationship_not_broken":True},institutions=["I-MARKET"],allowed=["recycle_finished_metalwork","wait"])
            packets[f"p7_recycling_{variant}"]={"db":str(path),"job_id":pkt['job_id'],"packet":pkt}

    # Pair 3: same P16 care need; conflict branch has one active short recovery-rest obligation.
    for variant,conflict in (("no_conflict",False),("recovery_conflict",True)):
        path=workdir/f"p16_care_{variant}.sqlite"; _copy(source,path)
        with WorldDB(path) as db:
            rid=db.one("SELECT run_id FROM runs LIMIT 1")["run_id"]; eng=WorldEngine(db,rid)
            care=db.one("SELECT * FROM obligations WHERE status='active' AND obligation_type='continuing_kin_care' AND obligor_person_id='P16' LIMIT 1")
            assert care
            if conflict:
                with db.transaction() as con:
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",(
                        "O-V017-P16-RECOVERY","P16","H-WIDOW","P16","H-WIDOW","validation_recovery_rest",
                        "Validation-only control: brief rest today after minor symptoms before resuming ordinary exertion.",eng.day,"active",
                        canonical_json({"validation_control":True,"notice":"paired evaluation only; not canonical history"})))
            seasonal=calendar_context(eng.day,start_day_of_year=120)
            prior=int(db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='kin_care_fulfilled'",(rid,)) or 0)
            stakes={"situation_id":"SIT-V017-CARE","care_obligation_id":care['obligation_id'],"beneficiary_person_id":"P15",
                    "support_kind":"household_property_support_day","prior_fulfilled_care_episodes":prior,"seasonal_context":seasonal,
                    "validation_control":"temporary_recovery_obligation_only",
                    "fixture_notice":"v017 validation-only pair using existing care mechanics."}
            pkt=_scene(db,eng,scene_id=f"SCENE-V017-P16-CARE-{variant}",actor="P16",family="household",trigger="continuing_kin_care_need",
                stakes=stakes,material={"support_day_has_opportunity_cost":True},
                social={"continuing_care_obligation":True,"property_consequence_not_automatic":True},institutions=["I-MEDIATION"],
                allowed=["fulfill_kin_care","defer_kin_care","communicate"])
            packets[f"p16_care_{variant}"]={"db":str(path),"job_id":pkt['job_id'],"packet":pkt}

    # Pair 4: same negotiated stewardship terms; only current H-WIDOW liquid silver differs.
    base_property=workdir/"property_base_day458.sqlite"
    _clean(base_property)
    replay_recorded_decisions(root,property_source,base_property,target_day=458)
    for variant,silver in (("funded",3.20),("underfunded",0.20)):
        path=workdir/f"p16_stewardship_{variant}.sqlite"; _copy(base_property,path)
        with WorldDB(path) as db:
            rid=db.one("SELECT run_id FROM runs LIMIT 1")["run_id"]
            eng=WorldEngine(db,rid)
            with db.transaction() as con:
                con.execute("UPDATE runs SET current_day=459 WHERE run_id=?",(rid,))
                con.execute("UPDATE resource_stocks SET amount=? WHERE household_id='H-WIDOW' AND resource_type='silver'",(silver,))
            stakes={"situation_id":"SIT-V017-PROPERTY","household_id":"H-WIDOW","holder_person_id":"P15","reviewer_person_id":"P10",
                    "proposed_steward_person_id":"P16","final_reserve_amount":0.40,"joint_approval_required":True,
                    "purpose":"household_property_maintenance","validation_control":"liquid_silver_only",
                    "fixture_notice":"v017 validation-only final stewardship consent; no ownership or inheritance transfer."}
            pkt=_scene(db,eng,scene_id=f"SCENE-V017-P16-STEWARDSHIP-{variant}",actor="P16",family="household",trigger="household_property_stewardship_consent",
                stakes=stakes,material={"reserve_amount":0.40,"ownership_transfer":False,"inheritance_decided":False},
                social={"individual_steward_consent_required":True},institutions=[],
                allowed=["accept_property_stewardship","decline_property_stewardship","communicate"])
            packets[f"p16_stewardship_{variant}"]={"db":str(path),"job_id":pkt['job_id'],"packet":pkt}

    # Pair 5: P3 sees either one unconfirmed shipping report or two discordant delivered reports.
    scenario=json.loads((root/'scenarios/ugarit_1350/scenario.json').read_text())
    for variant in ("single_report","discordant_reports"):
        path=workdir/f"p3_shipping_{variant}.sqlite"; _clean(path)
        with WorldDB(path) as db:
            rid=init_fixture(db,root,1701,scenario_override=scenario); eng=WorldEngine(db,rid)
            with db.transaction() as con:
                con.execute("UPDATE runs SET current_day=7 WHERE run_id=?",(rid,))
                if variant=="discordant_reports":
                    con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                        'K-V017-SHIP2-P3','P3','PROP-SHIP-002',7,'validation_delivered_report',None,'[\"P12\",\"P3\"]','hearsay',0.58,'ordinary',None))
            if variant=="single_report":
                stakes={"situation_id":"SIT-V017-SHIP","known_knowledge_id":"K-SHIP-P3","known_report_proposition_id":"PROP-SHIP-001",
                        "report_age_days":7,"report_confidence":0.55,"contact_person_ids":["P11","P12"],
                        "epistemic_status":"unconfirmed_report; contacts may know different things but their knowledge is not exposed here",
                        "validation_control":"shipping_reports_only"}
                trigger='merchant_harbor_information_uncertainty'
                social={"information_provenance":True,"no_private_contact_knowledge":True}
            else:
                stakes={"situation_id":"SIT-V017-SHIP","report_knowledge_ids":["K-SHIP-P3","K-V017-SHIP2-P3"],
                        "report_proposition_ids":["PROP-SHIP-001","PROP-SHIP-002"],
                        "epistemic_status":"reports are incomplete/discordant; canonical shipment outcome remains unspecified",
                        "validation_control":"shipping_reports_only"}
                trigger='contradictory_shipping_reports'
                social={"information_provenance":True}
            pkt=_scene(db,eng,scene_id=f"SCENE-V017-P3-SHIP-{variant}",actor="P3",family="economic",trigger=trigger,
                stakes=stakes,material={},social=social,institutions=["I-MARKET"],allowed=["send_message","wait"])
            packets[f"p3_shipping_{variant}"]={"db":str(path),"job_id":pkt['job_id'],"packet":pkt}

    return packets


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-db',required=True); ap.add_argument('--property-source-db',required=True); ap.add_argument('--root',default='.'); ap.add_argument('--workdir',required=True); ap.add_argument('--json-out',required=True)
    ns=ap.parse_args(); packets=build(Path(ns.source_db),Path(ns.property_source_db),Path(ns.root),Path(ns.workdir)); Path(ns.json_out).write_text(json.dumps(packets,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:{'job_id':v['job_id'],'db':v['db']} for k,v in packets.items()},indent=2))
if __name__=='__main__': main()
