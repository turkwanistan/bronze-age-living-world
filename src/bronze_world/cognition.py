from __future__ import annotations

import hashlib
import json
from typing import Any

from .db import WorldDB, canonical_json
from .lifeways import calendar_context


def _json(value: str) -> Any:
    return json.loads(value)


def _build_packet(db: WorldDB, job_id: str) -> dict[str, Any]:
    """Build a packet from current canonical state. Used only while sealing a new job."""
    job = db.one("SELECT * FROM cognition_jobs WHERE job_id=?", (job_id,))
    if not job:
        raise KeyError(job_id)
    actor = db.one("SELECT * FROM persons WHERE person_id=?", (job["actor_person_id"],))
    scene = db.one("SELECT * FROM scenes WHERE scene_id=?", (job["scene_id"],))
    membership = db.one("SELECT * FROM household_memberships WHERE person_id=? AND until_day IS NULL", (actor["person_id"],))
    household = db.one("SELECT * FROM households WHERE household_id=?", (membership["household_id"],))
    roles = [r[0] for r in db.all("SELECT roles.name FROM roles JOIN person_roles USING(role_id) WHERE person_roles.person_id=? AND person_roles.end_day IS NULL ORDER BY person_roles.priority", (actor["person_id"],))]
    traits = {r["trait_name"]: r["value"] for r in db.all("SELECT * FROM character_traits WHERE person_id=? ORDER BY trait_name", (actor["person_id"],))}
    resources = {r["resource_type"]: {"amount":r["amount"],"unit":r["unit_label"]} for r in db.all("SELECT * FROM resource_stocks WHERE household_id=? ORDER BY resource_type", (household["household_id"],))}
    rels = [dict(r) for r in db.all("SELECT * FROM relationships WHERE from_person_id=? ORDER BY to_person_id", (actor["person_id"],))]
    knowledge = [dict(r) for r in db.all("SELECT k.*, p.canonical_text FROM knowledge k JOIN propositions p USING(proposition_id) WHERE k.person_id=? AND k.learned_day<=? ORDER BY k.learned_day DESC, k.knowledge_id", (actor["person_id"], scene["day"]))]
    memories = [dict(r) for r in db.all("SELECT * FROM memories WHERE person_id=? ORDER BY salience DESC, created_day DESC LIMIT 12", (actor["person_id"],))]
    institution_ids = _json(scene["institution_ids_json"])
    institutions = [dict(db.one("SELECT * FROM institutions WHERE institution_id=?", (iid,))) for iid in institution_ids if db.one("SELECT * FROM institutions WHERE institution_id=?", (iid,))]
    obligations = [dict(r) for r in db.all("SELECT * FROM obligations WHERE status IN ('active','scheduled','granted') AND (obligor_person_id=? OR beneficiary_person_id=? OR obligor_household_id=? OR beneficiary_household_id=?) ORDER BY COALESCE(due_day,999999),obligation_id", (actor["person_id"],actor["person_id"],household["household_id"],household["household_id"]))]
    debts = [dict(r) for r in db.all("SELECT * FROM debts WHERE status='open' AND (debtor_household_id=? OR creditor_household_id=?) ORDER BY COALESCE(due_day,999999)", (household["household_id"],household["household_id"]))]
    marriages: list[dict[str, Any]] = []
    kinship_edges: list[dict[str, Any]] = []
    if db.schema_version() >= 2:
        marriages = [dict(r) for r in db.all(
            "SELECT * FROM marriages WHERE run_id=? AND status='active' AND (person_a_id=? OR person_b_id=?) ORDER BY marriage_id",
            (job["run_id"], actor["person_id"], actor["person_id"]),
        )]
        kinship_edges = [dict(r) for r in db.all(
            "SELECT * FROM kinship_edges WHERE run_id=? AND end_day IS NULL AND (person_a_id=? OR person_b_id=?) ORDER BY kinship_edge_id",
            (job["run_id"], actor["person_id"], actor["person_id"]),
        )]
    scenario_row = db.one(
        "SELECT s.config_json FROM scenarios s JOIN runs r ON r.scenario_id=s.scenario_id WHERE r.run_id=? ORDER BY s.scenario_version DESC LIMIT 1",
        (job["run_id"],),
    )
    start_doy = 120
    if scenario_row:
        try:
            start_doy = int(_json(scenario_row[0]).get("calendar", {}).get("start_day_of_year", 120))
        except (TypeError, ValueError):
            start_doy = 120
    seasonal = calendar_context(int(scene["day"]), start_day_of_year=start_doy)
    packet = {
        "protocol_version": job["protocol_version"],
        "job_id": job_id,
        "run_id": job["run_id"],
        "scene": {"scene_id":scene["scene_id"],"day":scene["day"],"place_id":scene["place_id"],"family":scene["scene_family"],"trigger":scene["trigger_type"],"stakes":_json(scene["stakes_json"]),"material_constraints":_json(scene["material_constraints_json"]),"social_constraints":_json(scene["social_constraints_json"])},
        "actor": {"person_id":actor["person_id"],"display_name":actor["display_name"],"age":actor["age"],"life_stage":actor["life_stage"],"legal_status":actor["legal_status"],"current_place_id":actor["current_place_id"],"beliefs":_json(actor["beliefs_json"]),"goals":_json(actor["goals_json"]),"roles":roles,"traits":traits},
        "household": {
            "household_id":household["household_id"],
            "name":household["name"],
            "status":_json(household["status_json"]),
            "resources":resources,
            "routine_expectations": {
                "daily_grain_need": household["fixture_daily_food_need"],
                "weekly_grain_receipt": household["fixture_weekly_receipt"],
                "next_weekly_receipt_day": ((int(scene["day"]) // 7) + 1) * 7,
                "notice": "Deterministic fixture routine under ASM-FIXTURE-002; not a historical ration/wage claim."
            },
            "fixture_notice":household["fixture_notice"]
        },
        "relationships": rels,
        "admissible_knowledge": knowledge,
        "relevant_memories": memories,
        "active_obligations": obligations,
        "active_debts": debts,
        "active_marriages": marriages,
        "kinship_edges": kinship_edges,
        "available_institutions": institutions,
        "seasonal_context": seasonal,
        "allowed_actions": _json(job["allowed_actions_json"]),
        "containment_rule": "Reason only from this packet. Do not use external/web/future-history facts. Cite decisive knowledge/belief IDs from admissible_knowledge.",
    }
    return packet


def compile_packet(db: WorldDB, job_id: str) -> dict[str, Any]:
    """Return the immutable packet sealed when the cognition job was created.

    A pending/rejected/accepted job must never be recompiled from later world state;
    doing so would leak future material, relationship, memory, or obligation state.
    """
    job = db.one("SELECT * FROM cognition_jobs WHERE job_id=?", (job_id,))
    if not job:
        raise KeyError(job_id)
    if job["status"] == "compiling":
        return _build_packet(db, job_id)
    packet = json.loads(job["packet_json"])
    expected = job["packet_hash"]
    if not expected or expected != packet_hash(packet):
        raise ValueError(f"sealed packet hash mismatch for {job_id}")
    return packet


def packet_hash(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(packet).encode("utf-8")).hexdigest()
