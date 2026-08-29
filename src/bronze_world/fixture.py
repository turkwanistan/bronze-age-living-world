from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import WorldDB, canonical_json
from .evidence import ingest_evidence
from .ids import stable_id

FIXTURE_NOTICE = "Abstract fixture units under ASM-FIXTURE-001/002; not historical quantities."

PLACES = [
    ("P-UGARIT", "Ugarit", "city", None, {}),
    ("P-NORTH-NEIGH", "North residential quarter", "neighborhood", "P-UGARIT", {}),
    ("P-HARBOR", "Harbor interface", "harbor", "P-UGARIT", {}),
    ("P-MARKET", "Neighborhood market", "market", "P-UGARIT", {}),
    ("P-SHRINE", "Local shrine", "shrine", "P-NORTH-NEIGH", {}),
    ("P-PALACE-OFFICE", "Palace administrative interface", "administrative_office", "P-UGARIT", {}),
    ("P-WORKSHOP", "Craft workshop lane", "workshop", "P-NORTH-NEIGH", {}),
    ("P-FIELDS", "Hinterland fields", "field", "P-UGARIT", {}),
    ("P-WELL-PRIVATE", "Private household well", "well", "P-NORTH-NEIGH", {"access":"restricted"}),
    ("P-WELL-SHARED", "Shared neighborhood water point", "well", "P-NORTH-NEIGH", {"access":"shared"}),
]

INSTITUTIONS = [
    ("I-WATER", "Neighborhood water access", "water_access", "P-NORTH-NEIGH", {"procedures":["household access","negotiated neighbor access"]}, {"sanctions":["refusal","reputation cost"]}),
    ("I-SHRINE", "Local household/shrine ritual network", "ritual", "P-SHRINE", {"procedures":["household rite","consult specialist"]}, {"sanctions":[]}),
    ("I-MARKET", "Market and credit interface", "market_credit", "P-MARKET", {"procedures":["exchange","credit negotiation","witnessed agreement"]}, {"sanctions":["credit refusal","reputation cost"]}),
    ("I-PALACE", "Palace administrative interface", "administrative", "P-PALACE-OFFICE", {"procedures":["record obligation","request labor/resource","petition"]}, {"sanctions":["administrative pressure","patron withdrawal"]}),
    ("I-MEDIATION", "Informal kin/patron/elder mediation interface", "informal_mediation", "P-NORTH-NEIGH", {"procedures":["private negotiation","kin/patron/elder mediation","compensation or obligation"]}, {"sanctions":["relationship strain","reputation cost","unresolved dispute"]}),
]

HOUSEHOLDS = [
    {"id":"H-FARM","name":"Field household","home":"P-NORTH-NEIGH","food":42,"oil":8,"silver":2,"need":0.80,"weekly":5.6,"water":"shared","status":"common agricultural","form":"multi-generation"},
    {"id":"H-MERCH","name":"Merchant household","home":"P-NORTH-NEIGH","food":33,"oil":10,"silver":18,"need":0.65,"weekly":4.55,"water":"private","status":"prosperous merchant","form":"joint household"},
    {"id":"H-SCRIBE","name":"Scribal household","home":"P-NORTH-NEIGH","food":27,"oil":7,"silver":7,"need":0.55,"weekly":3.85,"water":"private","status":"institution-connected specialist","form":"small household"},
    {"id":"H-CRAFT","name":"Craft household","home":"P-NORTH-NEIGH","food":29,"oil":5,"silver":4,"need":0.70,"weekly":4.9,"water":"shared","status":"craft specialist","form":"nuclear-plus-apprentice"},
    {"id":"H-RITUAL","name":"Ritual specialist household","home":"P-NORTH-NEIGH","food":24,"oil":12,"silver":3,"need":0.50,"weekly":3.5,"water":"shared","status":"ritual specialist","form":"small household"},
    {"id":"H-HARBOR","name":"Harbor household","home":"P-HARBOR","food":31,"oil":5,"silver":6,"need":0.65,"weekly":4.55,"water":"shared","status":"mobile maritime labor","form":"nuclear"},
    {"id":"H-DEPEND","name":"Dependent labor household","home":"P-NORTH-NEIGH","food":18,"oil":3,"silver":1,"need":0.75,"weekly":5.25,"water":"shared","status":"dependent labor","form":"couple with dependent"},
    {"id":"H-WIDOW","name":"Widowed elder household","home":"P-NORTH-NEIGH","food":16,"oil":4,"silver":3,"need":0.48,"weekly":3.36,"water":"shared","status":"widowed property claimant","form":"widowed/younger kin"},
]

# Display names are simulation identities. They are not claims about historical individuals.
PEOPLE = [
    {"id":"P1","name":"Ilimilku","house":"H-FARM","age":39,"sex":"male","member":"senior","roles":["farmer","household_manager"],"legal":"free_householder","traits":{"risk_tolerance":.35,"reciprocity_sensitivity":.78,"status_sensitivity":.42,"ritual_commitment":.70,"family_loyalty":.88,"sociability":.56},"beliefs":{"ritual_obligation_strength":.75,"omen_sensitivity":.48},"goals":["protect grain","maintain kin obligations"]},
    {"id":"P2","name":"Ahatmilku","house":"H-FARM","age":34,"sex":"female","member":"adult","roles":["farmer","textile_worker"],"legal":"free_householder","traits":{"risk_tolerance":.46,"reciprocity_sensitivity":.70,"status_sensitivity":.35,"ritual_commitment":.62,"family_loyalty":.80,"sociability":.67},"beliefs":{"ritual_obligation_strength":.66,"omen_sensitivity":.40},"goals":["secure household stores","support younger kin"]},
    {"id":"P3","name":"Yabninu","house":"H-MERCH","age":44,"sex":"male","member":"senior","roles":["merchant","broker"],"legal":"free_householder","traits":{"risk_tolerance":.64,"reciprocity_sensitivity":.82,"status_sensitivity":.72,"ritual_commitment":.48,"family_loyalty":.76,"sociability":.74,"mobility_comfort":.83},"beliefs":{"ritual_obligation_strength":.50,"omen_sensitivity":.31},"goals":["preserve credit","protect household continuity"]},
    {"id":"P4","name":"Pidduya","house":"H-MERCH","age":37,"sex":"female","member":"adult","roles":["household_manager","merchant_account_partner"],"legal":"free_householder","traits":{"risk_tolerance":.40,"reciprocity_sensitivity":.88,"status_sensitivity":.58,"ritual_commitment":.61,"family_loyalty":.82,"sociability":.63},"beliefs":{"ritual_obligation_strength":.65,"omen_sensitivity":.44},"goals":["maintain reserves","protect family credit reputation"]},
    {"id":"P5","name":"Rapanu","house":"H-SCRIBE","age":35,"sex":"male","member":"senior","roles":["scribe","interpreter"],"legal":"free_specialist","traits":{"risk_tolerance":.32,"reciprocity_sensitivity":.60,"status_sensitivity":.68,"ritual_commitment":.55,"family_loyalty":.62,"sociability":.51,"novelty_seeking":.70},"beliefs":{"ritual_obligation_strength":.58,"omen_sensitivity":.36},"goals":["protect record accuracy","maintain institutional trust"]},
    {"id":"P6","name":"Talmiyanu","house":"H-SCRIBE","age":29,"sex":"female","member":"adult","roles":["household_manager","textile_worker"],"legal":"free_householder","traits":{"risk_tolerance":.52,"reciprocity_sensitivity":.67,"status_sensitivity":.38,"ritual_commitment":.66,"family_loyalty":.71,"sociability":.77},"beliefs":{"ritual_obligation_strength":.69,"omen_sensitivity":.52},"goals":["secure household","maintain neighborhood ties"]},
    {"id":"P7","name":"Urtenu","house":"H-CRAFT","age":41,"sex":"male","member":"senior","roles":["metal_craft_worker","household_manager"],"legal":"free_specialist","traits":{"risk_tolerance":.55,"reciprocity_sensitivity":.57,"status_sensitivity":.49,"ritual_commitment":.43,"family_loyalty":.73,"sociability":.48,"entrepreneurial_tendency":.68},"beliefs":{"ritual_obligation_strength":.47,"omen_sensitivity":.29},"goals":["keep workshop supplied","train apprentice"]},
    {"id":"P8","name":"Niqmepa","house":"H-CRAFT","age":18,"sex":"male","member":"apprentice","roles":["craft_apprentice","porter"],"legal":"dependent_apprentice","traits":{"risk_tolerance":.72,"reciprocity_sensitivity":.51,"status_sensitivity":.62,"ritual_commitment":.39,"family_loyalty":.55,"sociability":.70,"novelty_seeking":.80},"beliefs":{"ritual_obligation_strength":.43,"omen_sensitivity":.35},"goals":["gain craft standing","avoid workshop blame"]},
    {"id":"P9","name":"Attanu","house":"H-RITUAL","age":52,"sex":"male","member":"senior","roles":["ritual_specialist","household_manager"],"legal":"free_specialist","traits":{"risk_tolerance":.27,"reciprocity_sensitivity":.71,"status_sensitivity":.61,"ritual_commitment":.93,"family_loyalty":.69,"sociability":.58},"beliefs":{"ritual_obligation_strength":.96,"omen_sensitivity":.84},"goals":["perform rites correctly","preserve specialist trust"]},
    {"id":"P10","name":"Šapšu","house":"H-RITUAL","age":24,"sex":"female","member":"adult","roles":["ritual_assistant","healer_helper"],"legal":"free_householder","traits":{"risk_tolerance":.44,"reciprocity_sensitivity":.79,"status_sensitivity":.33,"ritual_commitment":.87,"family_loyalty":.77,"sociability":.82,"empathy":.86},"beliefs":{"ritual_obligation_strength":.91,"omen_sensitivity":.68},"goals":["care for clients","build ritual competence"]},
    {"id":"P11","name":"Abdi-Rashap","house":"H-HARBOR","age":31,"sex":"male","member":"senior","roles":["sailor","porter"],"legal":"free_laborer","traits":{"risk_tolerance":.78,"reciprocity_sensitivity":.59,"status_sensitivity":.45,"ritual_commitment":.51,"family_loyalty":.64,"sociability":.76,"mobility_comfort":.94},"beliefs":{"ritual_obligation_strength":.55,"omen_sensitivity":.47},"goals":["secure next voyage","bring resources home"]},
    {"id":"P12","name":"Dagan-beli","house":"H-HARBOR","age":30,"sex":"female","member":"adult","roles":["household_manager","market_trader"],"legal":"free_householder","traits":{"risk_tolerance":.49,"reciprocity_sensitivity":.73,"status_sensitivity":.41,"ritual_commitment":.60,"family_loyalty":.81,"sociability":.84},"beliefs":{"ritual_obligation_strength":.63,"omen_sensitivity":.39},"goals":["smooth voyage income gaps","maintain market ties"]},
    {"id":"P13","name":"Arhalbu","house":"H-DEPEND","age":36,"sex":"male","member":"senior","roles":["dependent_field_worker","corvee_laborer"],"legal":"dependent_laborer","traits":{"risk_tolerance":.38,"reciprocity_sensitivity":.74,"status_sensitivity":.57,"ritual_commitment":.65,"family_loyalty":.91,"sociability":.46,"deference":.71},"beliefs":{"ritual_obligation_strength":.70,"omen_sensitivity":.54},"goals":["keep dependents fed","reduce vulnerability to patron demands"]},
    {"id":"P14","name":"Mullissu","house":"H-DEPEND","age":33,"sex":"female","member":"adult","roles":["textile_worker","dependent_household_worker"],"legal":"dependent_laborer","traits":{"risk_tolerance":.45,"reciprocity_sensitivity":.86,"status_sensitivity":.48,"ritual_commitment":.72,"family_loyalty":.93,"sociability":.65,"empathy":.74},"beliefs":{"ritual_obligation_strength":.77,"omen_sensitivity":.58},"goals":["protect child/kin","maintain aid network"]},
    {"id":"P15","name":"Bat-Rapiu","house":"H-WIDOW","age":48,"sex":"female","member":"senior","roles":["household_manager","property_claimant"],"legal":"widowed_householder","traits":{"risk_tolerance":.43,"reciprocity_sensitivity":.83,"status_sensitivity":.66,"ritual_commitment":.68,"family_loyalty":.75,"sociability":.55,"forgiveness":.41},"beliefs":{"ritual_obligation_strength":.72,"omen_sensitivity":.46},"goals":["preserve household property","secure support from kin"]},
    {"id":"P16","name":"Kothar","house":"H-WIDOW","age":21,"sex":"male","member":"younger_kin","roles":["porter","seasonal_worker"],"legal":"free_householder","traits":{"risk_tolerance":.69,"reciprocity_sensitivity":.62,"status_sensitivity":.54,"ritual_commitment":.42,"family_loyalty":.68,"sociability":.73,"mobility_comfort":.75},"beliefs":{"ritual_obligation_strength":.45,"omen_sensitivity":.34},"goals":["earn household resources","increase standing"]}
]

ROLE_DEFS = {
    "farmer":"agriculture","household_manager":"household","textile_worker":"craft","merchant":"commerce","broker":"commerce",
    "merchant_account_partner":"commerce","scribe":"scribal","interpreter":"scribal","metal_craft_worker":"craft","craft_apprentice":"craft",
    "porter":"labor","ritual_specialist":"ritual","ritual_assistant":"ritual","healer_helper":"ritual","sailor":"maritime",
    "market_trader":"commerce","dependent_field_worker":"agriculture","corvee_laborer":"institutional_labor","dependent_household_worker":"household",
    "property_claimant":"household","seasonal_worker":"labor","recognized_craft_worker":"craft"
}

RELATIONSHIPS = [
    ("P1","P2","spouse",.82,.79,.02,.72),("P2","P1","spouse",.84,.76,.01,.69),
    ("P3","P4","spouse",.73,.83,.03,.81),("P4","P3","spouse",.76,.78,.02,.74),
    ("P5","P6","spouse",.70,.75,.02,.68),("P6","P5","spouse",.74,.71,.02,.72),
    ("P7","P8","master_apprentice",.52,.63,.11,.58),("P8","P7","apprentice_master",.48,.59,.19,.76),
    ("P9","P10","mentor_kin",.78,.84,.04,.82),("P10","P9","kin_mentor",.81,.88,.06,.91),
    ("P11","P12","spouse",.80,.72,.03,.70),("P12","P11","spouse",.82,.69,.05,.67),
    ("P13","P14","spouse",.85,.82,.07,.76),("P14","P13","spouse",.87,.84,.06,.79),
    ("P15","P16","kin",.67,.58,.03,.61),("P16","P15","kin",.71,.62,.04,.73),
    ("P1","P13","work_neighbor",.43,.55,.05,.46),("P13","P1","work_neighbor",.47,.61,.08,.62),
    ("P3","P11","trade_contact",.38,.69,.04,.58),("P11","P3","trade_contact",.42,.66,.10,.72),
    ("P3","P5","record_client",.45,.77,.03,.73),("P5","P3","client",.41,.71,.05,.63),
    ("P15","P2","neighbor",.58,.65,.03,.57),("P2","P15","neighbor",.61,.68,.02,.60),
    # Fixture neighbor tie used only to exercise bounded water-access negotiation.
    ("P2","P6","neighbor",.50,.58,.03,.55),("P6","P2","neighbor",.53,.60,.03,.57),
]


def init_fixture(db: WorldDB, root: Path, seed: int = 1350, *, scenario_override: dict[str, Any] | None = None) -> str:
    db.migrate()
    ingest_evidence(db, root)
    scenario = (json.loads(json.dumps(scenario_override)) if scenario_override is not None
                else json.loads((root / "scenarios/ugarit_1350/scenario.json").read_text(encoding="utf-8")))
    run_id = stable_id("RUN", scenario["scenario_id"], seed)
    active_assumptions = set(scenario.get("active_assumptions", []))
    simulation_code_version = "0.3.0" if "ASM-FIXTURE-022" in active_assumptions else "0.2.0"
    simulation_version_id = "SIM-0.3.0" if simulation_code_version == "0.3.0" else "SIM-0.2.0"
    with db.transaction() as con:
        con.execute("INSERT OR REPLACE INTO simulation_versions VALUES (?,?,?,?,?)", (simulation_version_id,simulation_code_version,scenario["schema_version"],"cognition-v1","evidence-v0.1"))
        con.execute("INSERT OR REPLACE INTO scenarios VALUES (?,?,?,?,?)", (scenario["scenario_id"],scenario["scenario_version"],scenario["year_bce"],scenario["local_period_label"],canonical_json(scenario)))
        con.execute("INSERT OR REPLACE INTO runs(run_id,scenario_id,scenario_version,evidence_model_version,simulation_code_version,rng_seed,cognition_protocol_version,schema_version,current_day,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (run_id,scenario["scenario_id"],scenario["scenario_version"],scenario["evidence_model_version"],simulation_code_version,seed,scenario["cognition_protocol_version"],scenario["schema_version"],0,"active","2026-08-28T00:00:00Z"))
        for pid,name,ptype,parent,attrs in PLACES:
            con.execute("INSERT OR REPLACE INTO places VALUES (?,?,?,?,?)", (pid,name,ptype,parent,canonical_json(attrs)))
        route_pairs = [
            ("P-NORTH-NEIGH","P-MARKET",1,"walk"),("P-NORTH-NEIGH","P-SHRINE",1,"walk"),("P-NORTH-NEIGH","P-PALACE-OFFICE",1,"walk"),
            ("P-NORTH-NEIGH","P-WORKSHOP",1,"walk"),("P-NORTH-NEIGH","P-FIELDS",1,"walk"),("P-NORTH-NEIGH","P-HARBOR",1,"walk"),
            ("P-HARBOR","P-MARKET",1,"walk"),("P-UGARIT","P-HARBOR",1,"walk")]
        for a,b,days,mode in route_pairs:
            for x,y in [(a,b),(b,a)]:
                rid=stable_id("ROUTE",x,y,mode)
                con.execute("INSERT OR REPLACE INTO routes VALUES (?,?,?,?,?,?,?,?)",(rid,x,y,days,mode,1,"{}","{}"))
        for iid,name,itype,place,proc,san in INSTITUTIONS:
            access = {"water_access_variants":["shared","private"]} if iid=="I-WATER" else {}
            con.execute("INSERT OR REPLACE INTO institutions VALUES (?,?,?,?,?,?,?,?,?,?,?)",(iid,name,itype,place,"{}",canonical_json(proc),"{}","{}",canonical_json(san),canonical_json(access),"{}"))
        for h in HOUSEHOLDS:
            status = {"status":h["status"],"water_access":h["water"]}
            if "ASM-FIXTURE-024" in active_assumptions:
                if h["id"] == "H-FARM":
                    status["draft_access"] = "controls_fixture_team"
                elif h["id"] == "H-DEPEND":
                    status["draft_access"] = "requires_negotiation"
            con.execute("INSERT OR REPLACE INTO households VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                h["id"],h["name"],h["home"],canonical_json({"form":h["form"]}),canonical_json({"pool":"household"}),canonical_json({"dependent_care":"expected"}),canonical_json({"household_cult":"active"}),canonical_json(status),h["need"],h["weekly"],FIXTURE_NOTICE))
            for r,amt in [("grain",h["food"]),("oil",h["oil"]),("silver",h["silver"]),("ritual_goods",2 if h["id"]!="H-RITUAL" else 7)]:
                con.execute("INSERT OR REPLACE INTO resource_stocks VALUES (?,?,?,?,?)",(h["id"],r,float(amt),"abstract_fixture_unit","ASM-FIXTURE-001"))
            # Specialist inputs/outputs make occupations materially dependent instead of
            # decorative role labels. Quantities are engineering calibration only.
            specialist_resources = {
                "H-FARM": [("fiber", 3.5), ("textile_goods", 0.0)],
                "H-SCRIBE": [("fiber", 2.5), ("textile_goods", 0.0)],
                "H-DEPEND": [("fiber", 2.5), ("textile_goods", 0.0)],
                "H-CRAFT": [("metal", 1.5), ("charcoal", 6.0), ("finished_metalwork", 0.0)],
                "H-MERCH": [("metal", 3.0), ("trade_goods", 3.0)],
                "H-HARBOR": [("trade_goods", 1.0)],
            }.get(h["id"], [])
            for r,amt in specialist_resources:
                con.execute("INSERT OR REPLACE INTO resource_stocks VALUES (?,?,?,?,?)",
                            (h["id"],r,float(amt),"abstract_fixture_unit","ASM-FIXTURE-009"))
            if "ASM-FIXTURE-029" in active_assumptions and h["id"] == "H-CRAFT":
                con.execute("INSERT OR REPLACE INTO resource_stocks VALUES (?,?,?,?,?)",
                            ("H-CRAFT","fuel_feedstock",1.20,"abstract_fixture_unit","ASM-FIXTURE-029"))
            if "ASM-FIXTURE-025" in scenario.get("active_assumptions", []) and h["id"] == "H-FARM":
                con.execute("INSERT OR REPLACE INTO resource_stocks VALUES (?,?,?,?,?)",
                            ("H-FARM","draft_team_condition",1.0,"abstract_fixture_unit","ASM-FIXTURE-025"))
        for role,fam in ROLE_DEFS.items():
            con.execute("INSERT OR REPLACE INTO roles VALUES (?,?,?,?,?)",(f"R-{role.upper()}",role,fam,None,"{}"))
        for p in PEOPLE:
            con.execute("INSERT OR REPLACE INTO persons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(
                p["id"],p["name"],"simulation_identity_from_provisional_attested_name_pool; verify per P0 backlog",p["age"],p["sex"],"adult",1,1,
                next(h["home"] for h in HOUSEHOLDS if h["id"]==p["house"]),p["legal"],canonical_json({}),canonical_json(p["beliefs"]),canonical_json(p["goals"])))
            con.execute("INSERT OR REPLACE INTO household_memberships VALUES (?,?,?,?,?)",(p["house"],p["id"],p["member"],0,None))
            for t,v in p["traits"].items():
                con.execute("INSERT OR REPLACE INTO character_traits VALUES (?,?,?,?)",(p["id"],t,v,"individual fixture disposition; not civilization-derived"))
            for i,role in enumerate(p["roles"]):
                con.execute("INSERT OR REPLACE INTO person_roles VALUES (?,?,?,?,?)",(p["id"],f"R-{role.upper()}",i+1,0,None))
        for a,b,typ,aff,trust,fear,respect in RELATIONSHIPS:
            con.execute("INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
                stable_id("REL",a,b),a,b,typ,None,aff,trust,fear,respect,0,0,0,0,"{}",0))
        if int(scenario["schema_version"]) >= 2:
            initial_spouses = [("P1","P2","H-FARM"),("P3","P4","H-MERCH"),("P5","P6","H-SCRIBE"),("P11","P12","H-HARBOR"),("P13","P14","H-DEPEND")]
            for a,b,residence in initial_spouses:
                mid=stable_id("MAR",run_id,"initial",a,b)
                prov=canonical_json({"origin":"initial fixture spouse relationship","notice":"simulation starting relationship; not a claim about historical individuals"})
                con.execute("INSERT OR REPLACE INTO marriages VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (mid,run_id,a,b,0,None,"active",residence,canonical_json({"residence_household_id":residence}),prov))
                kid=stable_id("KIN",run_id,a,b,"spouse",0)
                con.execute("INSERT OR REPLACE INTO kinship_edges VALUES (?,?,?,?,?,?,?,?)",
                            (kid,run_id,a,b,"spouse",0,None,prov))
        # Initial cross-household obligations make later choices causally interesting without forcing a crisis.
        con.execute("INSERT OR REPLACE INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",(
            "O-FAVOR-001","P15","H-WIDOW","P2","H-FARM","reciprocal_aid","Bat-Rapiu remembers prior food aid from Ahatmilku's household; reciprocal help is expected if feasible.",21,"active",canonical_json({"basis":"SIT-002","uncertainty":"fixture social setup"})))
        con.execute("INSERT OR REPLACE INTO debts VALUES (?,?,?,?,?,?,?,?,?)",(
            "D-DEPEND-001","H-DEPEND","H-MERCH","grain",4.0,4.0,28,"open",canonical_json({"assumption":"fixture debt for causal mechanics; not historical rate"})))
        # Explicit simulation circumstances for the information-provenance slice. They are
        # unverified reports, not claims about a historical Ugaritic shipment.
        con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
            "PROP-SHIP-001","A coastal contact reports that one expected vessel may be delayed.","simulation_contingent",
            canonical_json({"canonical":"unconfirmed","topic":"fixture_expected_arrival","provenance":"ASM-FIXTURE-005"})))
        for kid,person,mode,conf in [("K-SHIP-P3","P3","hearsay",.55),("K-SHIP-P11","P11","direct",.72)]:
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (kid,person,"PROP-SHIP-001",0,"initial_scenario",None,"[]",mode,conf,"ordinary",None))
        con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
            "PROP-SHIP-002","A market-side contact has received no confirmation that the expected arrival timing changed.",
            "simulation_contingent",canonical_json({"canonical":"unconfirmed","topic":"fixture_expected_arrival","provenance":"ASM-FIXTURE-005"})))
        con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    ("K-SHIP-P12","P12","PROP-SHIP-002",0,"initial_scenario",None,"[]","hearsay",.58,"ordinary",None))
        # Every person gets local cultural/institutional knowledge, but not private facts.
        con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",("PROP-LOCAL-001","Household resource obligations and reputation can affect access to aid and cooperation.","true",canonical_json({"model_scope":"local norm representation"})))
        for p in PEOPLE:
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(f"K-LOCAL-{p['id']}",p["id"],"PROP-LOCAL-001",0,"cultural_socialization",None,"[]","belief",.75,"ordinary",None))
        local_norms = [
            ("PROP-LOCAL-LABOR-001", "Seasonal household field work can conflict with outside or institutional labor demands.",
             ["P1","P2","P13","P14","P15","P16"]),
            ("PROP-LOCAL-RITUAL-001", "Household and communal ritual participation can carry material costs, obligations, and reputation consequences.",
             [p["id"] for p in PEOPLE]),
            ("PROP-LOCAL-TRADE-001", "Trade and credit depend on trusted counterparties, information, transport access, and remembered obligations.",
             ["P3","P4","P5","P11","P12"]),
            ("PROP-LOCAL-DISPUTE-001", "Household and economic disagreements can be negotiated privately and, where socially available, through kin, patrons, elders, compensation, or obligations before more formal escalation.",
             [p["id"] for p in PEOPLE]),
            ("PROP-LOCAL-MARRIAGE-001", "Marriage can join households and alter residence, care, property expectations, and kin relationships; exact terms must be negotiated rather than assumed universal.",
             [p["id"] for p in PEOPLE]),
            ("PROP-LOCAL-STORAGE-001", "Seasonal household produce requires processing and storage; exposed surplus can be vulnerable before it is preserved, while exact rates depend on circumstance.",
             ["P1","P2","P13","P14","P15","P16"]),
        ]
        if "ASM-FIXTURE-023" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-CARE-001",
                "Continuing kin care can require practical labor or support, and remembered care can matter in later household or property preference; exact succession consequences must be negotiated rather than assumed.",
                ["P15","P16"],
            ))
        if "ASM-FIXTURE-024" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-SOWING-001",
                "Early-rains plowing and sowing can create time-sensitive labor, tool, and draft-access needs; households without direct access may need to negotiate help.",
                ["P1","P2","P13","P14"],
            ))
        if "ASM-FIXTURE-025" in scenario.get("active_assumptions", []):
            local_norms.append((
                "PROP-LOCAL-WINTER-001",
                "Winter rain, animal care, and maintenance of agricultural assets can create household labor demands; remembered favors may be answered through bounded practical help rather than fixed-price repayment.",
                ["P1","P13"],
            ))
        if "ASM-FIXTURE-027" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-RECYCLE-001",
                "Worked metal can sometimes be repaired, remelted, recycled, or recirculated; using finished objects as feedstock sacrifices valuable output and does not recover all material.",
                ["P7","P8"],
            ))
        if "ASM-FIXTURE-028" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-ALT-METAL-001",
                "When one supplier is exhausted, trusted merchant and harbor contacts can sometimes provide information about other market opportunities, but availability and terms must be learned rather than assumed.",
                ["P3","P7","P11","P12"],
            ))
        if "ASM-FIXTURE-029" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-CRAFT-FUEL-001",
                "Metalworking depends on prepared fuel as well as metal; finite household fuel material can require dedicated preparation before casting or finishing can resume.",
                ["P7","P8"],
            ))
        if "ASM-FIXTURE-031" in active_assumptions:
            local_norms.append((
                "PROP-LOCAL-FUEL-LOGISTICS-001",
                "Workshop fuel can require gathering, hauling, preparation and negotiated labor; a porter or seasonal worker may reasonably refuse during a household labor bottleneck.",
                ["P7","P15","P16"],
            ))
        if "ASM-FIXTURE-028" in active_assumptions:
            con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
                "PROP-METAL-ALT-001",
                "A harbor-side market contact reports that Dagan-beli may be able to arrange one small raw-metal lot on delayed terms.",
                "simulation_contingent",
                canonical_json({"canonical":"fixture_market_lead","topic":"alternate_workshop_metal","provenance":"ASM-FIXTURE-028"})))
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                "K-METAL-ALT-P11","P11","PROP-METAL-ALT-001",0,"initial_scenario",None,"[]","hearsay",.66,"ordinary",None))

            con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
                "PROP-METAL-TERMS-001",
                "Dagan-beli can arrange one small fixture raw-metal lot for 0.30 silver, with 0.30 metal due after three days if the terms are accepted.",
                "simulation_contingent",
                canonical_json({"canonical":"fixture_market_terms","topic":"alternate_workshop_metal","provenance":"ASM-FIXTURE-028"})))
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                "K-METAL-TERMS-P12","P12","PROP-METAL-TERMS-001",0,"initial_scenario",None,"[]","direct",.80,"ordinary",None))

        if "ASM-FIXTURE-030" in active_assumptions:
            con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
                "PROP-METAL-DISRUPT-001",
                "Dagan-beli reports that a later small raw-metal lot is disrupted by temporary harbor/weather handling problems: 0.30 silver would now secure only 0.18 usable metal after five days.",
                "simulation_contingent",
                canonical_json({"canonical":"fixture_disrupted_market_terms","topic":"alternate_workshop_metal","provenance":"ASM-FIXTURE-030"})))
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                "K-METAL-DISRUPT-P12","P12","PROP-METAL-DISRUPT-001",0,"initial_scenario",None,"[]","direct",.82,"ordinary",None))
        if "ASM-FIXTURE-032" in active_assumptions:
            con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",(
                "PROP-METAL-NONE-001",
                "Dagan-beli reports that the same fixture market contact currently has no additional usable raw-metal lot available; the workshop must wait, recycle, or seek a genuinely new path.",
                "simulation_contingent",
                canonical_json({"canonical":"fixture_temporary_no_lot","topic":"alternate_workshop_metal","provenance":"ASM-FIXTURE-032"})))
            con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",(
                "K-METAL-NONE-P12","P12","PROP-METAL-NONE-001",0,"initial_scenario",None,"[]","direct",.84,"ordinary",None))

        for prop_id,text,people in local_norms:
            con.execute("INSERT OR REPLACE INTO propositions VALUES (?,?,?,?)",
                        (prop_id,text,"true",canonical_json({"model_scope":"research-derived local norm representation"})))
            for person_id in people:
                kid = f"K-{prop_id.replace('PROP-','')}-{person_id}"
                con.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (kid,person_id,prop_id,0,"cultural_socialization",None,"[]","belief",.75,"ordinary",None))
        con.execute("INSERT INTO events(event_id,run_id,day,event_type,model_rule_or_assumption_ids_json,payload_json) VALUES (?,?,?,?,?,?)",
                    (stable_id("EV",run_id,0,"fixture_initialized"),run_id,0,"fixture_initialized",canonical_json(["ASM-FIXTURE-001","ASM-FIXTURE-002"]),canonical_json({"households":len(HOUSEHOLDS),"persons":len(PEOPLE)})))
    return run_id
