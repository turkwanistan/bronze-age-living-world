from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any

from .cognition import _build_packet, packet_hash
from .db import WorldDB, canonical_json
from .ids import stable_id
from .provisioning import effective_household_provisioning, scenario_config, scenario_has_assumption
from .lifeways import (
    calendar_context, communal_feast_due, household_ritual_due, palace_labor_cycle_due,
    role_activity, weekly_cycle_due,
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


class WorldEngine:
    def __init__(self, db: WorldDB, run_id: str):
        self.db = db
        self.run_id = run_id

    @property
    def day(self) -> int:
        row = self.db.one("SELECT current_day FROM runs WHERE run_id=?", (self.run_id,))
        if not row:
            raise KeyError(self.run_id)
        return int(row[0])

    def _household_for_person(self, person_id: str) -> str | None:
        row = self.db.one(
            "SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL ORDER BY since_day DESC LIMIT 1",
            (person_id,),
        )
        return None if not row else str(row[0])

    def _direct_message_route(self, originator: str, recipient: str):
        origin = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (originator,))
        target = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (recipient,))
        if not origin or not target or not origin["alive"] or not target["alive"] or not target["available"]:
            return None
        if origin["current_place_id"] == target["current_place_id"]:
            return None
        return self.db.one(
            "SELECT route_id,from_place_id,to_place_id,travel_days,mode FROM routes "
            "WHERE from_place_id=? AND to_place_id=? AND accessible=1 "
            "ORDER BY travel_days,route_id LIMIT 1",
            (origin["current_place_id"], target["current_place_id"]),
        )

    def _event(
        self,
        con,
        day: int,
        event_type: str,
        *,
        scene_id: str | None = None,
        decision_id: str | None = None,
        actors: list[str] | None = None,
        causes: list[str] | None = None,
        knowledge: list[str] | None = None,
        rules: list[str] | None = None,
        material: dict | None = None,
        relationships: dict | None = None,
        institutions: dict | None = None,
        payload: dict | None = None,
        discriminator: str = "",
    ) -> str:
        seq_hint = con.execute("SELECT COALESCE(MAX(event_seq),0)+1 FROM events").fetchone()[0]
        eid = stable_id("EV", self.run_id, day, event_type, seq_hint, discriminator)
        con.execute(
            "INSERT INTO events(event_id,run_id,day,event_type,scene_id,decision_id,actor_ids_json,causing_event_ids_json,knowledge_or_belief_ids_json,model_rule_or_assumption_ids_json,material_deltas_json,relationship_deltas_json,institutional_deltas_json,payload_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                self.run_id,
                day,
                event_type,
                scene_id,
                decision_id,
                canonical_json(actors or []),
                canonical_json(causes or []),
                canonical_json(knowledge or []),
                canonical_json(rules or []),
                canonical_json(material or {}),
                canonical_json(relationships or {}),
                canonical_json(institutions or {}),
                canonical_json(payload or {}),
            ),
        )
        return eid

    def _memory(self, con, person_id: str, day: int, summary: str, *, event_id: str | None = None,
                memory_type: str = "social_event", emotional_weight: float = .5,
                salience: float = .65, relationship_relevance: float = .5,
                goal_relevance: float = .5, provenance: dict | None = None) -> str:
        mid = stable_id("MEM", self.run_id, person_id, day, memory_type, summary, event_id or "")
        con.execute(
            "INSERT OR IGNORE INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (mid, person_id, memory_type, summary, event_id, day, emotional_weight, salience,
             relationship_relevance, goal_relevance, canonical_json(provenance or {})),
        )
        return mid

    def _ensure_relationship_pair(self, con, person_a: str, person_b: str, *, relationship_type: str = "exchange_contact") -> None:
        """Create a modest first-contact relationship only when a consequential interaction requires one."""
        for from_person,to_person in ((person_a,person_b),(person_b,person_a)):
            rid = stable_id("REL", from_person, to_person)
            con.execute(
                "INSERT OR IGNORE INTO relationships("
                "relationship_id,from_person_id,to_person_id,relationship_type,kin_degree,affection,trust,fear,respect,"
                "status_difference,favors_given,favors_owed,conflicts,attributes_json,last_contact_day"
                ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid,from_person,to_person,relationship_type,None,.45,.55,.03,.55,0.0,0.0,0.0,0,
                 canonical_json({"origin":"first consequential exchange interaction"}),self.day),
            )

    def _adjust_relationship(self, con, from_person: str, to_person: str, *, trust: float = 0,
                             respect: float = 0, favors_given: float = 0, favors_owed: float = 0,
                             conflicts: int = 0) -> dict[str, float]:
        row = con.execute(
            "SELECT trust,respect,favors_given,favors_owed,conflicts FROM relationships WHERE from_person_id=? AND to_person_id=?",
            (from_person, to_person),
        ).fetchone()
        if not row:
            return {}
        new_trust = max(0.0, min(1.0, float(row[0]) + trust))
        new_respect = max(0.0, min(1.0, float(row[1]) + respect))
        con.execute(
            "UPDATE relationships SET trust=?,respect=?,favors_given=favors_given+?,favors_owed=favors_owed+?,"
            "conflicts=MAX(0,conflicts+?),last_contact_day=? WHERE from_person_id=? AND to_person_id=?",
            (new_trust, new_respect, favors_given, favors_owed, int(conflicts), self.day, from_person, to_person),
        )
        return {"trust": new_trust, "respect": new_respect, "favors_given_delta": favors_given,
                "favors_owed_delta": favors_owed, "conflicts_delta": int(conflicts)}

    def _active_household_reserve_floor(self, household_id: str, resource: str) -> float | None:
        rows = self.db.all(
            "SELECT provenance_json FROM obligations WHERE status='active' "
            "AND obligation_type='household_reserve_commitment' AND obligor_household_id=? ORDER BY obligation_id",
            (household_id,),
        )
        floors: list[float] = []
        for row in rows:
            try:
                provenance = json.loads(row["provenance_json"])
            except json.JSONDecodeError:
                continue
            if provenance.get("resource") == resource and isinstance(provenance.get("reserve_floor"), (int, float)):
                floors.append(float(provenance["reserve_floor"]))
        return max(floors) if floors else None

    def _calendar_start_day_of_year(self) -> int:
        row = self.db.one(
            "SELECT s.config_json FROM scenarios s JOIN runs r ON r.scenario_id=s.scenario_id "
            "WHERE r.run_id=? ORDER BY s.scenario_version DESC LIMIT 1",
            (self.run_id,),
        )
        if not row:
            return 120
        try:
            return int(json.loads(row[0]).get("calendar", {}).get("start_day_of_year", 120))
        except (TypeError, ValueError, json.JSONDecodeError):
            return 120

    def _seasonal_context(self, day: int) -> dict[str, Any]:
        return calendar_context(day, start_day_of_year=self._calendar_start_day_of_year())

    def _v006_start_day(self) -> int:
        row = self.db.one(
            "SELECT s.config_json FROM scenarios s JOIN runs r ON r.scenario_id=s.scenario_id "
            "WHERE r.run_id=? ORDER BY s.scenario_version DESC LIMIT 1",
            (self.run_id,),
        )
        if not row:
            return 141
        try:
            return int(json.loads(row[0]).get("v006_lifeways_start_day", 141))
        except (TypeError, ValueError, json.JSONDecodeError):
            return 141


    def _v007_start_day(self) -> int:
        cfg = scenario_config(self.db, self.run_id)
        try:
            return int(cfg.get("v007_lifeways_start_day", 181))
        except (TypeError, ValueError):
            return 181

    def _v009_start_day(self) -> int:
        cfg = scenario_config(self.db, self.run_id)
        try:
            return int(cfg.get("v009_lifeways_start_day", 361))
        except (TypeError, ValueError):
            return 361

    def _v008_start_day(self) -> int:
        cfg = scenario_config(self.db, self.run_id)
        try:
            return int(cfg.get("v008_lifeways_start_day", 241))
        except (TypeError, ValueError):
            return 241

    def _has_assumption(self, assumption_id: str) -> bool:
        return scenario_has_assumption(self.db, self.run_id, assumption_id)

    def _is_unmarried(self, person_id: str) -> bool:
        if self.db.schema_version() < 2:
            return True
        return not bool(self.db.one(
            "SELECT 1 FROM marriages WHERE run_id=? AND status='active' AND (person_a_id=? OR person_b_id=?)",
            (self.run_id, person_id, person_id),
        ))

    def _next_lower_agricultural_intensity_day(self, day: int, *, threshold: float = 0.85) -> int:
        """Find the next calendar day whose modeled agricultural intensity is below threshold.

        This intentionally walks the scenario calendar rather than assuming every labor
        bottleneck ends at the cereal-harvest boundary. Exact phase lengths remain
        ASM-FIXTURE-008 calibration.
        """
        for offset in range(1, 361):
            if float(self._seasonal_context(day + offset)["agricultural_intensity"]) < float(threshold):
                return day + offset
        raise RuntimeError("seasonal_calendar_has_no_lower_intensity_day")

    def _change_resource(self, con, household_id: str, resource: str, delta: float, *, assumption_id: str) -> float:
        row = con.execute(
            "SELECT amount,unit_label FROM resource_stocks WHERE household_id=? AND resource_type=?",
            (household_id, resource),
        ).fetchone()
        current = float(row["amount"]) if row else 0.0
        new_amount = current + float(delta)
        if new_amount < -1e-9:
            raise ValueError(f"negative resource transition:{household_id}:{resource}:{current}:{delta}")
        new_amount = max(0.0, new_amount)
        if row:
            con.execute(
                "UPDATE resource_stocks SET amount=? WHERE household_id=? AND resource_type=?",
                (new_amount, household_id, resource),
            )
        else:
            con.execute(
                "INSERT INTO resource_stocks VALUES (?,?,?,?,?)",
                (household_id, resource, new_amount, "abstract_fixture_unit", assumption_id),
            )
        return new_amount

    def _apply_recurring_lifeways(self, con, day: int) -> None:
        """Apply routine work/religion/port/institution cycles without cognition.

        The shape of work is research-constrained; exact cadence and quantities are
        explicitly fixture calibration. Consequential conflicts are detected after the
        transaction and become sealed cognition jobs rather than being resolved here.
        """
        seasonal = self._seasonal_context(day)

        if self._has_assumption("ASM-FIXTURE-024"):
            draft_due = con.execute(
                "SELECT * FROM obligations WHERE status='scheduled' AND obligation_type='fixture_draft_team_service' "
                "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
                (day,),
            ).fetchall()
            for o in draft_due:
                beneficiary = o["beneficiary_household_id"]
                holder = o["obligor_household_id"]
                provenance=json.loads(o["provenance_json"])
                progress=float(provenance.get("service_sowing_progress",0.10))
                opportunity_cost=float(provenance.get("access_holder_opportunity_cost_progress",0.05))
                self._change_resource(con, beneficiary, "sowing_progress", progress, assumption_id="ASM-FIXTURE-024")
                holder_stock=con.execute("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='sowing_progress'",(holder,)).fetchone() if holder else None
                actual_cost=min(float(holder_stock[0]),opportunity_cost) if holder_stock else 0.0
                if holder and actual_cost>0:
                    self._change_resource(con,holder,"sowing_progress",-actual_cost,assumption_id="ASM-FIXTURE-024")
                con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (o["obligation_id"],))
                material={beneficiary:{"sowing_progress":progress}}
                if holder and actual_cost>0: material[holder]={"sowing_progress":-actual_cost}
                eid = self._event(
                    con, day, "draft_team_service_completed", actors=[x for x in [o["obligor_person_id"],o["beneficiary_person_id"]] if x],
                    rules=["ASM-FIXTURE-024","RULE-SOWING-DRAFT-ACCESS-001"],
                    material=material,
                    payload={"obligation_id":o["obligation_id"],"beneficiary_household_id":beneficiary,
                             "sowing_progress":progress,"access_holder_opportunity_cost_progress":actual_cost,
                             "notice":"fixture service/progress transfer, not a historical plowing rate"},
                    discriminator=o["obligation_id"],
                )
                if o["beneficiary_person_id"]:
                    self._memory(con,o["beneficiary_person_id"],day,"Received the negotiated draft-team service during the sowing window.",
                                 event_id=eid,memory_type="agricultural_access",salience=.82,relationship_relevance=.82,goal_relevance=.9,
                                 provenance={"assumption_id":"ASM-FIXTURE-024"})
                if o["obligor_person_id"]:
                    self._memory(con,o["obligor_person_id"],day,"Provided the negotiated draft-team service to the dependent field household.",
                                 event_id=eid,memory_type="agricultural_access",salience=.72,relationship_relevance=.78,goal_relevance=.62,
                                 provenance={"assumption_id":"ASM-FIXTURE-024"})

        if self._has_assumption("ASM-FIXTURE-025"):
            winter_help_due = con.execute(
                "SELECT * FROM obligations WHERE status='scheduled' AND obligation_type='fixture_winter_reciprocal_labor' "
                "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
                (day,),
            ).fetchall()
            for o in winter_help_due:
                provenance=json.loads(o["provenance_json"])
                household_id=o["beneficiary_household_id"] or "H-FARM"
                row=con.execute("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='draft_team_condition'",(household_id,)).fetchone()
                current=float(row[0]) if row else 0.0
                requested_restore=float(provenance.get("condition_restore",0.15))
                restored=max(0.0,min(requested_restore,1.0-current))
                if restored>0:
                    self._change_resource(con,household_id,"draft_team_condition",restored,assumption_id="ASM-FIXTURE-025")
                con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?",(o["obligation_id"],))
                helper=o["obligor_person_id"]
                beneficiary=o["beneficiary_person_id"]
                relationship_delta={}
                if helper and beneficiary:
                    relationship_delta[f"{helper}->{beneficiary}"]=self._adjust_relationship(con,helper,beneficiary,trust=.02,respect=.01,favors_owed=-1)
                    relationship_delta[f"{beneficiary}->{helper}"]=self._adjust_relationship(con,beneficiary,helper,trust=.02,respect=.01,favors_given=-1)
                eid=self._event(
                    con,day,"winter_reciprocal_labor_completed",actors=[x for x in [helper,beneficiary] if x],
                    rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],
                    material={household_id:{"draft_team_condition":restored}} if restored else {},
                    relationships=relationship_delta,
                    payload={"obligation_id":o["obligation_id"],"condition_restored":restored,
                             "notice":"bounded reciprocal labor fixture; no fixed historical exchange equivalence"},
                    discriminator=o["obligation_id"],
                )
                if helper:
                    self._memory(con,helper,day,"Completed the bounded winter maintenance help requested in return for earlier sowing-season assistance.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.84,relationship_relevance=.9,goal_relevance=.72,
                                 provenance={"assumption_id":"ASM-FIXTURE-025"})
                if beneficiary:
                    self._memory(con,beneficiary,day,"Received the agreed winter maintenance help; the earlier sowing favor is now answered.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.82,relationship_relevance=.9,goal_relevance=.76,
                                 provenance={"assumption_id":"ASM-FIXTURE-025"})

        # Resolve a v009 alternate raw-metal exchange only after its modeled market delay.
        # Silver was transferred to the intermediary household when terms were accepted;
        # the metal enters H-CRAFT here from the external fixture lot, not from hidden stock.
        if self._has_assumption("ASM-FIXTURE-028"):
            alt_due = con.execute(
                "SELECT * FROM obligations WHERE status='scheduled' AND obligation_type='fixture_alternate_metal_exchange' "
                "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
                (day,),
            ).fetchall()
            for o in alt_due:
                provenance = json.loads(o["provenance_json"])
                amount = float(provenance.get("metal_amount", 0.0))
                target_household = o["beneficiary_household_id"]
                if target_household and amount > 0:
                    self._change_resource(con,target_household,"metal",amount,assumption_id="ASM-FIXTURE-028")
                con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?",(o["obligation_id"],))
                eid=self._event(
                    con,day,"alternate_metal_exchange_completed",actors=[x for x in [o["obligor_person_id"],o["beneficiary_person_id"]] if x],
                    rules=["ASM-FIXTURE-028","RULE-ALTERNATE-METAL-SOURCING-001"],
                    material={target_household:{"metal":amount}} if target_household and amount else {},
                    payload={"obligation_id":o["obligation_id"],"metal_amount":amount,
                             "notice":"fixture external market lot delivered after modeled delay; not a historical shipment or price"},
                    discriminator=o["obligation_id"],
                )
                if o["beneficiary_person_id"]:
                    self._memory(con,o["beneficiary_person_id"],day,
                        f"The alternate market exchange completed and brought {amount:g} metal in fixture units after the agreed delay.",
                        event_id=eid,memory_type="trade",salience=.88,relationship_relevance=.72,goal_relevance=.95,
                        provenance={"assumption_id":"ASM-FIXTURE-028"})

        # Resolve scheduled external trade exchanges. Silver left the household when the
        # commitment was made; imported trade goods appear only after the modeled delay.
        trade_due = con.execute(
            "SELECT * FROM obligations WHERE status='scheduled' AND obligation_type='fixture_trade_exchange' "
            "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
            (day,),
        ).fetchall()
        for o in trade_due:
            provenance = json.loads(o["provenance_json"])
            goods = float(provenance.get("trade_goods_amount", 0.0))
            household_id = o["obligor_household_id"]
            if household_id and goods > 0:
                self._change_resource(con, household_id, "trade_goods", goods, assumption_id="ASM-FIXTURE-012")
            con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (o["obligation_id"],))
            eid = self._event(
                con, day, "fixture_trade_exchange_completed", actors=[o["obligor_person_id"]] if o["obligor_person_id"] else [],
                rules=["ASM-FIXTURE-012", "RULE-PORT-TRADE-CYCLE-001"],
                material={household_id: {"trade_goods": goods}} if household_id and goods else {},
                payload={"obligation_id": o["obligation_id"], "trade_goods_amount": goods,
                         "notice": "abstract external exchange; no historical price/profit rate claimed"},
                discriminator=o["obligation_id"],
            )
            if o["obligor_person_id"]:
                self._memory(
                    con, o["obligor_person_id"], day,
                    f"The committed port exchange completed and brought {goods:g} trade_goods in fixture units.",
                    event_id=eid, memory_type="trade", salience=.7, relationship_relevance=.35, goal_relevance=.8,
                    provenance={"assumption_id": "ASM-FIXTURE-012"},
                )

        # A postponed palace labor request becomes routine once the intense agricultural
        # bottleneck has passed. It remains an institutional obligation, not a magical
        # disappearance of state demands.
        if seasonal["agricultural_intensity"] < 0.85:
            palace_due = con.execute(
                "SELECT * FROM obligations WHERE status='active' AND obligation_type='palace_labor' "
                "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
                (day,),
            ).fetchall()
            for o in palace_due:
                con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (o["obligation_id"],))
                eid = self._event(
                    con, day, "palace_labor_completed", actors=[o["obligor_person_id"]] if o["obligor_person_id"] else [],
                    rules=["ASM-FIXTURE-011", "RULE-SEASONAL-LABOR-CONFLICT-001"],
                    institutions={"I-PALACE": {"labor_obligation": "fulfilled"}},
                    payload={"obligation_id": o["obligation_id"], "seasonal_context": seasonal,
                             "notice": "service cadence/duration are fixture mechanics; not a historical corvee rate"},
                    discriminator=o["obligation_id"],
                )
                if o["obligor_person_id"]:
                    self._memory(con, o["obligor_person_id"], day, "Completed the recorded palace labor obligation after the seasonal bottleneck.",
                                 event_id=eid, memory_type="institutional_labor", salience=.7, relationship_relevance=.2, goal_relevance=.75,
                                 provenance={"assumption_id": "ASM-FIXTURE-011"})

        if weekly_cycle_due(day):
            people = con.execute(
                "SELECT p.person_id,p.display_name,hm.household_id FROM persons p "
                "JOIN household_memberships hm USING(person_id) WHERE p.alive=1 AND p.available=1 AND hm.until_day IS NULL "
                "ORDER BY p.person_id"
            ).fetchall()
            household_work: dict[str, list[dict[str, Any]]] = {}
            for person in people:
                roles = [r[0] for r in con.execute(
                    "SELECT roles.name FROM roles JOIN person_roles USING(role_id) "
                    "WHERE person_roles.person_id=? AND person_roles.end_day IS NULL ORDER BY person_roles.priority",
                    (person["person_id"],),
                ).fetchall()]
                activities = [{"role": role, **role_activity(role, seasonal)} for role in roles]
                household_work.setdefault(person["household_id"], []).append(
                    {"person_id": person["person_id"], "roles": roles, "activities": activities}
                )
                material: dict[str, Any] = {}
                # Material specialist chains: no free textiles or metalwork.
                if "textile_worker" in roles:
                    fiber = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='fiber'",
                        (person["household_id"],),
                    ).fetchone()
                    if fiber and float(fiber[0]) >= 0.12:
                        self._change_resource(con, person["household_id"], "fiber", -0.12, assumption_id="ASM-FIXTURE-009")
                        self._change_resource(con, person["household_id"], "textile_goods", 0.08, assumption_id="ASM-FIXTURE-009")
                        material = {person["household_id"]: {"fiber": -0.12, "textile_goods": 0.08}}
                if "metal_craft_worker" in roles:
                    metal = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='metal'",
                        (person["household_id"],),
                    ).fetchone()
                    charcoal = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='charcoal'",
                        (person["household_id"],),
                    ).fetchone()
                    if metal and charcoal and float(metal[0]) >= 0.15 and float(charcoal[0]) >= 0.20:
                        self._change_resource(con, person["household_id"], "metal", -0.15, assumption_id="ASM-FIXTURE-009")
                        self._change_resource(con, person["household_id"], "charcoal", -0.20, assumption_id="ASM-FIXTURE-009")
                        self._change_resource(con, person["household_id"], "finished_metalwork", 0.08, assumption_id="ASM-FIXTURE-009")
                        material = {person["household_id"]: {"metal": -0.15, "charcoal": -0.20, "finished_metalwork": 0.08}}
                elif "recognized_craft_worker" in roles:
                    metal = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='metal'",
                        (person["household_id"],),
                    ).fetchone()
                    charcoal = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='charcoal'",
                        (person["household_id"],),
                    ).fetchone()
                    if metal and charcoal and float(metal[0]) >= 0.08 and float(charcoal[0]) >= 0.10:
                        self._change_resource(con, person["household_id"], "metal", -0.08, assumption_id="ASM-FIXTURE-017")
                        self._change_resource(con, person["household_id"], "charcoal", -0.10, assumption_id="ASM-FIXTURE-017")
                        self._change_resource(con, person["household_id"], "finished_metalwork", 0.04, assumption_id="ASM-FIXTURE-017")
                        material = {person["household_id"]: {"metal": -0.08, "charcoal": -0.10, "finished_metalwork": 0.04}}
                if (day >= self._v006_start_day()
                        and seasonal["phase"] == "grape_olive_and_field_preparation"
                        and any(r in roles for r in ("farmer", "dependent_field_worker"))):
                    produced = 0.12
                    self._change_resource(con, person["household_id"], "seasonal_produce", produced, assumption_id="ASM-FIXTURE-021")
                    material.setdefault(person["household_id"], {})["seasonal_produce"] = (
                        material.setdefault(person["household_id"], {}).get("seasonal_produce", 0.0) + produced
                    )
                if (self._has_assumption("ASM-FIXTURE-024") and day >= self._v007_start_day()
                        and seasonal["phase"] == "early_rains_and_sowing"
                        and any(r in roles for r in ("farmer", "dependent_field_worker"))):
                    sowing = 0.10 if "farmer" in roles else 0.05
                    self._change_resource(con, person["household_id"], "sowing_progress", sowing, assumption_id="ASM-FIXTURE-024")
                    material.setdefault(person["household_id"], {})["sowing_progress"] = (
                        material.setdefault(person["household_id"], {}).get("sowing_progress", 0.0) + sowing
                    )
                self._event(
                    con, day, "occupation_work_cycle", actors=[person["person_id"]],
                    rules=["ASM-FIXTURE-008", "ASM-FIXTURE-009", "RULE-OCCUPATION-WORKFLOW-001"],
                    material=material,
                    payload={"roles": roles, "activities": activities, "seasonal_context": seasonal},
                    discriminator=person["person_id"],
                )
            for household_id, allocations in sorted(household_work.items()):
                self._event(
                    con, day, "household_labor_allocation", rules=["ASM-FIXTURE-008", "RULE-HOUSEHOLD-LABOR-ALLOCATION-001"],
                    payload={"household_id": household_id, "seasonal_context": seasonal, "allocations": allocations},
                    discriminator=household_id,
                )

            if (self._has_assumption("ASM-FIXTURE-025") and day >= self._v008_start_day()
                    and seasonal["phase"] == "wet_winter_growth"):
                maintained=con.execute(
                    "SELECT 1 FROM events WHERE run_id=? AND event_type IN ('winter_reciprocal_labor_completed','winter_maintenance_handled_internally') LIMIT 1",
                    (self.run_id,),
                ).fetchone()
                row=con.execute("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='draft_team_condition'").fetchone()
                if row and not maintained:
                    current=float(row[0])
                    loss=min(current,0.05)
                    if loss>0:
                        self._change_resource(con,"H-FARM","draft_team_condition",-loss,assumption_id="ASM-FIXTURE-025")
                        self._event(
                            con,day,"winter_draft_team_condition_cycle",actors=["P1"],
                            rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],
                            material={"H-FARM":{"draft_team_condition":-loss}},
                            payload={"seasonal_context":seasonal,"condition_loss":loss,
                                     "notice":"abstract first-winter maintenance pressure; not an animal-health or foddering rate"},
                            discriminator="H-FARM",
                        )

            # A port is an occupational interface every week, even when no dramatic ship
            # event happens. No cargo outcome or foreign partner is invented here.
            self._event(
                con, day, "port_market_cycle", actors=["P3", "P5", "P11", "P12"],
                rules=["ASM-FIXTURE-012", "RULE-PORT-TRADE-CYCLE-001"],
                institutions={"I-MARKET": {"routine_exchange": True}},
                payload={"seasonal_context": seasonal,
                         "activities": ["cargo/porter coordination", "market exchange", "accounting/records", "harbor information brokerage"],
                         "notice": "recurring Ugaritic port-work model; exact transaction volume is unspecified"},
                discriminator="weekly-port",
            )

        if day >= self._v006_start_day() and day % 30 == 0:
            exposed = con.execute(
                "SELECT household_id,amount FROM resource_stocks WHERE resource_type='seasonal_produce' AND amount>0 ORDER BY household_id"
            ).fetchall()
            for row in exposed:
                loss = float(row["amount"]) * 0.05
                if loss <= 0:
                    continue
                self._change_resource(con, row["household_id"], "seasonal_produce", -loss, assumption_id="ASM-FIXTURE-021")
                self._event(
                    con, day, "seasonal_storage_loss", rules=["ASM-FIXTURE-021", "RULE-SEASONAL-SURPLUS-STORAGE-001"],
                    material={row["household_id"]: {"seasonal_produce": -loss}},
                    payload={"household_id": row["household_id"], "loss_fraction": 0.05,
                             "notice": "storage-loss fraction is engineering calibration, not a historical spoilage rate"},
                    discriminator=row["household_id"],
                )

        if household_ritual_due(day):
            households = con.execute("SELECT household_id FROM households ORDER BY household_id").fetchall()
            for h in households:
                stock = con.execute(
                    "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='ritual_goods'",
                    (h["household_id"],),
                ).fetchone()
                if not stock or float(stock[0]) < 0.05:
                    continue
                self._change_resource(con, h["household_id"], "ritual_goods", -0.05, assumption_id="ASM-FIXTURE-010")
                senior = con.execute(
                    "SELECT p.person_id FROM persons p JOIN household_memberships hm USING(person_id) "
                    "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 "
                    "ORDER BY CASE hm.membership_role WHEN 'senior' THEN 0 ELSE 1 END,p.person_id LIMIT 1",
                    (h["household_id"],),
                ).fetchone()
                actors = [senior[0]] if senior else []
                eid = self._event(
                    con, day, "household_ritual_observance", actors=actors,
                    rules=["ASM-FIXTURE-010", "ASM-UGA-003", "RULE-RECURRING-HOUSEHOLD-RITUAL-001"],
                    material={h["household_id"]: {"ritual_goods": -0.05}}, institutions={"I-SHRINE": {"household_cult": "observed"}},
                    payload={"household_id": h["household_id"], "seasonal_context": seasonal,
                             "notice": "recurring observance/cost cadence is fixture calibration; household religion itself is research-supported"},
                    discriminator=h["household_id"],
                )
                if senior:
                    self._memory(con, senior[0], day, "My household maintained its ordinary ritual observance.", event_id=eid,
                                 memory_type="ritual_household", salience=.42, relationship_relevance=.15, goal_relevance=.45,
                                 provenance={"assumption_id": "ASM-FIXTURE-010"})

        if communal_feast_due(day, start_day_of_year=self._calendar_start_day_of_year()):
            self._event(
                con, day, "communal_feast_calendar_due", actors=["P9", "P10"],
                rules=["ASM-FIXTURE-010", "RULE-COMMUNAL-FEAST-001"],
                institutions={"I-SHRINE": {"communal_feast": "due"}},
                payload={"seasonal_context": seasonal,
                         "notice": "communal ritual/feasting is research-supported; exact date/contribution scale are fixture calibration"},
                discriminator="communal-feast",
            )

        if palace_labor_cycle_due(day):
            existing = con.execute(
                "SELECT 1 FROM obligations WHERE obligation_type='palace_labor' AND json_extract(provenance_json,'$.cycle_day')=?",
                (day,),
            ).fetchone()
            if not existing:
                oid = stable_id("O", self.run_id, "palace_labor", "P13", day)
                con.execute(
                    "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (oid, "P13", "H-DEPEND", None, None, "palace_labor",
                     "Palace administrative labor request recorded for Arhalbu's household.", day, "active",
                     canonical_json({"assumption_id": "ASM-FIXTURE-011", "institution_id": "I-PALACE", "cycle_day": day,
                                     "notice": "cadence/duration are fixture mechanics, not a historical corvee rate"})),
                )
                self._event(
                    con, day, "palace_labor_requested", actors=["P13"],
                    rules=["ASM-FIXTURE-011", "RULE-SEASONAL-LABOR-CONFLICT-001"],
                    institutions={"I-PALACE": {"labor_request": "issued"}},
                    payload={"obligation_id": oid, "seasonal_context": seasonal,
                             "notice": "institutional labor is research-supported; exact request cadence is fixture calibration"},
                    discriminator=oid,
                )

    def advance(self, days: int, *, allow_unresolved: bool = False) -> int:
        """Advance up to ``days`` while no cognition job is unresolved.

        Normal simulation time stops at a cognition boundary. ``allow_unresolved`` is
        diagnostic-only and exists for deterministic subsystem tests; it must not be
        used for an accepted living-world run.
        """
        if days < 0:
            raise ValueError("days must be non-negative")
        advanced = 0
        run = self.db.one("SELECT rng_seed,current_day FROM runs WHERE run_id=?", (self.run_id,))
        seed = int(run["rng_seed"])
        for _ in range(days):
            unresolved = self.db.scalar(
                "SELECT COUNT(*) FROM cognition_jobs WHERE run_id=? AND status IN ('pending','rejected')",
                (self.run_id,),
            )
            if unresolved and not allow_unresolved:
                break
            target_day = self.day + 1
            rng = random.Random(f"{seed}:{target_day}:routine")
            with self.db.transaction() as con:
                for h in con.execute("SELECT household_id FROM households ORDER BY household_id").fetchall():
                    provisioning = effective_household_provisioning(self.db, self.run_id, h["household_id"])
                    stock = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='grain'",
                        (h["household_id"],),
                    ).fetchone()[0]
                    daily_need = float(provisioning["daily_need"])
                    consume = min(float(stock), daily_need)
                    con.execute(
                        "UPDATE resource_stocks SET amount=amount-? WHERE household_id=? AND resource_type='grain'",
                        (consume, h["household_id"]),
                    )
                    routine_rules=["ASM-FIXTURE-002"] + (["ASM-FIXTURE-022","RULE-COMPOSITION-NEUTRAL-PROVISIONING-001"] if provisioning["mode"] == "composition_neutral_per_person_share" else [])
                    consumption_payload={"notice":"abstract fixture unit"}
                    if provisioning["mode"] == "composition_neutral_per_person_share":
                        consumption_payload.update({"effective_daily_need":daily_need,"provisioning_mode":provisioning["mode"]})
                    self._event(
                        con, target_day, "routine_consumption", rules=routine_rules,
                        material={h["household_id"]: {"grain": -consume}},
                        payload=consumption_payload, discriminator=h["household_id"],
                    )
                    if target_day % 7 == 0:
                        receipt = float(provisioning["weekly_receipt"])
                        con.execute(
                            "UPDATE resource_stocks SET amount=amount+? WHERE household_id=? AND resource_type='grain'",
                            (receipt, h["household_id"]),
                        )
                        receipt_payload={"notice":"abstract fixture unit"}
                        if provisioning["mode"] == "composition_neutral_per_person_share":
                            receipt_payload.update({"effective_weekly_receipt":receipt,"provisioning_mode":provisioning["mode"]})
                        self._event(
                            con, target_day, "routine_weekly_receipt", rules=routine_rules,
                            material={h["household_id"]: {"grain": receipt}},
                            payload=receipt_payload, discriminator=h["household_id"],
                        )

                self._apply_recurring_lifeways(con, target_day)

                # Complete fixture outside-work commitments only after the agreed delay.
                scheduled_work = con.execute(
                    "SELECT * FROM obligations WHERE status='scheduled' AND obligation_type='fixture_outside_work' "
                    "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
                    (target_day,),
                ).fetchall()
                for o in scheduled_work:
                    provenance = json.loads(o["provenance_json"])
                    resource = provenance.get("resource", "grain")
                    amount = float(provenance.get("amount", 0))
                    household_id = o["beneficiary_household_id"] or o["obligor_household_id"]
                    if amount > 0 and household_id:
                        stock = con.execute(
                            "SELECT 1 FROM resource_stocks WHERE household_id=? AND resource_type=?",
                            (household_id, resource),
                        ).fetchone()
                        if stock:
                            con.execute(
                                "UPDATE resource_stocks SET amount=amount+? WHERE household_id=? AND resource_type=?",
                                (amount, household_id, resource),
                            )
                        else:
                            con.execute(
                                "INSERT INTO resource_stocks VALUES (?,?,?,?,?)",
                                (household_id, resource, amount, "abstract_fixture_unit", "ASM-FIXTURE-006"),
                            )
                    con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (o["obligation_id"],))
                    actors = [x for x in [o["obligor_person_id"], provenance.get("household_senior_person_id")] if x]
                    eid = self._event(
                        con, target_day, "fixture_outside_work_completed", actors=actors,
                        rules=["ASM-FIXTURE-006", "RULE-HOUSEHOLD-WORK-NEGOTIATION-001"],
                        material={household_id: {resource: amount}} if amount > 0 and household_id else {},
                        payload={"obligation_id": o["obligation_id"], "work_id": provenance.get("work_id"),
                                 "notice": "abstract fixture work receipt; not a historical wage"},
                        discriminator=o["obligation_id"],
                    )
                    if o["obligor_person_id"]:
                        self._memory(
                            con, o["obligor_person_id"], target_day,
                            f"Completed agreed outside work; my household received {amount:g} {resource} in fixture units.",
                            event_id=eid, memory_type="work", salience=.72, relationship_relevance=.55, goal_relevance=.8,
                            provenance={"assumption_id": "ASM-FIXTURE-006", "work_id": provenance.get("work_id")},
                        )
                    senior = provenance.get("household_senior_person_id")
                    if senior:
                        self._memory(
                            con, senior, target_day,
                            f"{o['obligor_person_id']} completed the agreed outside work; the household received {amount:g} {resource} in fixture units.",
                            event_id=eid, memory_type="work", salience=.66, relationship_relevance=.6, goal_relevance=.7,
                            provenance={"assumption_id": "ASM-FIXTURE-006", "work_id": provenance.get("work_id")},
                        )

                # Temporary water permissions expire deterministically without requiring cognition.
                expiring_water = con.execute(
                    "SELECT * FROM obligations WHERE status='granted' AND obligation_type='temporary_water_access' "
                    "AND due_day IS NOT NULL AND due_day<? ORDER BY obligation_id",
                    (target_day,),
                ).fetchall()
                for o in expiring_water:
                    provenance = json.loads(o["provenance_json"])
                    con.execute("UPDATE obligations SET status='expired' WHERE obligation_id=?", (o["obligation_id"],))
                    actors = [x for x in [o["obligor_person_id"], o["beneficiary_person_id"]] if x]
                    eid = self._event(
                        con, target_day, "water_access_permission_expired", actors=actors,
                        rules=["ASM-FIXTURE-007", "RULE-WATER-NEGOTIATION-001"],
                        institutions={"I-WATER": {"temporary_access": "expired"}},
                        payload={"obligation_id": o["obligation_id"], "request_event_id": provenance.get("request_event_id")},
                        discriminator=o["obligation_id"],
                    )
                    for person_id in actors:
                        self._memory(
                            con, person_id, target_day, "The temporary negotiated water-access period ended.",
                            event_id=eid, memory_type="water_access", salience=.5, relationship_relevance=.45, goal_relevance=.55,
                            provenance={"assumption_id": "ASM-FIXTURE-007"},
                        )

                due = con.execute(
                    "SELECT * FROM messages WHERE delivered_day IS NULL AND arrival_day<=? ORDER BY message_id",
                    (target_day,),
                ).fetchall()
                for m in due:
                    con.execute("UPDATE messages SET delivered_day=? WHERE message_id=?", (target_day, m["message_id"]))
                    if m["proposition_id"]:
                        kid = stable_id("K", m["recipient_person_id"], m["proposition_id"], m["message_id"], target_day)
                        con.execute(
                            "INSERT OR IGNORE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (kid, m["recipient_person_id"], m["proposition_id"], target_day, "message", m["message_id"],
                             canonical_json([m["originator_person_id"], m["recipient_person_id"]]), "hearsay", .65,
                             m["secrecy"], None),
                        )
                    eid = self._event(
                        con, target_day, "message_delivered", actors=[m["originator_person_id"], m["recipient_person_id"]],
                        rules=["RULE-MESSAGE-DELAY-001"], payload={"message_id": m["message_id"]},
                        discriminator=m["message_id"],
                    )
                    self._memory(con, m["recipient_person_id"], target_day,
                                 f"Received a message from {m['originator_person_id']}: {m['actual_content']}",
                                 event_id=eid, memory_type="message", salience=.55)

                people = con.execute("SELECT person_id,current_place_id FROM persons WHERE alive=1 ORDER BY person_id").fetchall()
                for p in people:
                    if rng.random() < 0.004:
                        sid = stable_id("SCENE", self.run_id, target_day, "minor_illness", p["person_id"])
                        if not con.execute("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)).fetchone():
                            con.execute(
                                "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (sid, self.run_id, target_day, p["current_place_id"], "religious", "minor_illness",
                                 canonical_json({"health_uncertainty": "minor"}), canonical_json({"time": "ordinary day"}),
                                 canonical_json({"ritual_and_practical_responses_both_possible": True}),
                                 canonical_json(["I-SHRINE"]), "open"),
                            )
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, p["person_id"], "affected_actor"))
                            self._event(
                                con, target_day, "runtime_circumstance", scene_id=sid, actors=[p["person_id"]],
                                rules=["ASM-UGA-003"], payload={"sample": "minor_illness", "runtime_stochastic": True},
                                discriminator=p["person_id"],
                            )
                con.execute("UPDATE runs SET current_day=? WHERE run_id=?", (target_day, self.run_id))
            self.detect_situations(target_day)
            advanced += 1
        return advanced

    def _project_household_grain_security(self, household_id: str, day: int, *, horizon_days: int = 7) -> dict[str, Any]:
        """Project one bounded fixture receipt cycle using the engine's actual routine order.

        These are abstract fixture mechanics, not historical ration or wage claims. A
        shortfall means the household cannot satisfy a full configured daily need
        before a scheduled receipt is applied on some day inside the horizon.
        """
        row = self.db.one(
            "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='grain'",
            (household_id,),
        )
        if not row:
            raise KeyError(household_id)
        provisioning = effective_household_provisioning(self.db, self.run_id, household_id)
        current = float(row["amount"])
        daily_need = float(provisioning["daily_need"])
        weekly_receipt = float(provisioning["weekly_receipt"])
        next_receipt_day = ((int(day) // 7) + 1) * 7
        horizon_day = int(day) + int(horizon_days)
        projected = current
        minimum = current
        first_shortfall_day: int | None = None
        for future_day in range(int(day) + 1, horizon_day + 1):
            if projected + 1e-9 < daily_need:
                first_shortfall_day = future_day
                break
            projected -= daily_need
            minimum = min(minimum, projected)
            if future_day % 7 == 0:
                projected += weekly_receipt
        return {
            "current_grain": current,
            "daily_need": daily_need,
            "next_receipt_day": next_receipt_day,
            "expected_receipt": weekly_receipt,
            "projection_horizon_day": horizon_day,
            "first_shortfall_day": first_shortfall_day,
            "projected_end_grain": projected,
            "minimum_projected_grain": minimum,
            "fixture_notice": "ASM-FIXTURE-004 projection over one configured weekly receipt cycle; not a historical rate.",
        }

    def detect_situations(self, day: int | None = None) -> list[str]:
        day = self.day if day is None else day
        created: list[str] = []
        households = self.db.all(
            "SELECT h.household_id,h.home_place_id FROM households h "
            "JOIN resource_stocks rs USING(household_id) "
            "WHERE rs.resource_type='grain' ORDER BY h.household_id"
        )
        for h in households:
            projection = self._project_household_grain_security(h["household_id"], day)
            if projection["first_shortfall_day"] is None:
                continue
            actor = self.db.one(
                "SELECT p.person_id FROM persons p JOIN household_memberships hm USING(person_id) "
                "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 "
                "ORDER BY CASE hm.membership_role WHEN 'senior' THEN 0 ELSE 1 END,p.person_id LIMIT 1",
                (h["household_id"],),
            )
            if actor:
                sid = stable_id("SCENE", self.run_id, "resource_shortfall", h["household_id"], day // 7)
                if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid, self.run_id, day, h["home_place_id"], "economic", "household_resource_shortfall",
                             canonical_json(projection),
                             canonical_json({"resource": "grain", **projection, "unit": "abstract_fixture_unit"}),
                             canonical_json({"household_security": True, "credit_reputation_may_matter": True}),
                             canonical_json(["I-MARKET"]), "open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, actor["person_id"], "decision_actor"))
                        self._event(
                            con, day, "projected_resource_shortfall_detected", scene_id=sid, actors=[actor["person_id"]],
                            rules=["ASM-FIXTURE-004"], payload=projection, discriminator=sid,
                        )
                    created.append(self.enqueue_job(
                        sid, actor["person_id"],
                        ["wait", "request_resource", "transfer_resource", "enter_obligation", "communicate", "refuse_proposal", "seek_mediation"],
                    ))

        # Merchant/harbor information uncertainty: an old unconfirmed report creates a
        # reason to seek information, not access to anyone else's private report.
        merchant_report = self.db.one(
            "SELECT k.knowledge_id,k.learned_day,k.confidence,p.canonical_text FROM knowledge k "
            "JOIN propositions p USING(proposition_id) WHERE k.person_id='P3' AND k.proposition_id='PROP-SHIP-001' "
            "AND k.learned_day<=? ORDER BY k.learned_day DESC,k.knowledge_id LIMIT 1",
            (day,),
        )
        if day >= 7 and merchant_report:
            sid = stable_id("SCENE", self.run_id, "merchant_harbor_information_uncertainty", "P3")
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id='P3' AND alive=1")
                if actor:
                    stakes = {
                        "situation_id": "SIT-005",
                        "known_knowledge_id": merchant_report["knowledge_id"],
                        "known_report_proposition_id": "PROP-SHIP-001",
                        "report_age_days": day - int(merchant_report["learned_day"]),
                        "report_confidence": float(merchant_report["confidence"]),
                        "contact_person_ids": ["P11", "P12"],
                        "epistemic_status": "unconfirmed_report; contacts may know different things but their knowledge is not exposed here",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid, self.run_id, day, actor["current_place_id"], "economic",
                             "merchant_harbor_information_uncertainty", canonical_json(stakes), "{}",
                             canonical_json({"information_provenance": True, "no_private_contact_knowledge": True}),
                             canonical_json(["I-MARKET"]), "open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P3", "decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P11", "harbor_contact"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P12", "market_contact"))
                        self._event(
                            con, day, "information_uncertainty_detected", scene_id=sid, actors=["P3"],
                            knowledge=[merchant_report["knowledge_id"]], rules=["ASM-FIXTURE-005"],
                            payload=stakes, discriminator=sid,
                        )
                    created.append(self.enqueue_job(sid, "P3", ["send_message", "wait"]))

        # A delivered inquiry becomes a bounded cognition scene for the recipient.
        # The scene contains the question and provenance, while any possible answer
        # must come from the recipient's own sealed packet.
        inquiries = self.db.all(
            "SELECT m.* FROM messages m WHERE m.sender_intent='inquiry' AND m.delivered_day IS NOT NULL "
            "AND m.delivered_day<=? AND NOT EXISTS (SELECT 1 FROM scenes s WHERE s.run_id=? "
            "AND s.trigger_type='information_inquiry_received' "
            "AND json_extract(s.stakes_json,'$.message_id')=m.message_id) ORDER BY m.delivered_day,m.message_id",
            (day, self.run_id),
        )
        for m in inquiries:
            recipient = self.db.one("SELECT current_place_id,alive FROM persons WHERE person_id=?", (m["recipient_person_id"],))
            if not recipient or not recipient["alive"]:
                continue
            sid = stable_id("SCENE", self.run_id, "information_inquiry_received", m["message_id"])
            stakes = {
                "situation_id": "SIT-005",
                "message_id": m["message_id"],
                "originator_person_id": m["originator_person_id"],
                "recipient_person_id": m["recipient_person_id"],
                "inquiry_content": m["actual_content"],
                "delivered_day": m["delivered_day"],
                "reply_must_use_recipient_packet_knowledge": True,
            }
            with self.db.transaction() as con:
                con.execute(
                    "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, self.run_id, day, recipient["current_place_id"], "economic", "information_inquiry_received",
                     canonical_json(stakes), "{}", canonical_json({"information_provenance": True}),
                     canonical_json(["I-MARKET"]), "open"),
                )
                con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, m["recipient_person_id"], "decision_actor"))
                con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, m["originator_person_id"], "requester"))
            created.append(self.enqueue_job(sid, m["recipient_person_id"], ["send_message", "wait"]))

        # Once Yabninu has actually received both independently sourced reports, the
        # contradiction/incompleteness itself can become a second decision boundary.
        received_reports = self.db.all(
            "SELECT k.knowledge_id,k.proposition_id,k.learned_day,k.source_kind,k.source_id,k.confidence,p.canonical_text "
            "FROM knowledge k JOIN propositions p USING(proposition_id) "
            "WHERE k.person_id='P3' AND k.proposition_id IN ('PROP-SHIP-001','PROP-SHIP-002') AND k.learned_day<=? "
            "ORDER BY k.proposition_id,k.learned_day DESC,k.knowledge_id",
            (day,),
        )
        if {r["proposition_id"] for r in received_reports} == {"PROP-SHIP-001", "PROP-SHIP-002"}:
            sid = stable_id("SCENE", self.run_id, "contradictory_shipping_reports", "P3")
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id='P3' AND alive=1")
                if actor:
                    newest = {}
                    for r in received_reports:
                        newest.setdefault(r["proposition_id"], r)
                    stakes = {
                        "situation_id": "SIT-005",
                        "report_knowledge_ids": [newest[p]["knowledge_id"] for p in sorted(newest)],
                        "report_proposition_ids": sorted(newest),
                        "epistemic_status": "reports are incomplete/discordant; canonical shipment outcome remains unspecified",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid, self.run_id, day, actor["current_place_id"], "economic", "contradictory_shipping_reports",
                             canonical_json(stakes), "{}", canonical_json({"information_provenance": True}),
                             canonical_json(["I-MARKET"]), "open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P3", "decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P11", "harbor_contact"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P12", "market_contact"))
                    created.append(self.enqueue_job(sid, "P3", ["send_message", "wait"]))

        # Ordinary-life fixture: a younger household member receives a bounded outside-work
        # opportunity. The fixture supplies the opportunity, not the character's response.
        if day >= 14:
            sid = stable_id("SCENE", self.run_id, "outside_work_opportunity", "WORK-P16-PORTER-001")
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                worker = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P16'")
                senior = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P15'")
                if worker and senior and worker["alive"] and worker["available"] and senior["alive"] and senior["available"]:
                    stakes = {
                        "situation_id": "SIT-006",
                        "work_id": "WORK-P16-PORTER-001",
                        "worker_person_id": "P16",
                        "household_senior_person_id": "P15",
                        "work_kind": "outside_porter_work",
                        "absence_days": 1,
                        "household_receipt": {"resource": "grain", "amount": 1.0, "unit": "abstract_fixture_unit"},
                        "epistemic_status": "the opportunity is known to P16; P15's private preferences are not exposed",
                        "fixture_notice": "ASM-FIXTURE-006 timing, duration, and compensation are engineering fixtures, not historical wage evidence.",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid, self.run_id, day, worker["current_place_id"], "household", "outside_work_opportunity",
                             canonical_json(stakes), canonical_json({"absence_days": 1, "household_receipt": stakes["household_receipt"]}),
                             canonical_json({"worker_agency": True, "household_labor_priority": True, "senior_private_preferences_hidden": True}),
                             "[]", "open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P16", "decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P15", "household_senior"))
                        self._event(
                            con, day, "fixture_work_opportunity_presented", scene_id=sid, actors=["P16"],
                            rules=["ASM-FIXTURE-006"], payload=stakes, discriminator=sid,
                        )
                    created.append(self.enqueue_job(
                        sid, "P16", ["request_household_work_agreement", "decline_fixture_work", "wait", "communicate"]
                    ))

        # Ordinary-life fixture: a temporary shared-water-point disruption makes unequal
        # access consequential. The exact disruption and negotiation procedure are not
        # historical claims; the archaeological inequality basis remains separate.
        if day >= 18:
            sid = stable_id("SCENE", self.run_id, "water_access_pressure", "WATER-P2-P6-001")
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                requester = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P2'")
                holder = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P6'")
                if requester and holder and requester["alive"] and requester["available"] and holder["alive"] and holder["available"]:
                    requester_status = json.loads(self.db.one("SELECT status_json FROM households WHERE household_id='H-FARM'")[0])
                    holder_status = json.loads(self.db.one("SELECT status_json FROM households WHERE household_id='H-SCRIBE'")[0])
                    if requester_status.get("water_access") == "shared" and holder_status.get("water_access") == "private":
                        stakes = {
                            "situation_id": "SIT-007",
                            "requester_person_id": "P2",
                            "requester_household_id": "H-FARM",
                            "access_holder_person_id": "P6",
                            "access_holder_household_id": "H-SCRIBE",
                            "shared_access_state": "temporarily_disrupted",
                            "known_access_option": "P6's household has private access that may be negotiated",
                            "suggested_request_days": 2,
                            "fixture_notice": "ASM-FIXTURE-007 is a simulation circumstance; exact Ugaritic access rights/procedure remain uncertain.",
                        }
                        with self.db.transaction() as con:
                            con.execute(
                                "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (sid, self.run_id, day, requester["current_place_id"], "household", "water_access_pressure",
                                 canonical_json(stakes), canonical_json({"shared_access": "temporarily_disrupted"}),
                                 canonical_json({"unequal_access": True, "negotiation_not_entitlement": True, "exact_procedure_uncertain": True}),
                                 canonical_json(["I-WATER"]), "open"),
                            )
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P2", "decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, "P6", "private_access_neighbor"))
                            self._event(
                                con, day, "fixture_water_access_pressure", scene_id=sid, actors=["P2"],
                                rules=["ASM-FIXTURE-007", "ASM-UGA-001"], payload=stakes, discriminator=sid,
                            )
                        created.append(self.enqueue_job(
                            sid, "P2", ["request_water_access", "seek_mediation", "wait", "communicate"]
                        ))

        # Communal ritual/feasting becomes a social/material decision for one
        # non-specialist household rather than a free flavor event for everyone.
        if self.db.one(
            "SELECT 1 FROM events WHERE run_id=? AND day=? AND event_type='communal_feast_calendar_due'",
            (self.run_id, day),
        ):
            sid = stable_id("SCENE", self.run_id, "communal_feast_contribution", day)
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                candidate = self.db.one(
                    "SELECT p.person_id,p.current_place_id,hm.household_id,rg.amount AS ritual_goods,g.amount AS grain,"
                    "COALESCE(rt.value,0)+COALESCE(st.value,0) AS social_ritual_salience "
                    "FROM persons p JOIN household_memberships hm USING(person_id) "
                    "JOIN resource_stocks rg ON rg.household_id=hm.household_id AND rg.resource_type='ritual_goods' "
                    "JOIN resource_stocks g ON g.household_id=hm.household_id AND g.resource_type='grain' "
                    "LEFT JOIN character_traits rt ON rt.person_id=p.person_id AND rt.trait_name='ritual_commitment' "
                    "LEFT JOIN character_traits st ON st.person_id=p.person_id AND st.trait_name='status_sensitivity' "
                    "WHERE hm.until_day IS NULL AND p.alive=1 AND p.available=1 AND hm.membership_role='senior' "
                    "AND p.person_id NOT IN ('P9') AND rg.amount>=0.1 ORDER BY social_ritual_salience DESC,p.person_id LIMIT 1"
                )
                if candidate:
                    seasonal = self._seasonal_context(day)
                    stakes = {
                        "situation_id": "SIT-008",
                        "household_id": candidate["household_id"],
                        "grain_available": float(candidate["grain"]),
                        "ritual_goods_available": float(candidate["ritual_goods"]),
                        "max_grain_contribution": 1.0,
                        "max_ritual_goods_contribution": 0.5,
                        "ritual_hosts": ["P9", "P10"],
                        "seasonal_context": seasonal,
                        "fixture_notice": "Communal ritual/feasting is research-supported; exact date and contribution quantities are ASM-FIXTURE-010 calibration.",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid,self.run_id,day,candidate["current_place_id"],"religious","communal_feast_contribution",
                             canonical_json(stakes),canonical_json({"household_resources_are_finite":True}),
                             canonical_json({"participation_reputation":True,"contribution_is_not_forced":True}),
                             canonical_json(["I-SHRINE"]),"open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,candidate["person_id"],"decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P9","ritual_host"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P10","ritual_host"))
                    created.append(self.enqueue_job(sid,candidate["person_id"],["contribute_communal_feast","decline_feast_contribution","communicate","wait"]))

        # A communal gathering can expose a marriage discussion opportunity, but the
        # pairing/timing are explicit fixtures and no marriage occurs without both
        # households and both principals passing through bounded typed decisions.
        if (self.db.schema_version() >= 2 and day >= 150
                and self.db.one("SELECT 1 FROM events WHERE run_id=? AND day=? AND event_type='communal_feast_calendar_due'", (self.run_id, day))
                and self._is_unmarried("P16") and self._is_unmarried("P10")):
            sid = stable_id("SCENE", self.run_id, "marriage_discussion_opportunity", "P16", "P10")
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                p16 = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P16'")
                p10 = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P10'")
                if p16 and p10 and p16["alive"] and p10["alive"] and p16["available"] and p10["available"] and p16["current_place_id"] == p10["current_place_id"]:
                    stakes = {
                        "situation_id":"SIT-015","initiator_person_id":"P16","prospective_partner_person_id":"P10",
                        "initiator_household_id":"H-WIDOW","partner_household_id":"H-RITUAL",
                        "household_senior_ids":["P15","P9"],
                        "fixture_notice":"Pairing and feast timing are ASM-FIXTURE-019; no historical Ugaritic marriage or matchmaking event is claimed.",
                    }
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (sid,self.run_id,day,p16["current_place_id"],"household","marriage_discussion_opportunity",
                                     canonical_json(stakes),"{}",canonical_json({"individual_willingness_first":True,"no_preselected_outcome":True}),
                                     canonical_json(["I-MEDIATION"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P16","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P10","prospective_partner"))
                        self._event(con,day,"marriage_discussion_opportunity",scene_id=sid,actors=["P16","P10"],
                                    rules=["ASM-FIXTURE-019","RULE-MARRIAGE-NEGOTIATION-001"],payload=stakes,discriminator=sid)
                    created.append(self.enqueue_job(sid,"P16",["request_marriage_discussion","wait","communicate"]))

        # The accepted P16->P15 continuing-care term becomes a concrete recurring support
        # need rather than passive prose. Exact timing/task are v007 fixture calibration.
        if (self._has_assumption("ASM-FIXTURE-023") and day >= self._v007_start_day() + 3
                and (day - (self._v007_start_day() + 3)) % 30 == 0):
            care = self.db.one(
                "SELECT * FROM obligations WHERE status='active' AND obligation_type='continuing_kin_care' "
                "AND obligor_person_id='P16' AND beneficiary_person_id='P15' ORDER BY obligation_id LIMIT 1"
            )
            if care:
                sid=stable_id("SCENE",self.run_id,"continuing_kin_care_need",care["obligation_id"],day)
                if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)):
                    actor=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P16'")
                    beneficiary=self.db.one("SELECT current_place_id,alive FROM persons WHERE person_id='P15'")
                    if actor and beneficiary and actor["alive"] and actor["available"] and beneficiary["alive"]:
                        prior=int(self.db.scalar("SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='kin_care_fulfilled' AND json_extract(payload_json,'$.care_obligation_id')=?",(self.run_id,care["obligation_id"])) or 0)
                        seasonal_care=self._seasonal_context(day)
                        support_kind="household_property_support_day"
                        care_notice="Concrete care timing/task are ASM-FIXTURE-023; the continuing obligation came from negotiated marriage terms and no inheritance transfer is implied."
                        if self._has_assumption("ASM-FIXTURE-025"):
                            if prior >= 3 and seasonal_care["phase"] == "wet_winter_growth":
                                support_kind="winter_household_maintenance_and_errands"
                            care_notice="Concrete care timing/task are ASM-FIXTURE-023; later episodes may vary by season, the continuing obligation remains active, and no inheritance transfer is implied."
                        stakes={"situation_id":"SIT-017","care_obligation_id":care["obligation_id"],"beneficiary_person_id":"P15",
                                "support_kind":support_kind,"prior_fulfilled_care_episodes":prior,
                                "seasonal_context":seasonal_care,
                                "fixture_notice":care_notice}
                        with self.db.transaction() as con:
                            con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                        (sid,self.run_id,day,actor["current_place_id"],"household","continuing_kin_care_need",canonical_json(stakes),
                                         canonical_json({"support_day_has_opportunity_cost":True}),
                                         canonical_json({"continuing_care_obligation":True,"property_consequence_not_automatic":True}),
                                         canonical_json(["I-MEDIATION"]),"open"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P16","decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P15","care_beneficiary"))
                            self._event(con,day,"kin_care_need",scene_id=sid,actors=["P16","P15"],rules=["ASM-FIXTURE-023","RULE-KIN-CARE-PROPERTY-001"],payload=stakes,discriminator=sid)
                        created.append(self.enqueue_job(sid,"P16",["fulfill_kin_care","defer_kin_care","communicate"]))

        # During the first v007 sowing window, H-DEPEND can seek bounded draft-team help
        # from H-FARM. Access asymmetry and exact service are explicit fixture assumptions.
        seasonal_now=self._seasonal_context(day)
        if (self._has_assumption("ASM-FIXTURE-024") and day >= self._v007_start_day()+1
                and seasonal_now["phase"] == "early_rains_and_sowing"):
            sid=stable_id("SCENE",self.run_id,"sowing_draft_access_pressure","H-DEPEND","H-FARM",self._v007_start_day())
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)):
                p13=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P13'")
                p1=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P1'")
                hs13=self.db.one("SELECT status_json FROM households WHERE household_id='H-DEPEND'")
                hs1=self.db.one("SELECT status_json FROM households WHERE household_id='H-FARM'")
                if p13 and p1 and p13["alive"] and p13["available"] and p1["alive"] and p1["available"]:
                    dep=json.loads(hs13[0]) if hs13 else {}
                    farm=json.loads(hs1[0]) if hs1 else {}
                    if dep.get("draft_access")=="requires_negotiation" and farm.get("draft_access")=="controls_fixture_team":
                        stakes={"situation_id":"SIT-018","requester_person_id":"P13","requester_household_id":"H-DEPEND",
                                "access_holder_person_id":"P1","access_holder_household_id":"H-FARM","service_days":1,
                                "service_sowing_progress":0.10,"access_holder_opportunity_cost_progress":0.05,
                                "seasonal_context":seasonal_now,
                                "fixture_notice":"The draft-team access asymmetry, household pairing, one-day service, and progress effect are ASM-FIXTURE-024 calibration."}
                        with self.db.transaction() as con:
                            con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                        (sid,self.run_id,day,p13["current_place_id"],"economic","sowing_draft_access_pressure",canonical_json(stakes),
                                         canonical_json({"sowing_window":True,"draft_access":"not_controlled"}),
                                         canonical_json({"negotiation_not_entitlement":True,"grant_has_household_opportunity_cost":True}),
                                         canonical_json(["I-MEDIATION"]),"open"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P13","decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P1","draft_access_holder"))
                            self._event(con,day,"sowing_draft_access_pressure",scene_id=sid,actors=["P13","P1"],rules=["ASM-FIXTURE-024","RULE-SOWING-DRAFT-ACCESS-001"],payload=stakes,discriminator=sid)
                        created.append(self.enqueue_job(sid,"P13",["request_draft_access","wait","communicate"]))

        # Winter maintenance pressure can turn the remembered sowing favor into a
        # concrete reciprocal-labor opportunity. Exact condition/timing are fixtures.
        if (self._has_assumption("ASM-FIXTURE-025") and day >= self._v008_start_day()
                and seasonal_now["phase"] == "wet_winter_growth"):
            cond=self.db.one("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='draft_team_condition'")
            rel=self.db.one("SELECT favors_given FROM relationships WHERE from_person_id='P1' AND to_person_id='P13'")
            favor_available=bool(rel and float(rel["favors_given"]) >= 1.0)
            if cond and float(cond["amount"]) <= 0.90 + 1e-9:
                sid=stable_id("SCENE",self.run_id,"winter_draft_maintenance_pressure","P1",day//7)
                if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)):
                    p1=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P1'")
                    p13=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P13'")
                    if p1 and p13 and p1["alive"] and p1["available"] and p13["alive"] and p13["available"]:
                        stakes={"situation_id":"SIT-020","requester_person_id":"P1","helper_person_id":"P13",
                                "beneficiary_household_id":"H-FARM","draft_team_condition":float(cond["amount"]),
                                "service_days":1,"condition_restore":0.15,"remembered_favor_available":favor_available,
                                "seasonal_context":seasonal_now,
                                "fixture_notice":"Winter condition threshold, service duration and restoration are ASM-FIXTURE-025 calibration; the earlier sowing favor has no fixed exchange value."}
                        with self.db.transaction() as con:
                            con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                        (sid,self.run_id,day,p1["current_place_id"],"household","winter_draft_maintenance_pressure",canonical_json(stakes),
                                         canonical_json({"draft_team_condition":float(cond["amount"]),"winter_maintenance":True}),
                                         canonical_json({"reciprocity_is_open_ended":True,"request_not_entitlement":True}),
                                         canonical_json(["I-MEDIATION"]),"open"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P1","decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P13","potential_helper"))
                            self._event(con,day,"winter_draft_maintenance_pressure",scene_id=sid,actors=["P1","P13"],
                                        rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],payload=stakes,discriminator=sid)
                        allowed=["handle_winter_maintenance_internally","wait","communicate"]
                        if favor_available:
                            allowed.insert(0,"request_reciprocal_labor")
                        created.append(self.enqueue_job(sid,"P1",allowed))

        # Seasonal surplus becomes a cognition boundary only once enough exposed produce
        # has accumulated to make preservation materially consequential. It is separate
        # from the neutral staple-grain baseline.
        if day >= self._v006_start_day():
            surplus_rows = self.db.all(
                "SELECT household_id,amount FROM resource_stocks WHERE resource_type='seasonal_produce' AND amount>=0.45 ORDER BY household_id"
            )
            for sr in surplus_rows:
                bucket = day // 30
                sid = stable_id("SCENE", self.run_id, "seasonal_surplus_storage_pressure", sr["household_id"], bucket)
                if self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                    continue
                actor = self.db.one(
                    "SELECT p.person_id,p.current_place_id FROM persons p JOIN household_memberships hm USING(person_id) "
                    "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 AND p.available=1 "
                    "ORDER BY CASE hm.membership_role WHEN 'senior' THEN 0 ELSE 1 END,p.person_id LIMIT 1",
                    (sr["household_id"],),
                )
                if not actor:
                    continue
                max_preserve = min(0.4, float(sr["amount"]))
                stakes = {
                    "situation_id":"SIT-016","household_id":sr["household_id"],
                    "exposed_seasonal_produce":float(sr["amount"]),"max_preserve_amount":max_preserve,
                    "preservation_output_ratio":0.9,"seasonal_context":self._seasonal_context(day),
                    "fixture_notice":"Surplus threshold, preservation amount/yield, and loss model are ASM-FIXTURE-021 calibration, not historical crop/storage rates.",
                }
                with self.db.transaction() as con:
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (sid,self.run_id,day,actor["current_place_id"],"economic","seasonal_surplus_storage_pressure",
                                 canonical_json(stakes),canonical_json({"seasonal_produce":float(sr["amount"])}),
                                 canonical_json({"household_storage_choice":True,"staple_grain_separate":True}),"[]","open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,actor["person_id"],"decision_actor"))
                    self._event(con,day,"seasonal_surplus_storage_pressure",scene_id=sid,actors=[actor["person_id"]],
                                rules=["ASM-FIXTURE-021","RULE-SEASONAL-SURPLUS-STORAGE-001"],payload=stakes,discriminator=sid)
                created.append(self.enqueue_job(sid,actor["person_id"],["preserve_seasonal_surplus","wait","communicate"]))

        # Palace labor becomes a cognition boundary only while it collides with an
        # ecological labor bottleneck. Outside that bottleneck it is completed by the
        # deterministic institutional routine above.
        seasonal = self._seasonal_context(day)
        palace_due = self.db.all(
            "SELECT * FROM obligations WHERE status='active' AND obligation_type='palace_labor' "
            "AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
            (day,),
        )
        if seasonal["agricultural_intensity"] >= 0.85:
            for o in palace_due:
                actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id=? AND alive=1 AND available=1", (o["obligor_person_id"],))
                if not actor:
                    continue
                suggested = self._next_lower_agricultural_intensity_day(day, threshold=.85)
                sid = stable_id("SCENE", self.run_id, "institutional_labor_conflict", o["obligation_id"], o["due_day"])
                if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                    stakes = {
                        "situation_id": "SIT-009", "obligation_id": o["obligation_id"],
                        "institution_id": "I-PALACE", "current_due_day": o["due_day"],
                        "suggested_reschedule_day": suggested, "seasonal_context": seasonal,
                        "fixture_notice": "Institutional labor is research-supported; cadence, service duration and rescheduling mechanism are ASM-FIXTURE-011 calibration.",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid,self.run_id,day,actor["current_place_id"],"institutional","institutional_labor_conflict",
                             canonical_json(stakes),canonical_json({"household_labor_bottleneck":seasonal["farm_activity"]}),
                             canonical_json({"palace_obligation":True,"household_opportunity_cost":True}),
                             canonical_json(["I-PALACE"]),"open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,o["obligor_person_id"],"decision_actor"))
                    created.append(self.enqueue_job(sid,o["obligor_person_id"],["accept_palace_labor","reschedule_palace_labor","seek_mediation"]))

        # Household strategy can become a real constraint on an individual's recurring
        # occupational choices. After repeated successful trade cycles, the lower-risk
        # household account partner can ask the merchant to preserve a silver reserve.
        # The timing/floor are fixture calibration; the negotiation and later constraint
        # are canonical social consequences rather than flavor text.
        if day >= 91:
            completed_trades = int(self.db.scalar(
                "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='fixture_trade_exchange_completed'",
                (self.run_id,),
            ) or 0)
            active_reserve = self._active_household_reserve_floor("H-MERCH", "silver")
            p3_risk = self.db.scalar("SELECT value FROM character_traits WHERE person_id='P3' AND trait_name='risk_tolerance'")
            p4_risk = self.db.scalar("SELECT value FROM character_traits WHERE person_id='P4' AND trait_name='risk_tolerance'")
            if completed_trades >= 2 and active_reserve is None and p3_risk is not None and p4_risk is not None \
                    and float(p3_risk) - float(p4_risk) >= 0.15:
                sid = stable_id("SCENE", self.run_id, "household_trade_reserve_priority", "H-MERCH")
                if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                    actor = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P4'")
                    silver = self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='silver'")
                    if actor and actor["alive"] and actor["available"] and silver is not None:
                        proposed_floor = max(0.0, round(float(silver) - 0.5, 2))
                        stakes = {
                            "situation_id": "SIT-013", "requester_person_id": "P4", "merchant_person_id": "P3",
                            "household_id": "H-MERCH", "resource": "silver", "current_amount": float(silver),
                            "completed_trade_exchanges": completed_trades, "proposed_reserve_floor": proposed_floor,
                            "fixture_notice": "The reserve-review threshold and floor are ASM-FIXTURE-016 calibration; household strategy constraining individual trade exposure is the modeled social mechanism.",
                        }
                        with self.db.transaction() as con:
                            con.execute(
                                "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (sid,self.run_id,day,actor["current_place_id"],"household","household_trade_reserve_priority",
                                 canonical_json(stakes),canonical_json({"silver_available":float(silver)}),
                                 canonical_json({"private_negotiation_first":True,"household_resource_strategy":True}),
                                 canonical_json(["I-MEDIATION"]),"open"),
                            )
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P4","decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P3","household_trade_actor"))
                            self._event(
                                con,day,"household_resource_priority_raised",scene_id=sid,actors=["P4","P3"],
                                rules=["ASM-FIXTURE-016","RULE-HOUSEHOLD-RESOURCE-PRIORITY-001"],payload=stakes,discriminator=sid,
                            )
                        created.append(self.enqueue_job(sid,"P4",["request_household_reserve_agreement","communicate","wait"]))

        # Apprenticeship progression is based on accumulated work history rather than a
        # random birthday. The first implementation is deliberately modest: recognition
        # inside the same workshop/household, not a universal claim about Ugaritic legal
        # emancipation, guild rank, or apprenticeship duration.
        if day >= 91:
            apprentice_role = self.db.one(
                "SELECT pr.start_day FROM person_roles pr JOIN roles r USING(role_id) "
                "WHERE pr.person_id='P8' AND r.name='craft_apprentice' AND pr.end_day IS NULL ORDER BY pr.start_day LIMIT 1"
            )
            prior_progression = self.db.one(
                "SELECT 1 FROM scenes WHERE run_id=? AND trigger_type IN ('apprenticeship_progression_review','apprenticeship_progression_request') LIMIT 1",
                (self.run_id,),
            )
            work_cycles = int(self.db.scalar(
                "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='occupation_work_cycle' "
                "AND actor_ids_json LIKE '%P8%' AND payload_json LIKE '%craft_apprentice%'",
                (self.run_id,),
            ) or 0)
            finished = self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
            if apprentice_role and not prior_progression and day - int(apprentice_role["start_day"]) >= 91 \
                    and work_cycles >= 12 and finished is not None and float(finished) >= 0.6:
                sid = stable_id("SCENE", self.run_id, "apprenticeship_progression_review", "P8")
                apprentice = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P8'")
                master = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id='P7'")
                if apprentice and master and apprentice["alive"] and apprentice["available"] and master["alive"] and master["available"]:
                    stakes = {
                        "situation_id":"SIT-014","apprentice_person_id":"P8","master_person_id":"P7",
                        "work_cycles_as_apprentice":work_cycles,"apprenticeship_days":day-int(apprentice_role["start_day"]),
                        "household_finished_metalwork":float(finished),
                        "proposed_recognition":"recognized_craft_worker",
                        "fixture_notice":"Eligibility timing and production threshold are ASM-FIXTURE-017 calibration; progression is workshop recognition, not a reconstructed Ugaritic legal rank or universal apprenticeship duration.",
                    }
                    with self.db.transaction() as con:
                        con.execute(
                            "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (sid,self.run_id,day,apprentice["current_place_id"],"household","apprenticeship_progression_review",
                             canonical_json(stakes),canonical_json({"accumulated_work_cycles":work_cycles}),
                             canonical_json({"master_apprentice_relationship":True,"progression_requires_negotiation":True}),
                             canonical_json(["I-MEDIATION"]),"open"),
                        )
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P8","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P7","master"))
                        self._event(
                            con,day,"apprenticeship_progression_eligible",scene_id=sid,actors=["P8","P7"],
                            rules=["ASM-FIXTURE-017","RULE-APPRENTICESHIP-PROGRESSION-001"],payload=stakes,discriminator=sid,
                        )
                    created.append(self.enqueue_job(sid,"P8",["request_apprenticeship_progression","communicate","wait"]))

        # Recurrent port activity becomes a material commitment decision only after the
        # merchant has already experienced the information-provenance chain.
        if day >= 42 and day % 28 == 14 and self.db.one(
            "SELECT 1 FROM events WHERE run_id=? AND day=? AND event_type='port_market_cycle'", (self.run_id,day)
        ):
            cycle = day // 28
            sid = stable_id("SCENE",self.run_id,"port_trade_opportunity","P3",cycle)
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)):
                actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id='P3' AND alive=1 AND available=1")
                silver = self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='silver'")
                if actor and silver is not None and float(silver) >= 0.25:
                    stakes = {
                        "situation_id":"SIT-010","trade_cycle":cycle,"silver_available":float(silver),
                        "max_silver_commitment":0.5,"transit_days":7,"exchange_goods_ratio":1.0,
                        "household_reserve_floor":self._active_household_reserve_floor("H-MERCH","silver"),
                        "contacts":["P11","P12"],"seasonal_context":seasonal,
                        "fixture_notice":"Exchange amount, ratio and delay are ASM-FIXTURE-012 calibration; the Ugaritic port/trade/credit interface is research-supported.",
                    }
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (sid,self.run_id,day,actor["current_place_id"],"economic","port_trade_opportunity",
                                     canonical_json(stakes),canonical_json({"capital_at_risk":True,"transport_delay":7}),
                                     canonical_json({"trust_credit_and_information_matter":True}),canonical_json(["I-MARKET"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P3","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P11","harbor_contact"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P12","market_contact"))
                    created.append(self.enqueue_job(sid,"P3",["commit_trade_exchange","send_message","wait"]))

        # Workshop supply pressure emerges from the material workflow consuming metal.
        # From v009, once P3 has legitimately refused further supply for scarcity reasons,
        # expose costly recycling and a provenance-preserving network-search alternative
        # instead of mechanically repeating the same supplier request forever.
        craft_metal = self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='metal'")
        v009_alt_opened = False
        if (craft_metal is not None and float(craft_metal) < 0.31
                and self._has_assumption("ASM-FIXTURE-028") and day >= self._v009_start_day()):
            conflict = self.db.one("SELECT conflicts FROM relationships WHERE from_person_id='P7' AND to_person_id='P3'")
            refusal = self.db.one(
                "SELECT e.event_id,e.day FROM events e WHERE e.run_id=? AND e.event_type='proposal_refused' "
                "AND e.actor_ids_json LIKE '%P3%' AND e.actor_ids_json LIKE '%P7%' ORDER BY e.day DESC,e.event_seq DESC LIMIT 1",
                (self.run_id,),
            )
            alt_sid=stable_id("SCENE",self.run_id,"workshop_supply_alternatives","P7","P3")
            if conflict and int(conflict["conflicts"])>0 and refusal and self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(alt_sid,)):
                # The accepted scarcity refusal permanently retires the legacy single-supplier
                # loop for this run. Subsequent supply work proceeds through recycling or the
                # modeled alternate network rather than silently offering P3 again.
                v009_alt_opened=True
            if conflict and int(conflict["conflicts"])>0 and refusal and not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(alt_sid,)):
                actor=self.db.one("SELECT current_place_id FROM persons WHERE person_id='P7' AND alive=1 AND available=1")
                finished=self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-CRAFT' AND resource_type='finished_metalwork'")
                supplier=self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='metal'")
                if actor:
                    stakes={
                        "situation_id":"SIT-021","resource":"metal","current_amount":float(craft_metal),
                        "next_cycle_need":0.15,"recent_supplier_refusal_event_id":refusal["event_id"],
                        "known_supplier_person_id":"P3","known_supplier_stock":float(supplier or 0),
                        "finished_metalwork_available":float(finished or 0),
                        "recycle_input_finished_metalwork":0.20,"recycle_output_metal":0.12,
                        "possible_introduction_person_id":"P3","possible_harbor_contact_person_id":"P11",
                        "fixture_notice":"Recycling is research-supported but 0.20→0.12 is ASM-FIXTURE-027 calibration. Alternate sourcing must proceed through ASM-FIXTURE-028 social/information steps; no second supplier is pre-known to P7."
                    }
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (alt_sid,self.run_id,day,actor["current_place_id"],"economic","workshop_supply_alternatives",
                             canonical_json(stakes),canonical_json({"metal_needed_for_next_cycle":0.15,"recycling_sacrifices_finished_output":True}),
                             canonical_json({"recent_supplier_refusal":True,"alternate_contact_not_yet_known":True}),
                             canonical_json(["I-MARKET"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(alt_sid,"P7","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(alt_sid,"P3","merchant_relationship"))
                        self._event(con,day,"workshop_supply_alternatives_opened",scene_id=alt_sid,actors=["P7","P3"],
                            rules=["ASM-FIXTURE-027","ASM-FIXTURE-028","RULE-ALTERNATE-METAL-SOURCING-001"],payload=stakes,discriminator=alt_sid)
                    created.append(self.enqueue_job(alt_sid,"P7",["recycle_finished_metalwork","request_market_introduction","wait","communicate"]))
                    v009_alt_opened=True
        if craft_metal is not None and float(craft_metal) < 0.31 and not v009_alt_opened:
            prior_craft_scene = self.db.one(
                "SELECT scene_id FROM scenes WHERE run_id=? AND trigger_type='craft_supply_pressure' ORDER BY day DESC,scene_id DESC LIMIT 1",
                (self.run_id,),
            )
            # Preserve the first accepted episode ID for replay compatibility; later low-stock
            # episodes are bucketed so replenishment can matter and a new shortage can recur.
            sid = (stable_id("SCENE",self.run_id,"craft_supply_pressure","H-CRAFT","metal")
                   if not prior_craft_scene
                   else stable_id("SCENE",self.run_id,"craft_supply_pressure","H-CRAFT","metal",day // 14))
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)):
                actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id='P7' AND alive=1 AND available=1")
                supplier = self.db.scalar("SELECT amount FROM resource_stocks WHERE household_id='H-MERCH' AND resource_type='metal'")
                if actor and supplier is not None and float(supplier) > 0:
                    stakes = {
                        "situation_id":"SIT-011","resource":"metal","current_amount":float(craft_metal),
                        "next_cycle_need":0.15,"known_supplier_person_id":"P3","known_supplier_household_id":"H-MERCH",
                        "supplier_stock_visible_as_market_availability":float(supplier),
                        "fixture_notice":"Material amounts are ASM-FIXTURE-009 calibration; metal/fuel dependency, recycling and specialist vulnerability are research-supported.",
                    }
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (sid,self.run_id,day,actor["current_place_id"],"economic","craft_supply_pressure",
                                     canonical_json(stakes),canonical_json({"metal_needed_for_next_cycle":0.15}),
                                     canonical_json({"specialist_dependency":True,"market_or_patron_help_possible":True}),
                                     canonical_json(["I-MARKET"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P7","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,"P3","known_supplier"))
                    created.append(self.enqueue_job(sid,"P7",["request_resource","communicate","wait"]))

        # Once P7 has actually received P11's private fixture lead through message delivery,
        # expose a terms request to P12. Mere repository/scenario knowledge is insufficient.
        if self._has_assumption("ASM-FIXTURE-028") and day >= self._v009_start_day():
            lead_k=self.db.one(
                "SELECT knowledge_id,learned_day FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-ALT-001' "
                "AND learned_day<=? ORDER BY learned_day DESC,knowledge_id LIMIT 1",(day,))
            lead_sid=stable_id("SCENE",self.run_id,"alternate_metal_lead_received","P7","P12")
            if lead_k and not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(lead_sid,)):
                actor=self.db.one("SELECT current_place_id FROM persons WHERE person_id='P7' AND alive=1 AND available=1")
                if actor:
                    stakes={"situation_id":"SIT-022","lead_knowledge_id":lead_k["knowledge_id"],
                            "market_intermediary_person_id":"P12","silver_cost":0.30,"metal_amount":0.30,"delivery_days":3,
                            "fixture_notice":"P11's delivered report exposes only a fixture market lead. P12 must independently decide whether to offer the calibrated terms under ASM-FIXTURE-028."}
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (lead_sid,self.run_id,day,actor["current_place_id"],"economic","alternate_metal_lead_received",
                             canonical_json(stakes),canonical_json({"lead_is_information_not_stock":True}),
                             canonical_json({"market_terms_not_yet_offered":True}),canonical_json(["I-MARKET"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(lead_sid,"P7","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(lead_sid,"P12","possible_market_intermediary"))
                    created.append(self.enqueue_job(lead_sid,"P7",["send_message","wait"]))

        # A P12 offer becomes actionable only after his report of the private terms has
        # actually been delivered to P7. Until then the fixture terms remain hidden.
        if self._has_assumption("ASM-FIXTURE-028") and day >= self._v009_start_day():
            terms_k=self.db.one(
                "SELECT knowledge_id,learned_day FROM knowledge WHERE person_id='P7' AND proposition_id='PROP-METAL-TERMS-001' "
                "AND learned_day<=? ORDER BY learned_day DESC,knowledge_id LIMIT 1",(day,))
            offer_sid=stable_id("SCENE",self.run_id,"alternate_metal_exchange_offer_received","P7","P12")
            if terms_k and not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?",(offer_sid,)):
                actor=self.db.one("SELECT current_place_id FROM persons WHERE person_id='P7' AND alive=1 AND available=1")
                if actor:
                    stakes={"situation_id":"SIT-023","terms_knowledge_id":terms_k["knowledge_id"],
                            "market_intermediary_person_id":"P12","silver_cost":0.30,"metal_amount":0.30,"delivery_days":3,
                            "fixture_notice":"The exact 0.30/0.30/3-day terms are ASM-FIXTURE-028 calibration and became actionable only after P12's report was delivered."}
                    with self.db.transaction() as con:
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (offer_sid,self.run_id,day,actor["current_place_id"],"economic","alternate_metal_exchange_offer",canonical_json(stakes),
                             canonical_json({"silver_due_on_acceptance":0.30,"metal_delayed":0.30}),
                             canonical_json({"requester_may_accept_or_walk_away":True}),canonical_json(["I-MARKET"]),"open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(offer_sid,"P7","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(offer_sid,"P12","market_intermediary"))
                    created.append(self.enqueue_job(offer_sid,"P7",["accept_alternate_metal_exchange","wait","communicate"]))

        # Let an open reciprocal exchange close through later occupational output.
        # The obligation is qualitative social credit, not a priced debt: the suggested
        # return is a bounded opportunity to reciprocate, not a claimed exchange rate.
        reciprocal = self.db.all(
            "SELECT * FROM obligations WHERE status='active' AND obligation_type='reciprocal_exchange' ORDER BY obligation_id"
        )
        for o in reciprocal:
            provenance = json.loads(o["provenance_json"])
            origin_scene_id = provenance.get("origin_scene_id")
            origin_scene = self.db.one("SELECT day FROM scenes WHERE scene_id=?", (origin_scene_id,)) if origin_scene_id else None
            if not origin_scene or day - int(origin_scene["day"]) < 30:
                continue
            actor_id = o["obligor_person_id"]
            beneficiary = o["beneficiary_person_id"]
            actor_household = o["obligor_household_id"]
            beneficiary_household = o["beneficiary_household_id"]
            # Current first implementation uses the craft household's actual accumulated
            # output; other occupation-specific return forms can be added when evidence
            # and workflows require them. Older accepted histories retain the legacy 0.3
            # suggestion exactly. From ASM-FIXTURE-026 onward, a sealed smaller support
            # amount conservatively caps the suggestion without asserting equivalence.
            suggested_amount = 0.3
            if self._has_assumption("ASM-FIXTURE-026"):
                origin_amount = provenance.get("origin_amount")
                if isinstance(origin_amount, (int, float)) and float(origin_amount) > 0:
                    suggested_amount = min(0.3, float(origin_amount))
            finished = self.db.scalar(
                "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='finished_metalwork'",
                (actor_household,),
            )
            if finished is None or float(finished) + 1e-9 < suggested_amount:
                continue
            actor = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (actor_id,))
            if not actor or not actor["alive"] or not actor["available"]:
                continue
            sid = stable_id("SCENE", self.run_id, "reciprocal_return_opportunity", o["obligation_id"])
            if self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                continue
            stakes = {
                "situation_id": "SIT-012",
                "obligation_id": o["obligation_id"],
                "beneficiary_person_id": beneficiary,
                "beneficiary_household_id": beneficiary_household,
                "suggested_resource": "finished_metalwork",
                "suggested_amount": suggested_amount,
                "available_finished_metalwork": float(finished),
                "origin_scene_id": origin_scene_id,
                "fixture_notice": (
                    "The reciprocal obligation is socially causal; 30-day review timing and the return suggestion are fixture calibration. "
                    "Under ASM-FIXTURE-026 a sealed smaller support amount caps the suggestion conservatively; no historical price/equivalence is claimed."
                    if self._has_assumption("ASM-FIXTURE-026") else
                    "The reciprocal obligation is socially causal; 30-day review timing and 0.3 finished-metalwork return are ASM-FIXTURE-015 calibration, not a historical price/equivalence claim."
                ),
            }
            with self.db.transaction() as con:
                con.execute(
                    "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (sid,self.run_id,day,actor["current_place_id"],"economic","reciprocal_return_opportunity",
                     canonical_json(stakes),canonical_json({"available_finished_metalwork":float(finished)}),
                     canonical_json({"reciprocity":True,"return_is_optional":True,"not_fixed_price_debt":True}),
                     canonical_json(["I-MARKET"]),"open"),
                )
                con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,actor_id,"decision_actor"))
                if beneficiary:
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(sid,beneficiary,"beneficiary"))
                self._event(
                    con,day,"reciprocal_return_opportunity",scene_id=sid,actors=[x for x in [actor_id,beneficiary] if x],
                    rules=["ASM-FIXTURE-015","RULE-RECIPROCAL-SOCIAL-CREDIT-001"],payload=stakes,discriminator=sid,
                )
            created.append(self.enqueue_job(sid,actor_id,["transfer_resource","communicate","wait"]))

        obligations = self.db.all(
            "SELECT * FROM obligations WHERE status='active' AND obligation_type!='palace_labor' AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
            (day,),
        )
        for o in obligations:
            actor_id = o["obligor_person_id"]
            if not actor_id:
                continue
            actor = self.db.one("SELECT current_place_id FROM persons WHERE person_id=? AND alive=1", (actor_id,))
            if not actor:
                continue
            sid = stable_id("SCENE", self.run_id, "obligation_due", o["obligation_id"])
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                with self.db.transaction() as con:
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (sid, self.run_id, day, actor["current_place_id"], "household", "obligation_due",
                         canonical_json({"obligation_id": o["obligation_id"]}), "{}",
                         canonical_json({"reciprocity_and_reputation": True}), canonical_json(["I-MARKET"]), "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, actor_id, "decision_actor"))
                created.append(self.enqueue_job(
                    sid, actor_id,
                    ["transfer_resource", "communicate", "enter_obligation", "refuse_proposal", "seek_mediation"],
                ))

        debts = self.db.all(
            "SELECT * FROM debts WHERE status='open' AND outstanding>0 AND due_day IS NOT NULL AND due_day<=? ORDER BY debt_id",
            (day,),
        )
        for d in debts:
            actor = self.db.one(
                "SELECT p.person_id,p.current_place_id FROM persons p JOIN household_memberships hm USING(person_id) "
                "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 "
                "ORDER BY CASE hm.membership_role WHEN 'senior' THEN 0 ELSE 1 END,p.person_id LIMIT 1",
                (d["debtor_household_id"],),
            )
            creditor = self.db.one(
                "SELECT p.person_id FROM persons p JOIN household_memberships hm USING(person_id) "
                "WHERE hm.household_id=? AND hm.until_day IS NULL AND p.alive=1 "
                "ORDER BY CASE hm.membership_role WHEN 'senior' THEN 0 ELSE 1 END,p.person_id LIMIT 1",
                (d["creditor_household_id"],),
            )
            if not actor or not creditor:
                continue
            sid = stable_id("SCENE", self.run_id, "debt_due", d["debt_id"], d["due_day"])
            if not self.db.one("SELECT 1 FROM scenes WHERE scene_id=?", (sid,)):
                stakes = {
                    "debt_id": d["debt_id"], "resource": d["resource_type"], "outstanding": d["outstanding"],
                    "due_day": d["due_day"], "creditor_household_id": d["creditor_household_id"],
                    "creditor_person_id": creditor["person_id"],
                }
                with self.db.transaction() as con:
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (sid, self.run_id, day, actor["current_place_id"], "economic", "debt_due",
                         canonical_json(stakes), canonical_json({"resource": d["resource_type"], "outstanding": d["outstanding"]}),
                         canonical_json({"credit_reputation": True, "household_security": True}),
                         canonical_json(["I-MARKET"]), "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, actor["person_id"], "decision_actor"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (sid, creditor["person_id"], "creditor"))
                created.append(self.enqueue_job(
                    sid, actor["person_id"],
                    ["repay_debt", "request_debt_extension", "request_resource", "communicate", "seek_mediation", "refuse_proposal"],
                ))

        for s in self.db.all(
            "SELECT s.* FROM scenes s LEFT JOIN cognition_jobs j USING(scene_id) "
            "WHERE s.run_id=? AND s.trigger_type='minor_illness' AND j.job_id IS NULL ORDER BY s.scene_id",
            (self.run_id,),
        ):
            actor = self.db.one(
                "SELECT person_id FROM scene_participants WHERE scene_id=? ORDER BY person_id LIMIT 1", (s["scene_id"],)
            )[0]
            created.append(self.enqueue_job(s["scene_id"], actor, ["perform_ritual", "communicate", "travel", "refuse_proposal"]))
        return created

    def enqueue_job(self, scene_id: str, actor_person_id: str, allowed_actions: list[str]) -> str:
        job_id = stable_id("JOB", self.run_id, scene_id, actor_person_id)
        if self.db.one("SELECT 1 FROM cognition_jobs WHERE job_id=?", (job_id,)):
            return job_id
        scene = self.db.one("SELECT day FROM scenes WHERE scene_id=?", (scene_id,))
        placeholder = {"job_id": job_id, "state": "packet_compilation_pending"}
        with self.db.transaction() as con:
            con.execute(
                "INSERT INTO cognition_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (job_id, self.run_id, scene_id, actor_person_id, "cognition-v1", canonical_json(placeholder), "",
                 canonical_json(allowed_actions), "compiling", scene["day"], 0),
            )
        packet = _build_packet(self.db, job_id)
        ph = packet_hash(packet)
        with self.db.transaction() as con:
            con.execute(
                "UPDATE cognition_jobs SET packet_json=?,packet_hash=?,status='pending' WHERE job_id=?",
                (canonical_json(packet), ph, job_id),
            )
            self._event(
                con, scene["day"], "cognition_job_enqueued", scene_id=scene_id, actors=[actor_person_id],
                payload={"job_id": job_id, "packet_hash": ph}, discriminator=job_id,
            )
        return job_id

    def validate_decision(self, job_id: str, envelope: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        job = self.db.one("SELECT * FROM cognition_jobs WHERE job_id=?", (job_id,))
        if not job:
            return ValidationResult(False, ["unknown_job"])
        if job["status"] not in {"pending", "rejected"}:
            errors.append("job_not_pending")
        if envelope.get("actor_id") != job["actor_person_id"]:
            errors.append("actor_mismatch")
        actor = self.db.one("SELECT alive,available,current_place_id FROM persons WHERE person_id=?", (job["actor_person_id"],))
        if not actor or not actor["alive"]:
            errors.append("actor_not_alive")
        if actor and not actor["available"]:
            errors.append("actor_unavailable")
        packet = json.loads(job["packet_json"])
        scene_day = int(packet["scene"]["day"])
        if self.day != scene_day:
            errors.append(f"temporal_mismatch:scene_day={scene_day}:current_day={self.day}")
        admissible = {k["knowledge_id"] for k in packet.get("admissible_knowledge", [])}
        admissible_propositions = {k["proposition_id"] for k in packet.get("admissible_knowledge", [])}
        for kid in envelope.get("decisive_knowledge_or_belief_ids", []):
            if kid not in admissible:
                errors.append(f"epistemic_leak:{kid}")
        allowed = set(json.loads(job["allowed_actions_json"]))
        actions = envelope.get("proposed_actions", [])
        if not isinstance(actions, list):
            errors.append("proposed_actions_not_list")
            actions = []
        actor_household = self._household_for_person(job["actor_person_id"])
        scene_institutions = {i["institution_id"] for i in packet.get("available_institutions", [])}

        for i, action in enumerate(actions):
            typ = action.get("type")
            if typ not in allowed:
                errors.append(f"action_{i}:not_allowed:{typ}")
                continue
            if typ == "transfer_resource":
                amount = action.get("amount")
                if not isinstance(amount, (int, float)) or amount <= 0:
                    errors.append(f"action_{i}:invalid_amount")
                    continue
                target = action.get("target_household_id")
                if not self.db.one("SELECT 1 FROM households WHERE household_id=?", (target,)):
                    errors.append(f"action_{i}:invalid_target")
                resource = action.get("resource")
                stock = self.db.one(
                    "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?", (actor_household, resource)
                ) if actor_household else None
                if not stock or amount > stock["amount"]:
                    errors.append(f"action_{i}:insufficient_controlled_resource")
                social_target = action.get("social_target_person_id")
                if social_target and self._household_for_person(social_target) != target:
                    errors.append(f"action_{i}:social_target_not_in_target_household")
                if action.get("create_reciprocal_obligation"):
                    if packet.get("scene", {}).get("trigger") != "resource_request":
                        errors.append(f"action_{i}:reciprocal_obligation_requires_resource_request")
                    if not social_target:
                        errors.append(f"action_{i}:reciprocal_obligation_requires_social_target")
                obligation_id = action.get("fulfills_obligation_id")
                if obligation_id:
                    obligation = self.db.one("SELECT * FROM obligations WHERE obligation_id=?", (obligation_id,))
                    if not obligation or obligation["status"] != "active" or obligation["obligor_person_id"] != job["actor_person_id"]:
                        errors.append(f"action_{i}:invalid_obligation_fulfillment")
            elif typ == "request_resource":
                amount = action.get("amount")
                target_person = action.get("target_person_id")
                if not isinstance(amount, (int, float)) or amount <= 0:
                    errors.append(f"action_{i}:invalid_amount")
                target = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (target_person,))
                if not target or not target["alive"] or not target["available"]:
                    errors.append(f"action_{i}:invalid_target_person")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:target_not_colocated")
                if target_person == job["actor_person_id"]:
                    errors.append(f"action_{i}:cannot_request_from_self")
                if not action.get("resource"):
                    errors.append(f"action_{i}:missing_resource")
            elif typ == "recycle_finished_metalwork":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "workshop_supply_alternatives":
                    errors.append(f"action_{i}:invalid_scene_for_metal_recycling")
                input_amount=action.get("input_finished_metalwork")
                output_amount=action.get("output_metal")
                if abs(float(input_amount or 0)-float(stakes.get("recycle_input_finished_metalwork",0)))>1e-9 or abs(float(output_amount or 0)-float(stakes.get("recycle_output_metal",0)))>1e-9:
                    errors.append(f"action_{i}:recycling_terms_mismatch")
                stock=self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='finished_metalwork'",(actor_household,)) if actor_household else None
                if not stock or not isinstance(input_amount,(int,float)) or float(stock["amount"])+1e-9<float(input_amount):
                    errors.append(f"action_{i}:insufficient_finished_metalwork")
            elif typ == "request_market_introduction":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "workshop_supply_alternatives":
                    errors.append(f"action_{i}:invalid_scene_for_market_introduction_request")
                if action.get("target_person_id") != stakes.get("possible_introduction_person_id") or action.get("requested_contact_person_id") != stakes.get("possible_harbor_contact_person_id"):
                    errors.append(f"action_{i}:market_introduction_party_mismatch")
            elif typ == "grant_market_introduction":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "market_introduction_request":
                    errors.append(f"action_{i}:invalid_scene_for_market_introduction_grant")
                if job["actor_person_id"] != stakes.get("merchant_person_id") or action.get("requester_person_id") != stakes.get("requester_person_id") or action.get("contact_person_id") != stakes.get("contact_person_id"):
                    errors.append(f"action_{i}:market_introduction_terms_mismatch")
            elif typ == "accept_alternate_metal_exchange":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "alternate_metal_exchange_offer":
                    errors.append(f"action_{i}:invalid_scene_for_alt_metal_acceptance")
                for k in ("silver_cost","metal_amount","delivery_days"):
                    if abs(float(action.get(k,0))-float(stakes.get(k,0)))>1e-9:
                        errors.append(f"action_{i}:alternate_accept_{k}_mismatch")
                silver=self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='silver'",(actor_household,)) if actor_household else None
                if not silver or float(silver["amount"])+1e-9<float(action.get("silver_cost",0)):
                    errors.append(f"action_{i}:insufficient_silver_for_alternate_exchange")
            elif typ == "repay_debt":
                debt = self.db.one("SELECT * FROM debts WHERE debt_id=?", (action.get("debt_id"),))
                amount = action.get("amount")
                if not debt or debt["status"] != "open" or debt["debtor_household_id"] != actor_household:
                    errors.append(f"action_{i}:invalid_debt")
                elif not isinstance(amount, (int, float)) or amount <= 0 or amount > debt["outstanding"]:
                    errors.append(f"action_{i}:invalid_repayment_amount")
                else:
                    stock = self.db.one(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?",
                        (actor_household, debt["resource_type"]),
                    )
                    if not stock or amount > stock["amount"]:
                        errors.append(f"action_{i}:insufficient_repayment_resource")
                cp = action.get("creditor_person_id")
                if cp and debt and self._household_for_person(cp) != debt["creditor_household_id"]:
                    errors.append(f"action_{i}:creditor_person_mismatch")
            elif typ == "request_debt_extension":
                debt = self.db.one("SELECT * FROM debts WHERE debt_id=?", (action.get("debt_id"),))
                target_person = action.get("target_person_id")
                new_due = action.get("new_due_day")
                if not debt or debt["status"] != "open" or debt["debtor_household_id"] != actor_household:
                    errors.append(f"action_{i}:invalid_debt")
                if not target_person or (debt and self._household_for_person(target_person) != debt["creditor_household_id"]):
                    errors.append(f"action_{i}:invalid_creditor_person")
                target = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (target_person,)) if target_person else None
                if not target or not target["alive"] or not target["available"]:
                    errors.append(f"action_{i}:creditor_unavailable")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:creditor_not_colocated")
                if not isinstance(new_due, int) or new_due <= self.day:
                    errors.append(f"action_{i}:invalid_new_due_day")
            elif typ == "accept_debt_extension":
                debt = self.db.one("SELECT * FROM debts WHERE debt_id=?", (action.get("debt_id"),))
                new_due = action.get("new_due_day")
                if not debt or debt["status"] != "open" or debt["creditor_household_id"] != actor_household:
                    errors.append(f"action_{i}:invalid_creditor_debt")
                requested = packet.get("scene", {}).get("stakes", {}).get("new_due_day")
                if not isinstance(new_due, int) or new_due <= self.day or (requested is not None and new_due != requested):
                    errors.append(f"action_{i}:invalid_extension_due_day")
            elif typ == "request_household_work_agreement":
                stakes = packet.get("scene", {}).get("stakes", {})
                target_person = action.get("target_person_id")
                if packet.get("scene", {}).get("trigger") != "outside_work_opportunity":
                    errors.append(f"action_{i}:invalid_scene_for_work_request")
                if stakes.get("worker_person_id") != job["actor_person_id"]:
                    errors.append(f"action_{i}:worker_mismatch")
                if target_person != stakes.get("household_senior_person_id"):
                    errors.append(f"action_{i}:invalid_household_senior")
                target = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (target_person,)) if target_person else None
                if not target or not target["alive"] or not target["available"]:
                    errors.append(f"action_{i}:household_senior_unavailable")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:household_senior_not_colocated")
                if target_person and self._household_for_person(target_person) != actor_household:
                    errors.append(f"action_{i}:household_senior_not_same_household")
            elif typ == "accept_fixture_work":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "household_work_request":
                    errors.append(f"action_{i}:invalid_scene_for_work_acceptance")
                if action.get("work_id") != stakes.get("work_id"):
                    errors.append(f"action_{i}:work_id_mismatch")
                worker_id = stakes.get("worker_person_id")
                if not worker_id or self._household_for_person(worker_id) != actor_household:
                    errors.append(f"action_{i}:worker_not_in_household")
            elif typ == "decline_fixture_work":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "outside_work_opportunity":
                    errors.append(f"action_{i}:invalid_scene_for_work_decline")
                if action.get("work_id") != stakes.get("work_id"):
                    errors.append(f"action_{i}:work_id_mismatch")
            elif typ == "request_water_access":
                stakes = packet.get("scene", {}).get("stakes", {})
                target_person = action.get("target_person_id")
                requested_days = action.get("requested_days")
                if packet.get("scene", {}).get("trigger") != "water_access_pressure":
                    errors.append(f"action_{i}:invalid_scene_for_water_request")
                if target_person != stakes.get("access_holder_person_id"):
                    errors.append(f"action_{i}:invalid_water_access_holder")
                if not isinstance(requested_days, int) or requested_days < 1 or requested_days > 7:
                    errors.append(f"action_{i}:invalid_requested_days")
                target = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (target_person,)) if target_person else None
                if not target or not target["alive"] or not target["available"]:
                    errors.append(f"action_{i}:water_access_holder_unavailable")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:water_access_holder_not_colocated")
                actor_h = self.db.one("SELECT status_json FROM households WHERE household_id=?", (actor_household,)) if actor_household else None
                target_household = self._household_for_person(target_person) if target_person else None
                target_h = self.db.one("SELECT status_json FROM households WHERE household_id=?", (target_household,)) if target_household else None
                if not actor_h or json.loads(actor_h[0]).get("water_access") != "shared":
                    errors.append(f"action_{i}:requester_not_shared_access_household")
                if not target_h or json.loads(target_h[0]).get("water_access") != "private":
                    errors.append(f"action_{i}:target_not_private_access_household")
            elif typ == "grant_water_access":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "water_access_request":
                    errors.append(f"action_{i}:invalid_scene_for_water_grant")
                requested_days = stakes.get("requested_days")
                if action.get("requested_days") != requested_days:
                    errors.append(f"action_{i}:requested_days_mismatch")
                requester_id = stakes.get("requester_person_id")
                if not requester_id or self._household_for_person(requester_id) != stakes.get("requester_household_id"):
                    errors.append(f"action_{i}:invalid_water_requester")
                if actor_household != stakes.get("access_holder_household_id"):
                    errors.append(f"action_{i}:grantor_household_mismatch")
            elif typ == "contribute_communal_feast":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "communal_feast_contribution":
                    errors.append(f"action_{i}:invalid_scene_for_feast_contribution")
                grain = action.get("grain_amount", 0)
                ritual = action.get("ritual_goods_amount", 0)
                if not isinstance(grain, (int, float)) or not isinstance(ritual, (int, float)) or grain < 0 or ritual < 0 or grain + ritual <= 0:
                    errors.append(f"action_{i}:invalid_contribution_amount")
                else:
                    if grain > float(stakes.get("max_grain_contribution", 0)) + 1e-9 or ritual > float(stakes.get("max_ritual_goods_contribution", 0)) + 1e-9:
                        errors.append(f"action_{i}:contribution_exceeds_scene_limit")
                    for resource, amount in (("grain", grain), ("ritual_goods", ritual)):
                        if amount <= 0:
                            continue
                        stock = self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?", (actor_household, resource)) if actor_household else None
                        if not stock or amount > float(stock["amount"]) + 1e-9:
                            errors.append(f"action_{i}:insufficient_{resource}")
            elif typ == "decline_feast_contribution":
                if packet.get("scene", {}).get("trigger") != "communal_feast_contribution":
                    errors.append(f"action_{i}:invalid_scene_for_feast_decline")
            elif typ == "accept_palace_labor":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "institutional_labor_conflict":
                    errors.append(f"action_{i}:invalid_scene_for_palace_labor")
                obligation = self.db.one("SELECT * FROM obligations WHERE obligation_id=?", (action.get("obligation_id"),))
                if not obligation or obligation["status"] != "active" or obligation["obligation_type"] != "palace_labor" or obligation["obligor_person_id"] != job["actor_person_id"]:
                    errors.append(f"action_{i}:invalid_palace_labor_obligation")
                if action.get("obligation_id") != stakes.get("obligation_id"):
                    errors.append(f"action_{i}:palace_labor_obligation_mismatch")
            elif typ == "reschedule_palace_labor":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "institutional_labor_conflict":
                    errors.append(f"action_{i}:invalid_scene_for_palace_reschedule")
                obligation = self.db.one("SELECT * FROM obligations WHERE obligation_id=?", (action.get("obligation_id"),))
                if not obligation or obligation["status"] != "active" or obligation["obligation_type"] != "palace_labor" or obligation["obligor_person_id"] != job["actor_person_id"]:
                    errors.append(f"action_{i}:invalid_palace_labor_obligation")
                requested = action.get("new_due_day")
                if requested != stakes.get("suggested_reschedule_day"):
                    errors.append(f"action_{i}:invalid_palace_reschedule_day")
            elif typ == "request_marriage_discussion":
                stakes = packet.get("scene", {}).get("stakes", {})
                target = action.get("target_person_id")
                if packet.get("scene", {}).get("trigger") != "marriage_discussion_opportunity":
                    errors.append(f"action_{i}:invalid_scene_for_marriage_discussion")
                if job["actor_person_id"] != stakes.get("initiator_person_id") or target != stakes.get("prospective_partner_person_id"):
                    errors.append(f"action_{i}:marriage_discussion_party_mismatch")
                if not self._is_unmarried(job["actor_person_id"]) or not self._is_unmarried(target):
                    errors.append(f"action_{i}:marriage_party_not_unmarried")
                target_row = self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?", (target,)) if target else None
                if not target_row or not target_row["alive"] or not target_row["available"]:
                    errors.append(f"action_{i}:marriage_target_unavailable")
                elif actor and target_row["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:marriage_target_not_colocated")
            elif typ == "accept_marriage_discussion":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "marriage_discussion_request":
                    errors.append(f"action_{i}:invalid_scene_for_marriage_discussion_acceptance")
                if job["actor_person_id"] != stakes.get("prospective_partner_person_id"):
                    errors.append(f"action_{i}:prospective_partner_mismatch")
                if not self._is_unmarried(job["actor_person_id"]) or not self._is_unmarried(stakes.get("initiator_person_id")):
                    errors.append(f"action_{i}:marriage_party_not_unmarried")
            elif typ == "propose_marriage_household_terms":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "marriage_household_terms":
                    errors.append(f"action_{i}:invalid_scene_for_marriage_terms")
                if job["actor_person_id"] != stakes.get("initiator_household_senior_person_id"):
                    errors.append(f"action_{i}:marriage_terms_negotiator_mismatch")
                residence = action.get("residence_household_id")
                if residence not in {"H-WIDOW", "H-RITUAL"}:
                    errors.append(f"action_{i}:invalid_marriage_residence")
                if action.get("target_household_senior_person_id") != stakes.get("partner_household_senior_person_id"):
                    errors.append(f"action_{i}:invalid_marriage_terms_target")
                if not isinstance(action.get("continue_p16_care_to_p15"), bool):
                    errors.append(f"action_{i}:invalid_care_term")
            elif typ == "accept_marriage_household_terms":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "marriage_household_terms_review":
                    errors.append(f"action_{i}:invalid_scene_for_marriage_terms_acceptance")
                if job["actor_person_id"] != stakes.get("partner_household_senior_person_id"):
                    errors.append(f"action_{i}:marriage_terms_reviewer_mismatch")
                if action.get("residence_household_id") != stakes.get("residence_household_id"):
                    errors.append(f"action_{i}:marriage_residence_term_mismatch")
                if action.get("continue_p16_care_to_p15") != stakes.get("continue_p16_care_to_p15"):
                    errors.append(f"action_{i}:marriage_care_term_mismatch")
            elif typ == "give_marriage_consent":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "marriage_final_consent":
                    errors.append(f"action_{i}:invalid_scene_for_marriage_consent")
                if job["actor_person_id"] != stakes.get("consenting_person_id"):
                    errors.append(f"action_{i}:marriage_consent_actor_mismatch")
                if action.get("partner_person_id") != stakes.get("partner_person_id"):
                    errors.append(f"action_{i}:marriage_consent_partner_mismatch")
                if not self._is_unmarried(job["actor_person_id"]) or not self._is_unmarried(stakes.get("partner_person_id")):
                    errors.append(f"action_{i}:marriage_party_not_unmarried")
            elif typ == "decline_marriage_consent":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "marriage_final_consent" or job["actor_person_id"] != stakes.get("consenting_person_id"):
                    errors.append(f"action_{i}:invalid_marriage_consent_decline")
            elif typ == "preserve_seasonal_surplus":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "seasonal_surplus_storage_pressure":
                    errors.append(f"action_{i}:invalid_scene_for_surplus_preservation")
                amount = action.get("amount")
                if not isinstance(amount, (int, float)) or amount <= 0 or amount > float(stakes.get("max_preserve_amount", 0)) + 1e-9:
                    errors.append(f"action_{i}:invalid_preserve_amount")
                stock = self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='seasonal_produce'", (actor_household,)) if actor_household else None
                if not stock or not isinstance(amount, (int, float)) or amount > float(stock["amount"]) + 1e-9:
                    errors.append(f"action_{i}:insufficient_seasonal_produce")
            elif typ == "fulfill_kin_care":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "continuing_kin_care_need":
                    errors.append(f"action_{i}:invalid_scene_for_kin_care")
                oid=action.get("care_obligation_id")
                obligation=self.db.one("SELECT * FROM obligations WHERE obligation_id=?",(oid,)) if oid else None
                if not obligation or obligation["status"]!="active" or obligation["obligation_type"]!="continuing_kin_care" or obligation["obligor_person_id"]!=job["actor_person_id"]:
                    errors.append(f"action_{i}:invalid_kin_care_obligation")
                if oid != stakes.get("care_obligation_id") or action.get("support_kind") != stakes.get("support_kind"):
                    errors.append(f"action_{i}:kin_care_terms_mismatch")
            elif typ == "defer_kin_care":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "continuing_kin_care_need":
                    errors.append(f"action_{i}:invalid_scene_for_kin_care_defer")
                oid=action.get("care_obligation_id")
                obligation=self.db.one("SELECT * FROM obligations WHERE obligation_id=?",(oid,)) if oid else None
                if not obligation or obligation["status"]!="active" or obligation["obligation_type"]!="continuing_kin_care" or obligation["obligor_person_id"]!=job["actor_person_id"]:
                    errors.append(f"action_{i}:invalid_kin_care_obligation")
                if oid != stakes.get("care_obligation_id"):
                    errors.append(f"action_{i}:kin_care_obligation_mismatch")
            elif typ == "record_property_preference":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "property_preference_review":
                    errors.append(f"action_{i}:invalid_scene_for_property_preference")
                if self.db.schema_version() < 3:
                    errors.append(f"action_{i}:property_preference_schema_unavailable")
                if job["actor_person_id"] != stakes.get("holder_person_id") or action.get("beneficiary_person_id") != stakes.get("beneficiary_person_id"):
                    errors.append(f"action_{i}:property_preference_party_mismatch")
                if action.get("preference_type") != "care_informed_priority" or action.get("scope") != "household_property_if_later_negotiated":
                    errors.append(f"action_{i}:invalid_property_preference_scope")
                if self.db.one("SELECT 1 FROM property_preferences WHERE run_id=? AND household_id=? AND status='active'",(self.run_id,stakes.get("household_id"))):
                    errors.append(f"action_{i}:property_preference_already_active")
            elif typ == "request_draft_access":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "sowing_draft_access_pressure":
                    errors.append(f"action_{i}:invalid_scene_for_draft_request")
                if action.get("target_person_id") != stakes.get("access_holder_person_id") or int(action.get("service_days",0) or 0) != int(stakes.get("service_days",0) or 0):
                    errors.append(f"action_{i}:draft_request_terms_mismatch")
                if job["actor_person_id"] != stakes.get("requester_person_id"):
                    errors.append(f"action_{i}:draft_requester_mismatch")
                target=self.db.one("SELECT current_place_id,alive,available FROM persons WHERE person_id=?",(action.get("target_person_id"),)) if action.get("target_person_id") else None
                if not target or not target["alive"] or not target["available"]:
                    errors.append(f"action_{i}:draft_holder_unavailable")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:draft_holder_not_colocated")
            elif typ == "request_reciprocal_labor":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "winter_draft_maintenance_pressure":
                    errors.append(f"action_{i}:invalid_scene_for_reciprocal_labor_request")
                if job["actor_person_id"] != stakes.get("requester_person_id") or action.get("target_person_id") != stakes.get("helper_person_id"):
                    errors.append(f"action_{i}:reciprocal_labor_party_mismatch")
                if action.get("service_days") != stakes.get("service_days"):
                    errors.append(f"action_{i}:reciprocal_labor_duration_mismatch")
                rel=self.db.one("SELECT favors_given FROM relationships WHERE from_person_id=? AND to_person_id=?",(job["actor_person_id"],action.get("target_person_id")))
                if not rel or float(rel["favors_given"]) < 1.0:
                    errors.append(f"action_{i}:no_open_favor_for_reciprocal_labor")
            elif typ == "handle_winter_maintenance_internally":
                stakes=packet.get("scene",{}).get("stakes",{})
                if packet.get("scene",{}).get("trigger") != "winter_draft_maintenance_pressure" or job["actor_person_id"] != stakes.get("requester_person_id"):
                    errors.append(f"action_{i}:invalid_internal_winter_maintenance")
            elif typ == "fulfill_reciprocal_labor":
                scene_packet=packet.get("scene",{})
                stakes=scene_packet.get("stakes",{})
                effective=stakes.get("source_stakes",stakes) if scene_packet.get("trigger")=="informal_mediation_review" else stakes
                source_trigger=stakes.get("source_trigger") if scene_packet.get("trigger")=="informal_mediation_review" else scene_packet.get("trigger")
                if source_trigger != "reciprocal_labor_request":
                    errors.append(f"action_{i}:invalid_scene_for_reciprocal_labor_fulfillment")
                if job["actor_person_id"] != effective.get("helper_person_id") or action.get("requester_person_id") != effective.get("requester_person_id"):
                    errors.append(f"action_{i}:reciprocal_labor_fulfillment_party_mismatch")
                if action.get("service_days") != effective.get("service_days"):
                    errors.append(f"action_{i}:reciprocal_labor_fulfillment_duration_mismatch")
                if self.db.one("SELECT 1 FROM obligations WHERE status='scheduled' AND obligation_type='fixture_winter_reciprocal_labor'"):
                    errors.append(f"action_{i}:winter_reciprocal_labor_already_scheduled")
            elif typ == "grant_draft_access":
                scene_packet=packet.get("scene",{})
                stakes=scene_packet.get("stakes",{})
                effective=stakes.get("source_stakes",stakes) if scene_packet.get("trigger")=="informal_mediation_review" else stakes
                source_trigger=stakes.get("source_trigger") if scene_packet.get("trigger")=="informal_mediation_review" else scene_packet.get("trigger")
                if source_trigger != "draft_access_request":
                    errors.append(f"action_{i}:invalid_scene_for_draft_grant")
                if job["actor_person_id"] != effective.get("access_holder_person_id"):
                    errors.append(f"action_{i}:draft_grantor_mismatch")
                if action.get("requester_person_id") != effective.get("requester_person_id") or int(action.get("service_days",0) or 0) != int(effective.get("service_days",0) or 0):
                    errors.append(f"action_{i}:draft_grant_terms_mismatch")
                if self.db.one("SELECT 1 FROM obligations WHERE status='scheduled' AND obligation_type='fixture_draft_team_service'"):
                    errors.append(f"action_{i}:draft_service_already_scheduled")
            elif typ == "request_household_reserve_agreement":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "household_trade_reserve_priority":
                    errors.append(f"action_{i}:invalid_scene_for_reserve_request")
                if job["actor_person_id"] != stakes.get("requester_person_id"):
                    errors.append(f"action_{i}:reserve_requester_mismatch")
                if action.get("target_person_id") != stakes.get("merchant_person_id"):
                    errors.append(f"action_{i}:invalid_reserve_target")
                if action.get("resource") != "silver":
                    errors.append(f"action_{i}:invalid_reserve_resource")
                floor = action.get("reserve_floor")
                if not isinstance(floor, (int, float)) or abs(float(floor) - float(stakes.get("proposed_reserve_floor", -1))) > 1e-9:
                    errors.append(f"action_{i}:invalid_reserve_floor")
                if action.get("target_person_id") and self._household_for_person(action["target_person_id"]) != actor_household:
                    errors.append(f"action_{i}:reserve_target_not_same_household")
            elif typ == "accept_household_reserve":
                scene_packet = packet.get("scene", {})
                stakes = scene_packet.get("stakes", {})
                effective = stakes.get("source_stakes", stakes) if scene_packet.get("trigger") == "informal_mediation_review" else stakes
                source_trigger = stakes.get("source_trigger") if scene_packet.get("trigger") == "informal_mediation_review" else scene_packet.get("trigger")
                if source_trigger != "household_reserve_request":
                    errors.append(f"action_{i}:invalid_scene_for_reserve_acceptance")
                if job["actor_person_id"] != effective.get("merchant_person_id"):
                    errors.append(f"action_{i}:reserve_acceptor_mismatch")
                if action.get("resource") != effective.get("resource") or action.get("resource") != "silver":
                    errors.append(f"action_{i}:reserve_resource_mismatch")
                floor = action.get("reserve_floor")
                if not isinstance(floor, (int, float)) or abs(float(floor) - float(effective.get("reserve_floor", -1))) > 1e-9:
                    errors.append(f"action_{i}:reserve_floor_mismatch")
                stock = self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='silver'", (actor_household,)) if actor_household else None
                if not stock or float(floor or 0) > float(stock["amount"]) + 1e-9:
                    errors.append(f"action_{i}:reserve_exceeds_current_stock")
                if self._active_household_reserve_floor(actor_household, "silver") is not None:
                    errors.append(f"action_{i}:reserve_already_active")
            elif typ == "request_apprenticeship_progression":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "apprenticeship_progression_review":
                    errors.append(f"action_{i}:invalid_scene_for_apprentice_request")
                if job["actor_person_id"] != stakes.get("apprentice_person_id"):
                    errors.append(f"action_{i}:apprentice_requester_mismatch")
                if action.get("target_person_id") != stakes.get("master_person_id"):
                    errors.append(f"action_{i}:invalid_master_target")
                if action.get("requested_recognition") != stakes.get("proposed_recognition"):
                    errors.append(f"action_{i}:invalid_requested_recognition")
            elif typ == "grant_apprenticeship_progression":
                scene_packet = packet.get("scene", {})
                stakes = scene_packet.get("stakes", {})
                effective = stakes.get("source_stakes", stakes) if scene_packet.get("trigger") == "informal_mediation_review" else stakes
                source_trigger = stakes.get("source_trigger") if scene_packet.get("trigger") == "informal_mediation_review" else scene_packet.get("trigger")
                if source_trigger != "apprenticeship_progression_request":
                    errors.append(f"action_{i}:invalid_scene_for_apprentice_grant")
                if job["actor_person_id"] != effective.get("master_person_id"):
                    errors.append(f"action_{i}:master_mismatch")
                if action.get("apprentice_person_id") != effective.get("apprentice_person_id"):
                    errors.append(f"action_{i}:apprentice_mismatch")
                active = self.db.one(
                    "SELECT 1 FROM person_roles pr JOIN roles r USING(role_id) WHERE pr.person_id=? "
                    "AND r.name='craft_apprentice' AND pr.end_day IS NULL",
                    (effective.get("apprentice_person_id"),),
                )
                if not active:
                    errors.append(f"action_{i}:apprentice_role_not_active")
            elif typ == "commit_trade_exchange":
                stakes = packet.get("scene", {}).get("stakes", {})
                if packet.get("scene", {}).get("trigger") != "port_trade_opportunity":
                    errors.append(f"action_{i}:invalid_scene_for_trade_commitment")
                amount = action.get("silver_amount")
                if not isinstance(amount, (int, float)) or amount <= 0 or amount > float(stakes.get("max_silver_commitment", 0)) + 1e-9:
                    errors.append(f"action_{i}:invalid_trade_silver_amount")
                else:
                    stock = self.db.one("SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='silver'", (actor_household,)) if actor_household else None
                    if not stock or amount > float(stock["amount"]) + 1e-9:
                        errors.append(f"action_{i}:insufficient_trade_silver")
                    else:
                        reserve_floor = self._active_household_reserve_floor(actor_household, "silver")
                        if reserve_floor is not None and float(stock["amount"]) - float(amount) < reserve_floor - 1e-9:
                            errors.append(f"action_{i}:household_reserve_floor_violation")
            elif typ == "send_message":
                target_person = action.get("target_person_id")
                if target_person == job["actor_person_id"]:
                    errors.append(f"action_{i}:cannot_message_self")
                route = self._direct_message_route(job["actor_person_id"], target_person) if target_person else None
                if not route:
                    errors.append(f"action_{i}:no_accessible_message_route")
                content = action.get("content")
                if not isinstance(content, str) or not content.strip():
                    errors.append(f"action_{i}:empty_content")
                elif len(content) > 500:
                    errors.append(f"action_{i}:content_too_long")
                intent = action.get("sender_intent")
                if intent not in {"inquiry", "report"}:
                    errors.append(f"action_{i}:invalid_sender_intent")
                proposition_id = action.get("proposition_id")
                if intent == "inquiry" and proposition_id is not None:
                    errors.append(f"action_{i}:inquiry_must_not_transmit_proposition")
                if intent == "report":
                    if not proposition_id:
                        errors.append(f"action_{i}:report_requires_proposition")
                    elif proposition_id not in admissible_propositions:
                        errors.append(f"action_{i}:epistemic_leak_proposition:{proposition_id}")
            elif typ == "communicate":
                target_person = action.get("target_person_id")
                target = self.db.one("SELECT current_place_id,alive FROM persons WHERE person_id=?", (target_person,))
                if not target or not target["alive"]:
                    errors.append(f"action_{i}:invalid_target_person")
                elif actor and target["current_place_id"] != actor["current_place_id"]:
                    errors.append(f"action_{i}:target_not_colocated")
                if not isinstance(action.get("content"), str) or not action.get("content", "").strip():
                    errors.append(f"action_{i}:empty_content")
            elif typ == "enter_obligation":
                bp = action.get("beneficiary_person_id")
                bh = action.get("beneficiary_household_id")
                if not bp and not bh:
                    errors.append(f"action_{i}:missing_beneficiary")
                if bp and not self.db.one("SELECT 1 FROM persons WHERE person_id=?", (bp,)):
                    errors.append(f"action_{i}:invalid_beneficiary_person")
                if bh and not self.db.one("SELECT 1 FROM households WHERE household_id=?", (bh,)):
                    errors.append(f"action_{i}:invalid_beneficiary_household")
                due = action.get("due_day")
                if due is not None and (not isinstance(due, int) or due < self.day):
                    errors.append(f"action_{i}:invalid_due_day")
                if not action.get("description"):
                    errors.append(f"action_{i}:missing_description")
            elif typ == "perform_ritual":
                cost = action.get("ritual_goods_cost", 0)
                if not isinstance(cost, (int, float)) or cost < 0:
                    errors.append(f"action_{i}:invalid_ritual_cost")
                    continue
                stock = self.db.one(
                    "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='ritual_goods'",
                    (actor_household,),
                ) if actor_household else None
                if not stock or cost > stock["amount"]:
                    errors.append(f"action_{i}:insufficient_ritual_goods")
            elif typ == "seek_mediation":
                iid = action.get("institution_id")
                if iid not in scene_institutions:
                    errors.append(f"action_{i}:institution_not_available")
            elif typ == "travel":
                dest = action.get("to_place_id")
                if not self.db.one("SELECT 1 FROM places WHERE place_id=?", (dest,)):
                    errors.append(f"action_{i}:invalid_destination")
                elif actor and not self.db.one(
                    "SELECT 1 FROM routes WHERE from_place_id=? AND to_place_id=? AND accessible=1",
                    (actor["current_place_id"], dest),
                ):
                    errors.append(f"action_{i}:unreachable_destination")
        return ValidationResult(not errors, errors)

    def submit_decision(self, job_id: str, envelope: dict[str, Any]) -> ValidationResult:
        result = self.validate_decision(job_id, envelope)
        job = self.db.one("SELECT * FROM cognition_jobs WHERE job_id=?", (job_id,))
        decision_id = envelope.get("decision_id") or stable_id("DEC", job_id, canonical_json(envelope))
        day = self.day
        if not result.ok:
            with self.db.transaction() as con:
                con.execute(
                    "INSERT OR REPLACE INTO decisions VALUES (?,?,?,?,?,?,?,?)",
                    (decision_id, job_id, job["actor_person_id"], canonical_json(envelope), "rejected",
                     canonical_json(result.errors), day, None),
                )
                con.execute(
                    "UPDATE cognition_jobs SET status='rejected',correction_attempts=correction_attempts+1 WHERE job_id=?",
                    (job_id,),
                )
                self._event(
                    con, day, "decision_rejected", scene_id=job["scene_id"], decision_id=decision_id,
                    actors=[job["actor_person_id"]], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                    payload={"errors": result.errors}, discriminator=decision_id,
                )
            return result

        followups: list[tuple[str, str, list[str]]] = []
        with self.db.transaction() as con:
            con.execute(
                "INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?)",
                (decision_id, job_id, job["actor_person_id"], canonical_json(envelope), "accepted", "[]", day, day),
            )
            scene = con.execute("SELECT * FROM scenes WHERE scene_id=?", (job["scene_id"],)).fetchone()
            scene_stakes = json.loads(scene["stakes_json"])
            actor_id = job["actor_person_id"]
            actor_household = con.execute(
                "SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL", (actor_id,)
            ).fetchone()[0]

            for idx, action in enumerate(envelope.get("proposed_actions", [])):
                aid = stable_id("ACT", decision_id, idx)
                typ = action["type"]
                con.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?)", (aid, decision_id, idx, typ, canonical_json(action), "accepted", None))

                if typ == "transfer_resource":
                    target = action["target_household_id"]
                    resource = action["resource"]
                    amount = float(action["amount"])
                    current = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?", (actor_household, resource)
                    ).fetchone()
                    if current is None or current[0] < amount:
                        raise ValueError("material precondition changed before apply")
                    con.execute(
                        "UPDATE resource_stocks SET amount=amount-? WHERE household_id=? AND resource_type=?",
                        (amount, actor_household, resource),
                    )
                    target_stock = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?", (target, resource)
                    ).fetchone()
                    if target_stock:
                        con.execute(
                            "UPDATE resource_stocks SET amount=amount+? WHERE household_id=? AND resource_type=?",
                            (amount, target, resource),
                        )
                    else:
                        con.execute(
                            "INSERT INTO resource_stocks VALUES (?,?,?,?,?)",
                            (target, resource, amount, "abstract_fixture_unit", "ASM-FIXTURE-001"),
                        )
                    causes = [scene_stakes["request_event_id"]] if scene_stakes.get("request_event_id") else []
                    relationship_delta: dict[str, Any] = {}
                    target_person = action.get("social_target_person_id")
                    obligation_id = action.get("fulfills_obligation_id")
                    if target_person and scene["trigger_type"] == "resource_request":
                        self._ensure_relationship_pair(con, actor_id, target_person, relationship_type="exchange_contact")
                    if obligation_id:
                        obligation = con.execute("SELECT * FROM obligations WHERE obligation_id=?", (obligation_id,)).fetchone()
                        con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (obligation_id,))
                        target_person = obligation["beneficiary_person_id"] or target_person
                        if target_person:
                            reciprocal_return = obligation["obligation_type"] == "reciprocal_exchange"
                            relationship_delta[f"{actor_id}->{target_person}"] = self._adjust_relationship(
                                con, actor_id, target_person, trust=.03, respect=.01,
                                favors_owed=-1 if reciprocal_return else 0
                            )
                            relationship_delta[f"{target_person}->{actor_id}"] = self._adjust_relationship(
                                con, target_person, actor_id, trust=.04, respect=.02,
                                favors_given=-1 if reciprocal_return else 0
                            )
                    elif target_person:
                        relationship_delta[f"{actor_id}->{target_person}"] = self._adjust_relationship(
                            con, actor_id, target_person, favors_given=1
                        )
                        relationship_delta[f"{target_person}->{actor_id}"] = self._adjust_relationship(
                            con, target_person, actor_id, trust=.02, favors_owed=1
                        )
                    reciprocal_obligation_id = None
                    if action.get("create_reciprocal_obligation") and target_person:
                        reciprocal_obligation_id = stable_id("O", self.run_id, "reciprocal_exchange", decision_id, idx)
                        description = action.get("reciprocal_obligation_description") or (
                            f"{target_person} and household owe a future reciprocal return for {amount:g} {resource} supplied by {actor_id}."
                        )
                        reciprocal_provenance={
                            "assumption_id":"ASM-FIXTURE-013",
                            "rule_id":"RULE-RECIPROCAL-SOCIAL-CREDIT-001",
                            "origin_scene_id":job["scene_id"],
                            "notice":"Open-ended reciprocal social credit; no historical price, interest, or maturity rate claimed."
                        }
                        if self._has_assumption("ASM-FIXTURE-026"):
                            reciprocal_provenance["origin_resource"]=resource
                            reciprocal_provenance["origin_amount"]=amount
                            reciprocal_provenance["return_cap_assumption_id"]="ASM-FIXTURE-026"
                        con.execute(
                            "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (reciprocal_obligation_id,target_person,target,actor_id,actor_household,"reciprocal_exchange",
                             description,None,"active",canonical_json(reciprocal_provenance)),
                        )
                    transfer_payload = {"action_id": aid, "fulfills_obligation_id": obligation_id}
                    if reciprocal_obligation_id:
                        transfer_payload["reciprocal_obligation_id"] = reciprocal_obligation_id
                    eid = self._event(
                        con, day, "resource_transfer", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id] + ([target_person] if target_person else []), causes=causes,
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["RULE-ATOMIC-EVENT-001"] + (["ASM-FIXTURE-013", "RULE-RECIPROCAL-SOCIAL-CREDIT-001"] if reciprocal_obligation_id else []),
                        material={actor_household: {resource: -amount}, target: {resource: amount}},
                        relationships=relationship_delta,
                        payload=transfer_payload, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Transferred {amount:g} {resource} to {target}.", event_id=eid,
                        memory_type="resource_exchange", salience=.72, relationship_relevance=.7, goal_relevance=.7,
                    )
                    if target_person:
                        target_summary = f"{actor_id} transferred {amount:g} {resource} to my household."
                        if reciprocal_obligation_id:
                            target_summary += " I now carry an open reciprocal obligation for that support."
                        self._memory(
                            con, target_person, day, target_summary,
                            event_id=eid, memory_type="resource_exchange", salience=.82 if reciprocal_obligation_id else .78,
                            relationship_relevance=.9 if reciprocal_obligation_id else .85, goal_relevance=.7 if reciprocal_obligation_id else .6,
                            provenance={"reciprocal_obligation_id":reciprocal_obligation_id} if reciprocal_obligation_id else {},
                        )

                elif typ == "perform_ritual":
                    cost = float(action.get("ritual_goods_cost", 0))
                    current = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='ritual_goods'", (actor_household,)
                    ).fetchone()[0]
                    if current < cost:
                        raise ValueError("ritual material precondition changed")
                    con.execute(
                        "UPDATE resource_stocks SET amount=amount-? WHERE household_id=? AND resource_type='ritual_goods'",
                        (cost, actor_household),
                    )
                    eid = self._event(
                        con, day, "ritual_performed", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["RULE-RITUAL-AFFORDANCE-001", "ASM-UGA-003"],
                        material={actor_household: {"ritual_goods": -cost}},
                        payload={"action_id": aid, "ritual_kind": action.get("ritual_kind", "unspecified"),
                                 "practical_response": action.get("practical_response")}, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day,
                        f"Responded to illness with {action.get('ritual_kind', 'a household rite')}"
                        + (f" and {action.get('practical_response')}" if action.get('practical_response') else "") + ".",
                        event_id=eid, memory_type="ritual_health", emotional_weight=.6, salience=.7,
                        relationship_relevance=.2, goal_relevance=.6,
                    )

                elif typ == "repay_debt":
                    debt = con.execute("SELECT * FROM debts WHERE debt_id=?", (action["debt_id"],)).fetchone()
                    amount = float(action["amount"])
                    creditor_household = debt["creditor_household_id"]
                    resource = debt["resource_type"]
                    current = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type=?", (actor_household, resource)
                    ).fetchone()[0]
                    if current < amount or debt["outstanding"] < amount:
                        raise ValueError("debt repayment precondition changed")
                    con.execute("UPDATE resource_stocks SET amount=amount-? WHERE household_id=? AND resource_type=?",
                                (amount, actor_household, resource))
                    con.execute("UPDATE resource_stocks SET amount=amount+? WHERE household_id=? AND resource_type=?",
                                (amount, creditor_household, resource))
                    remaining = float(debt["outstanding"]) - amount
                    con.execute("UPDATE debts SET outstanding=?,status=? WHERE debt_id=?",
                                (remaining, "paid" if remaining <= 1e-9 else "open", debt["debt_id"]))
                    creditor_person = action.get("creditor_person_id") or scene_stakes.get("creditor_person_id")
                    eid = self._event(
                        con, day, "debt_repayment", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id] + ([creditor_person] if creditor_person else []),
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        material={actor_household: {resource: -amount}, creditor_household: {resource: amount}},
                        payload={"action_id": aid, "debt_id": debt["debt_id"], "amount": amount, "remaining": remaining},
                        discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Repaid {amount:g} {resource} on debt {debt['debt_id']}; {remaining:g} remains.",
                                 event_id=eid, memory_type="debt", salience=.85, relationship_relevance=.65, goal_relevance=.9)
                    if creditor_person:
                        self._memory(con, creditor_person, day, f"{actor_id} repaid {amount:g} {resource} on debt {debt['debt_id']}; {remaining:g} remains.",
                                     event_id=eid, memory_type="debt", salience=.8, relationship_relevance=.7, goal_relevance=.75)

                elif typ == "request_debt_extension":
                    debt = con.execute("SELECT * FROM debts WHERE debt_id=?", (action["debt_id"],)).fetchone()
                    target_person = action["target_person_id"]
                    request_scene = stable_id("SCENE", self.run_id, day, "debt_extension_request", decision_id, idx)
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene, self.run_id, day, scene["place_id"], "economic", "debt_extension_request", "{}",
                         canonical_json({"debt_id": debt["debt_id"], "outstanding": debt["outstanding"],
                                         "current_due_day": debt["due_day"], "requested_due_day": action["new_due_day"]}),
                         canonical_json({"requester_person_id": actor_id, "target_person_id": target_person,
                                         "reason": action.get("reason", "household pressure")}),
                         canonical_json(["I-MARKET"]), "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, actor_id, "requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, target_person, "decision_actor"))
                    eid = self._event(
                        con, day, "debt_extension_requested", scene_id=request_scene, decision_id=decision_id,
                        actors=[actor_id, target_person], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "debt_id": debt["debt_id"], "new_due_day": action["new_due_day"],
                                 "reason": action.get("reason")}, discriminator=aid,
                    )
                    stakes = {"request_event_id": eid, "debt_id": debt["debt_id"], "requester_person_id": actor_id,
                              "new_due_day": action["new_due_day"], "outstanding": debt["outstanding"],
                              "reason": action.get("reason", "household pressure")}
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?", (canonical_json(stakes), request_scene))
                    self._memory(con, actor_id, day, f"Asked {target_person} to extend debt {debt['debt_id']} to day {action['new_due_day']}.",
                                 event_id=eid, memory_type="debt_negotiation", salience=.85, relationship_relevance=.75, goal_relevance=.9)
                    followups.append((request_scene, target_person, ["accept_debt_extension", "refuse_proposal", "communicate", "seek_mediation"]))

                elif typ == "accept_debt_extension":
                    debt = con.execute("SELECT * FROM debts WHERE debt_id=?", (action["debt_id"],)).fetchone()
                    old_due = debt["due_day"]
                    new_due = int(action["new_due_day"])
                    con.execute("UPDATE debts SET due_day=? WHERE debt_id=?", (new_due, debt["debt_id"]))
                    cause = scene_stakes.get("request_event_id")
                    requester = scene_stakes.get("requester_person_id")
                    eid = self._event(
                        con, day, "debt_extension_accepted", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id] + ([requester] if requester else []), causes=[cause] if cause else [],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "debt_id": debt["debt_id"], "old_due_day": old_due, "new_due_day": new_due},
                        discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Extended debt {debt['debt_id']} from day {old_due} to day {new_due}.",
                                 event_id=eid, memory_type="debt_negotiation", salience=.78, relationship_relevance=.7, goal_relevance=.75)
                    if requester:
                        self._memory(con, requester, day, f"{actor_id} extended debt {debt['debt_id']} to day {new_due}.",
                                     event_id=eid, memory_type="debt_negotiation", salience=.82, relationship_relevance=.8, goal_relevance=.9)

                elif typ == "request_household_work_agreement":
                    target_person = action["target_person_id"]
                    work_id = scene_stakes["work_id"]
                    request_scene = stable_id("SCENE", self.run_id, day, "household_work_request", decision_id, idx)
                    request_stakes = {
                        "situation_id": "SIT-006",
                        "requester_person_id": actor_id,
                        "worker_person_id": actor_id,
                        "household_senior_person_id": target_person,
                        "work_id": work_id,
                        "work_kind": scene_stakes["work_kind"],
                        "absence_days": int(scene_stakes["absence_days"]),
                        "household_receipt": scene_stakes["household_receipt"],
                        "request_reason": action.get("reason", "outside work may benefit the household"),
                        "fixture_notice": scene_stakes["fixture_notice"],
                    }
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene, self.run_id, day, scene["place_id"], "household", "household_work_request",
                         canonical_json(request_stakes), canonical_json({"absence_days": request_stakes["absence_days"],
                                                                        "household_receipt": request_stakes["household_receipt"]}),
                         canonical_json({"worker_agency": True, "household_priority_decision": True}),
                         "[]", "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, actor_id, "requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, target_person, "decision_actor"))
                    eid = self._event(
                        con, day, "household_work_agreement_requested", scene_id=request_scene, decision_id=decision_id,
                        actors=[actor_id, target_person], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-006", "RULE-HOUSEHOLD-WORK-NEGOTIATION-001"],
                        payload={"action_id": aid, "work_id": work_id, "reason": action.get("reason")}, discriminator=aid,
                    )
                    request_stakes["request_event_id"] = eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?", (canonical_json(request_stakes), request_scene))
                    self._memory(
                        con, actor_id, day, f"Asked {target_person} to agree that I take the outside work opportunity {work_id}.",
                        event_id=eid, memory_type="household_work", salience=.72, relationship_relevance=.8, goal_relevance=.85,
                        provenance={"assumption_id": "ASM-FIXTURE-006"},
                    )
                    self._memory(
                        con, target_person, day, f"{actor_id} asked to take outside work {work_id}; household labor and the fixture receipt are both at stake.",
                        event_id=eid, memory_type="household_work", salience=.7, relationship_relevance=.8, goal_relevance=.75,
                        provenance={"assumption_id": "ASM-FIXTURE-006"},
                    )
                    self._adjust_relationship(con, actor_id, target_person)
                    self._adjust_relationship(con, target_person, actor_id)
                    followups.append((request_scene, target_person, ["accept_fixture_work", "refuse_proposal", "communicate"]))

                elif typ == "accept_fixture_work":
                    worker_id = scene_stakes["worker_person_id"]
                    compensation = scene_stakes["household_receipt"]
                    absence_days = int(scene_stakes["absence_days"])
                    completion_day = day + absence_days
                    oid = stable_id("O", self.run_id, "fixture_outside_work", scene_stakes["work_id"], decision_id)
                    provenance = {
                        "assumption_id": "ASM-FIXTURE-006",
                        "rule_id": "RULE-HOUSEHOLD-WORK-NEGOTIATION-001",
                        "work_id": scene_stakes["work_id"],
                        "resource": compensation["resource"],
                        "amount": float(compensation["amount"]),
                        "household_senior_person_id": actor_id,
                        "request_event_id": scene_stakes.get("request_event_id"),
                        "notice": "fixture work timing/receipt; not a historical wage or contract",
                    }
                    con.execute(
                        "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid, worker_id, actor_household, actor_id, actor_household, "fixture_outside_work",
                         f"Complete fixture outside work {scene_stakes['work_id']} for the household.",
                         completion_day, "scheduled", canonical_json(provenance)),
                    )
                    relationship_delta = {
                        f"{actor_id}->{worker_id}": self._adjust_relationship(con, actor_id, worker_id, trust=.01, respect=.01),
                        f"{worker_id}->{actor_id}": self._adjust_relationship(con, worker_id, actor_id, trust=.02, respect=.01),
                    }
                    eid = self._event(
                        con, day, "household_work_agreed", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id, worker_id], causes=[scene_stakes["request_event_id"]] if scene_stakes.get("request_event_id") else [],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-006", "RULE-HOUSEHOLD-WORK-NEGOTIATION-001"],
                        relationships=relationship_delta,
                        payload={"action_id": aid, "work_id": scene_stakes["work_id"], "completion_day": completion_day,
                                 "scheduled_obligation_id": oid, "household_receipt": compensation}, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Agreed that {worker_id} may take outside work {scene_stakes['work_id']}; completion is expected on day {completion_day}.",
                        event_id=eid, memory_type="household_work", salience=.74, relationship_relevance=.8, goal_relevance=.75,
                        provenance={"assumption_id": "ASM-FIXTURE-006"},
                    )
                    self._memory(
                        con, worker_id, day, f"{actor_id} agreed that I may take outside work {scene_stakes['work_id']} for the household.",
                        event_id=eid, memory_type="household_work", salience=.78, relationship_relevance=.85, goal_relevance=.85,
                        provenance={"assumption_id": "ASM-FIXTURE-006"},
                    )

                elif typ == "decline_fixture_work":
                    eid = self._event(
                        con, day, "fixture_work_declined", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-006", "RULE-HOUSEHOLD-WORK-NEGOTIATION-001"],
                        payload={"action_id": aid, "work_id": scene_stakes["work_id"], "reason": action.get("reason")},
                        discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Declined outside work {scene_stakes['work_id']}: {action.get('reason', 'household priorities came first')}.",
                        event_id=eid, memory_type="household_work", salience=.62, relationship_relevance=.35, goal_relevance=.72,
                        provenance={"assumption_id": "ASM-FIXTURE-006"},
                    )

                elif typ == "request_water_access":
                    target_person = action["target_person_id"]
                    target_household = self._household_for_person(target_person)
                    request_scene = stable_id("SCENE", self.run_id, day, "water_access_request", decision_id, idx)
                    request_stakes = {
                        "situation_id": "SIT-007",
                        "requester_person_id": actor_id,
                        "requester_household_id": actor_household,
                        "access_holder_person_id": target_person,
                        "access_holder_household_id": target_household,
                        "requested_days": int(action["requested_days"]),
                        "reason": action.get("reason", "temporary shared-water access disruption"),
                        "fixture_notice": scene_stakes["fixture_notice"],
                    }
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene, self.run_id, day, scene["place_id"], "household", "water_access_request",
                         canonical_json(request_stakes), canonical_json({"requested_days": request_stakes["requested_days"]}),
                         canonical_json({"negotiation_not_entitlement": True, "exact_procedure_uncertain": True}),
                         canonical_json(["I-WATER"]), "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, actor_id, "requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, target_person, "decision_actor"))
                    eid = self._event(
                        con, day, "water_access_requested", scene_id=request_scene, decision_id=decision_id,
                        actors=[actor_id, target_person], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-007", "ASM-UGA-001", "RULE-WATER-NEGOTIATION-001"],
                        institutions={"I-WATER": {"requested": True}},
                        payload={"action_id": aid, "requested_days": request_stakes["requested_days"],
                                 "reason": request_stakes["reason"]}, discriminator=aid,
                    )
                    request_stakes["request_event_id"] = eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?", (canonical_json(request_stakes), request_scene))
                    self._memory(
                        con, actor_id, day, f"Asked {target_person} for temporary water access for {request_stakes['requested_days']} day(s).",
                        event_id=eid, memory_type="water_access", salience=.75, relationship_relevance=.82, goal_relevance=.8,
                        provenance={"assumption_id": "ASM-FIXTURE-007"},
                    )
                    self._memory(
                        con, target_person, day, f"{actor_id} asked my household for temporary water access for {request_stakes['requested_days']} day(s).",
                        event_id=eid, memory_type="water_access", salience=.73, relationship_relevance=.82, goal_relevance=.72,
                        provenance={"assumption_id": "ASM-FIXTURE-007"},
                    )
                    self._adjust_relationship(con, actor_id, target_person)
                    self._adjust_relationship(con, target_person, actor_id)
                    followups.append((request_scene, target_person, ["grant_water_access", "refuse_proposal", "communicate", "seek_mediation"]))

                elif typ == "grant_water_access":
                    requester = scene_stakes["requester_person_id"]
                    requester_household = scene_stakes["requester_household_id"]
                    requested_days = int(scene_stakes["requested_days"])
                    last_access_day = day + requested_days - 1
                    oid = stable_id("O", self.run_id, "temporary_water_access", scene_stakes["request_event_id"], actor_id)
                    provenance = {
                        "assumption_id": "ASM-FIXTURE-007",
                        "rule_id": "RULE-WATER-NEGOTIATION-001",
                        "request_event_id": scene_stakes["request_event_id"],
                        "institution_id": "I-WATER",
                        "notice": "temporary fixture permission; exact historical access procedure remains uncertain",
                    }
                    con.execute(
                        "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid, actor_id, actor_household, requester, requester_household, "temporary_water_access",
                         f"Temporary negotiated water access for {requester_household} through day {last_access_day}.",
                         last_access_day, "granted", canonical_json(provenance)),
                    )
                    relationship_delta = {
                        f"{actor_id}->{requester}": self._adjust_relationship(con, actor_id, requester, trust=.01, favors_given=1),
                        f"{requester}->{actor_id}": self._adjust_relationship(con, requester, actor_id, trust=.02, respect=.01, favors_owed=1),
                    }
                    eid = self._event(
                        con, day, "water_access_granted", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id, requester], causes=[scene_stakes["request_event_id"]],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-007", "ASM-UGA-001", "RULE-WATER-NEGOTIATION-001"],
                        relationships=relationship_delta, institutions={"I-WATER": {"temporary_access": "granted"}},
                        payload={"action_id": aid, "obligation_id": oid, "requested_days": requested_days,
                                 "last_access_day": last_access_day}, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Granted {requester} temporary water access through day {last_access_day}.",
                        event_id=eid, memory_type="water_access", salience=.76, relationship_relevance=.85, goal_relevance=.65,
                        provenance={"assumption_id": "ASM-FIXTURE-007"},
                    )
                    self._memory(
                        con, requester, day, f"{actor_id} granted my household temporary water access through day {last_access_day}.",
                        event_id=eid, memory_type="water_access", salience=.82, relationship_relevance=.9, goal_relevance=.82,
                        provenance={"assumption_id": "ASM-FIXTURE-007"},
                    )

                elif typ == "contribute_communal_feast":
                    grain = float(action.get("grain_amount", 0))
                    ritual = float(action.get("ritual_goods_amount", 0))
                    material: dict[str, Any] = {actor_household: {}}
                    if grain > 0:
                        self._change_resource(con, actor_household, "grain", -grain, assumption_id="ASM-FIXTURE-010")
                        material[actor_household]["grain"] = -grain
                    if ritual > 0:
                        self._change_resource(con, actor_household, "ritual_goods", -ritual, assumption_id="ASM-FIXTURE-010")
                        material[actor_household]["ritual_goods"] = -ritual
                    eid = self._event(
                        con, day, "communal_feast_contribution", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id,"P9","P10"], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-010","RULE-COMMUNAL-FEAST-001"], material=material,
                        institutions={"I-SHRINE":{"communal_feast":"contributed"}},
                        payload={"action_id":aid,"grain_amount":grain,"ritual_goods_amount":ritual,
                                 "reason":action.get("reason")}, discriminator=aid,
                    )
                    self._memory(con,actor_id,day,
                                 f"Contributed {grain:g} grain and {ritual:g} ritual_goods to the communal rite/feast.",
                                 event_id=eid,memory_type="communal_ritual",salience=.78,relationship_relevance=.65,goal_relevance=.68,
                                 provenance={"assumption_id":"ASM-FIXTURE-010"})
                    for host in ("P9","P10"):
                        self._memory(con,host,day,
                                     f"{actor_id}'s household contributed to the communal rite/feast.",
                                     event_id=eid,memory_type="communal_ritual",salience=.58,relationship_relevance=.62,goal_relevance=.55,
                                     provenance={"assumption_id":"ASM-FIXTURE-010"})

                elif typ == "decline_feast_contribution":
                    eid = self._event(
                        con,day,"communal_feast_contribution_declined",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id,"P9","P10"],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-010","RULE-COMMUNAL-FEAST-001"],
                        institutions={"I-SHRINE":{"communal_feast":"declined_contribution"}},
                        payload={"action_id":aid,"reason":action.get("reason")},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Declined a material contribution to the communal rite/feast: {action.get('reason','household priorities')}.",
                                 event_id=eid,memory_type="communal_ritual",salience=.66,relationship_relevance=.58,goal_relevance=.72,
                                 provenance={"assumption_id":"ASM-FIXTURE-010"})
                    for host in ("P9","P10"):
                        self._memory(con,host,day,f"{actor_id}'s household did not make a material contribution to the communal rite/feast.",
                                     event_id=eid,memory_type="communal_ritual",salience=.5,relationship_relevance=.58,goal_relevance=.45,
                                     provenance={"assumption_id":"ASM-FIXTURE-010"})

                elif typ == "accept_palace_labor":
                    oid = action["obligation_id"]
                    con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?",(oid,))
                    eid = self._event(
                        con,day,"palace_labor_accepted",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-011","RULE-SEASONAL-LABOR-CONFLICT-001"],
                        institutions={"I-PALACE":{"labor_obligation":"fulfilled_during_bottleneck"}},
                        payload={"action_id":aid,"obligation_id":oid,"seasonal_context":scene_stakes.get("seasonal_context"),
                                 "reason":action.get("reason")},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,"Accepted and completed the palace labor demand despite the household seasonal labor conflict.",
                                 event_id=eid,memory_type="institutional_labor",salience=.82,relationship_relevance=.25,goal_relevance=.88,
                                 provenance={"assumption_id":"ASM-FIXTURE-011"})

                elif typ == "reschedule_palace_labor":
                    oid = action["obligation_id"]
                    new_due = int(action["new_due_day"])
                    con.execute("UPDATE obligations SET due_day=? WHERE obligation_id=?",(new_due,oid))
                    eid = self._event(
                        con,day,"palace_labor_rescheduled",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-011","RULE-SEASONAL-LABOR-CONFLICT-001"],
                        institutions={"I-PALACE":{"labor_obligation":"rescheduled_fixture"}},
                        payload={"action_id":aid,"obligation_id":oid,"new_due_day":new_due,
                                 "reason":action.get("reason"),"notice":"rescheduling is a bounded fixture mechanism, not a reconstructed Ugaritic administrative procedure"},
                        discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Moved the recorded palace labor obligation to day {new_due} so the household can pass the current seasonal bottleneck.",
                                 event_id=eid,memory_type="institutional_labor",salience=.84,relationship_relevance=.3,goal_relevance=.9,
                                 provenance={"assumption_id":"ASM-FIXTURE-011"})

                elif typ == "request_marriage_discussion":
                    target_person = action["target_person_id"]
                    self._ensure_relationship_pair(con, actor_id, target_person, relationship_type="prospective_marriage_contact")
                    request_scene = stable_id("SCENE", self.run_id, day, "marriage_discussion_request", decision_id, idx)
                    request_stakes = {
                        "situation_id":"SIT-015","requester_person_id":actor_id,
                        "initiator_person_id":actor_id,"prospective_partner_person_id":target_person,
                        "initiator_household_id":scene_stakes["initiator_household_id"],
                        "partner_household_id":scene_stakes["partner_household_id"],
                        "initiator_household_senior_person_id":"P15","partner_household_senior_person_id":"P9",
                        "request_reason":action.get("reason","ask whether to explore a marriage arrangement"),
                        "fixture_notice":scene_stakes["fixture_notice"],
                    }
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (request_scene,self.run_id,day,scene["place_id"],"household","marriage_discussion_request",
                                 canonical_json(request_stakes),"{}",
                                 canonical_json({"prospective_partner_has_independent_choice":True}),"[]","open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,actor_id,"requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,target_person,"decision_actor"))
                    eid=self._event(con,day,"marriage_discussion_requested",scene_id=request_scene,decision_id=decision_id,
                                    actors=[actor_id,target_person],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-019","RULE-MARRIAGE-NEGOTIATION-001"],
                                    payload={"action_id":aid,"reason":action.get("reason")},discriminator=aid)
                    request_stakes["request_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(request_stakes),request_scene))
                    self._memory(con,actor_id,day,f"Asked {target_person} whether to explore a marriage arrangement.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.82,relationship_relevance=.9,goal_relevance=.8,
                                 provenance={"assumption_id":"ASM-FIXTURE-019"})
                    self._memory(con,target_person,day,f"{actor_id} asked whether I would explore a marriage arrangement before any household terms are settled.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.84,relationship_relevance=.9,goal_relevance=.75,
                                 provenance={"assumption_id":"ASM-FIXTURE-019"})
                    followups.append((request_scene,target_person,["accept_marriage_discussion","refuse_proposal","communicate","wait"]))

                elif typ == "accept_marriage_discussion":
                    initiator=scene_stakes["initiator_person_id"]
                    self._adjust_relationship(con,actor_id,initiator,trust=.01,respect=.01)
                    self._adjust_relationship(con,initiator,actor_id,trust=.01,respect=.01)
                    terms_scene=stable_id("SCENE",self.run_id,day,"marriage_household_terms",decision_id,idx)
                    terms_stakes={
                        "situation_id":"SIT-015","requester_person_id":initiator,
                        "initiator_person_id":initiator,"prospective_partner_person_id":actor_id,
                        "initiator_household_id":scene_stakes["initiator_household_id"],
                        "partner_household_id":scene_stakes["partner_household_id"],
                        "initiator_household_senior_person_id":scene_stakes["initiator_household_senior_person_id"],
                        "partner_household_senior_person_id":scene_stakes["partner_household_senior_person_id"],
                        "discussion_request_event_id":scene_stakes.get("request_event_id"),
                        "fixture_notice":"Residence/care terms are bounded ASM-FIXTURE-020 options; no universal Ugaritic residence or marriage-transfer rule is claimed.",
                    }
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (terms_scene,self.run_id,day,scene["place_id"],"household","marriage_household_terms",
                                 canonical_json(terms_stakes),"{}",
                                 canonical_json({"household_strategy":True,"no_resource_transfer_implied":True}),
                                 canonical_json(["I-MEDIATION"]),"open"))
                    for pid,role in ((initiator,"prospective_spouse"),(actor_id,"prospective_spouse"),("P15","decision_actor"),("P9","other_household_senior")):
                        con.execute("INSERT OR IGNORE INTO scene_participants VALUES (?,?,?)",(terms_scene,pid,role))
                    eid=self._event(con,day,"marriage_discussion_accepted",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id,initiator],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-019","RULE-MARRIAGE-NEGOTIATION-001"],payload={"action_id":aid},discriminator=aid)
                    self._memory(con,actor_id,day,"Agreed to explore marriage terms; no marriage has been concluded.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.82,relationship_relevance=.9,goal_relevance=.75)
                    self._memory(con,initiator,day,f"{actor_id} agreed to explore marriage terms; our households still need to negotiate residence and care obligations.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.84,relationship_relevance=.9,goal_relevance=.82)
                    followups.append((terms_scene,"P15",["propose_marriage_household_terms","refuse_proposal","seek_mediation","communicate","wait"]))

                elif typ == "propose_marriage_household_terms":
                    residence=action["residence_household_id"]
                    care=bool(action["continue_p16_care_to_p15"])
                    reviewer=action["target_household_senior_person_id"]
                    review_scene=stable_id("SCENE",self.run_id,day,"marriage_household_terms_review",decision_id,idx)
                    review_stakes={
                        **scene_stakes,"requester_person_id":actor_id,
                        "residence_household_id":residence,"continue_p16_care_to_p15":care,
                        "terms_proposer_person_id":actor_id,"partner_household_senior_person_id":reviewer,
                        "occupational_roles_remain_active":True,"residence_changes_household_membership":True,
                        "fixture_notice":"Residence and continuing-care terms are ASM-FIXTURE-020 calibration; no bridewealth/dowry or universal residence rule is inferred.",
                    }
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (review_scene,self.run_id,day,scene["place_id"],"household","marriage_household_terms_review",
                                 canonical_json(review_stakes),"{}",
                                 canonical_json({"two_household_review":True,"mediation_if_household_terms_disagree":True}),
                                 canonical_json(["I-MEDIATION"]),"open"))
                    for pid,role in ((actor_id,"terms_proposer"),(reviewer,"decision_actor"),(scene_stakes["initiator_person_id"],"prospective_spouse"),(scene_stakes["prospective_partner_person_id"],"prospective_spouse")):
                        con.execute("INSERT OR IGNORE INTO scene_participants VALUES (?,?,?)",(review_scene,pid,role))
                    eid=self._event(con,day,"marriage_household_terms_proposed",scene_id=review_scene,decision_id=decision_id,
                                    actors=[actor_id,reviewer,scene_stakes["initiator_person_id"],scene_stakes["prospective_partner_person_id"]],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-020","RULE-MARRIAGE-NEGOTIATION-001"],
                                    payload={"action_id":aid,"residence_household_id":residence,"continue_p16_care_to_p15":care,
                                             "reason":action.get("reason")},discriminator=aid)
                    review_stakes["terms_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(review_stakes),review_scene))
                    for pid in ("P15","P9","P16","P10"):
                        self._memory(con,pid,day,f"Marriage household terms proposed: residence {residence}; continuing P16 care to P15={care}.",
                                     event_id=eid,memory_type="marriage_negotiation",salience=.82,relationship_relevance=.82,goal_relevance=.8,
                                     provenance={"assumption_id":"ASM-FIXTURE-020"})
                    followups.append((review_scene,reviewer,["accept_marriage_household_terms","refuse_proposal","seek_mediation","communicate"]))

                elif typ == "accept_marriage_household_terms":
                    consent_scene=stable_id("SCENE",self.run_id,day,"marriage_final_consent","P16",decision_id,idx)
                    consent_stakes={
                        **scene_stakes,"consenting_person_id":"P16","partner_person_id":"P10","consent_stage":"initiator",
                        "terms_acceptance_event_id":None,
                        "fixture_notice":"Household terms are accepted, but marriage still requires separate final consent from P16 and P10.",
                    }
                    eid=self._event(con,day,"marriage_household_terms_accepted",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id,scene_stakes["terms_proposer_person_id"],"P16","P10"],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-020","RULE-MARRIAGE-NEGOTIATION-001"],
                                    payload={"action_id":aid,"residence_household_id":scene_stakes["residence_household_id"],
                                             "continue_p16_care_to_p15":scene_stakes["continue_p16_care_to_p15"]},discriminator=aid)
                    consent_stakes["terms_acceptance_event_id"]=eid
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (consent_scene,self.run_id,day,scene["place_id"],"household","marriage_final_consent",
                                 canonical_json(consent_stakes),"{}",
                                 canonical_json({"individual_final_consent":True,"no_mediation_overrides_refusal":True}),"[]","open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(consent_scene,"P16","decision_actor"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(consent_scene,"P10","prospective_spouse"))
                    for pid in ("P15","P9","P16","P10"):
                        self._memory(con,pid,day,"Both household seniors accepted the bounded residence/care terms; final individual consent is still required.",
                                     event_id=eid,memory_type="marriage_negotiation",salience=.84,relationship_relevance=.82,goal_relevance=.84)
                    followups.append((consent_scene,"P16",["give_marriage_consent","decline_marriage_consent","communicate"]))

                elif typ == "give_marriage_consent":
                    partner=scene_stakes["partner_person_id"]
                    eid=self._event(con,day,"marriage_consent_given",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id,partner],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-019","ASM-FIXTURE-020","RULE-MARRIAGE-NEGOTIATION-001"],
                                    payload={"action_id":aid,"consent_stage":scene_stakes["consent_stage"]},discriminator=aid)
                    self._memory(con,actor_id,day,"Gave final consent to the negotiated marriage terms.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.95,relationship_relevance=.95,goal_relevance=.9)
                    self._memory(con,partner,day,f"{actor_id} gave final consent to the negotiated marriage terms.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.9,relationship_relevance=.95,goal_relevance=.85)
                    if scene_stakes["consent_stage"] == "initiator":
                        next_scene=stable_id("SCENE",self.run_id,day,"marriage_final_consent","P10",decision_id,idx)
                        next_stakes={**scene_stakes,"consenting_person_id":"P10","partner_person_id":"P16","consent_stage":"partner",
                                     "initiator_consent_event_id":eid}
                        con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (next_scene,self.run_id,day,scene["place_id"],"household","marriage_final_consent",
                                     canonical_json(next_stakes),"{}",canonical_json({"individual_final_consent":True,"no_mediation_overrides_refusal":True}),"[]","open"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(next_scene,"P10","decision_actor"))
                        con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(next_scene,"P16","prospective_spouse"))
                        followups.append((next_scene,"P10",["give_marriage_consent","decline_marriage_consent","communicate"]))
                    else:
                        residence=scene_stakes["residence_household_id"]
                        care=bool(scene_stakes["continue_p16_care_to_p15"])
                        marriage_id=stable_id("MAR",self.run_id,"P16","P10",day,scene_stakes.get("terms_event_id",""))
                        terms={"residence_household_id":residence,"continue_p16_care_to_p15":care,"no_material_transfer_modeled":True}
                        provenance={"assumption_ids":["ASM-FIXTURE-019","ASM-FIXTURE-020"],"rule_id":"RULE-MARRIAGE-NEGOTIATION-001",
                                    "notice":"simulation marriage outcome; no historical individual/event or universal Ugaritic marriage rule claimed"}
                        con.execute("INSERT INTO marriages VALUES (?,?,?,?,?,?,?,?,?,?)",
                                    (marriage_id,self.run_id,"P16","P10",day,None,"active",residence,canonical_json(terms),canonical_json(provenance)))
                        for a,b,ktype in (("P16","P10","spouse"),("P15","P10","affinal_kin"),("P9","P16","affinal_kin")):
                            kid=stable_id("KIN",self.run_id,a,b,ktype,day)
                            con.execute("INSERT INTO kinship_edges VALUES (?,?,?,?,?,?,?,?)",
                                        (kid,self.run_id,a,b,ktype,day,None,canonical_json(provenance)))
                        self._ensure_relationship_pair(con,"P16","P10",relationship_type="spouse")
                        self._ensure_relationship_pair(con,"P15","P10",relationship_type="affinal_kin")
                        self._ensure_relationship_pair(con,"P9","P16",relationship_type="affinal_kin")
                        con.execute("UPDATE relationships SET relationship_type='spouse',kin_degree='spouse',last_contact_day=? WHERE (from_person_id='P16' AND to_person_id='P10') OR (from_person_id='P10' AND to_person_id='P16')",(day,))
                        self._adjust_relationship(con,"P16","P10",trust=.05,respect=.03)
                        self._adjust_relationship(con,"P10","P16",trust=.05,respect=.03)
                        mover="P10" if residence == "H-WIDOW" else "P16"
                        old_house=self._household_for_person(mover)
                        if old_house != residence:
                            con.execute("UPDATE household_memberships SET until_day=? WHERE person_id=? AND until_day IS NULL",(day,mover))
                            con.execute("INSERT INTO household_memberships VALUES (?,?,?,?,?)",(residence,mover,"married_in_adult",day,None))
                            home=con.execute("SELECT home_place_id FROM households WHERE household_id=?",(residence,)).fetchone()[0]
                            con.execute("UPDATE persons SET current_place_id=? WHERE person_id=?",(home,mover))
                        care_oid=None
                        if care:
                            care_oid=stable_id("O",self.run_id,"continuing_kin_care","P16","P15",marriage_id)
                            if not con.execute("SELECT 1 FROM obligations WHERE obligation_id=?",(care_oid,)).fetchone():
                                con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                                            (care_oid,"P16",residence,"P15","H-WIDOW","continuing_kin_care",
                                             "Kothar retains a continuing support obligation toward Bat-Rapiu after marriage/residence settlement.",
                                             None,"active",canonical_json({"assumption_id":"ASM-FIXTURE-020","marriage_id":marriage_id,
                                                                          "notice":"bounded simulation care term, not universal Ugaritic elder-care law"})))
                        final_eid=self._event(con,day,"marriage_concluded",scene_id=job["scene_id"],decision_id=decision_id,
                                              actors=["P16","P10","P15","P9"],causes=[x for x in [scene_stakes.get("initiator_consent_event_id"),eid] if x],
                                              rules=["ASM-FIXTURE-019","ASM-FIXTURE-020","RULE-MARRIAGE-NEGOTIATION-001"],
                                              payload={"marriage_id":marriage_id,"residence_household_id":residence,"moved_person_id":mover,
                                                       "continuing_care_obligation_id":care_oid,"no_material_transfer_modeled":True},
                                              discriminator=marriage_id)
                        for pid in ("P16","P10","P15","P9"):
                            self._memory(con,pid,day,f"P16 and P10 concluded marriage after individual and household agreement; residence is {residence}.",
                                         event_id=final_eid,memory_type="marriage",salience=.95,relationship_relevance=.95,goal_relevance=.9,
                                         provenance=provenance)

                elif typ == "decline_marriage_consent":
                    partner=scene_stakes["partner_person_id"]
                    eid=self._event(con,day,"marriage_consent_declined",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id,partner],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-019","ASM-FIXTURE-020","RULE-MARRIAGE-NEGOTIATION-001"],
                                    payload={"action_id":aid,"reason":action.get("reason"),"final":True},discriminator=aid)
                    self._memory(con,actor_id,day,f"Declined final marriage consent: {action.get('reason','did not consent')}.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.9,relationship_relevance=.9,goal_relevance=.85)
                    self._memory(con,partner,day,f"{actor_id} declined final marriage consent; no marriage was created.",event_id=eid,
                                 memory_type="marriage_negotiation",salience=.9,relationship_relevance=.9,goal_relevance=.8)

                elif typ == "preserve_seasonal_surplus":
                    amount=float(action["amount"])
                    ratio=float(scene_stakes.get("preservation_output_ratio",.9))
                    stored=amount*ratio
                    self._change_resource(con,actor_household,"seasonal_produce",-amount,assumption_id="ASM-FIXTURE-021")
                    self._change_resource(con,actor_household,"stored_seasonal_goods",stored,assumption_id="ASM-FIXTURE-021")
                    eid=self._event(con,day,"seasonal_surplus_preserved",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                                    rules=["ASM-FIXTURE-021","RULE-SEASONAL-SURPLUS-STORAGE-001"],
                                    material={actor_household:{"seasonal_produce":-amount,"stored_seasonal_goods":stored}},
                                    payload={"action_id":aid,"input_amount":amount,"stored_amount":stored,"output_ratio":ratio,
                                             "reason":action.get("reason"),"staple_grain_changed":False},discriminator=aid)
                    self._memory(con,actor_id,day,f"Preserved {amount:g} seasonal produce into {stored:g} stored seasonal goods in fixture units.",
                                 event_id=eid,memory_type="seasonal_storage",salience=.72,relationship_relevance=.2,goal_relevance=.82,
                                 provenance={"assumption_id":"ASM-FIXTURE-021"})

                elif typ == "fulfill_kin_care":
                    oid=action["care_obligation_id"]
                    beneficiary=scene_stakes["beneficiary_person_id"]
                    relationship_delta={
                        f"{actor_id}->{beneficiary}":self._adjust_relationship(con,actor_id,beneficiary,trust=.02,respect=.02),
                        f"{beneficiary}->{actor_id}":self._adjust_relationship(con,beneficiary,actor_id,trust=.03,respect=.03),
                    }
                    eid=self._event(
                        con,day,"kin_care_fulfilled",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,beneficiary],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-023","RULE-KIN-CARE-PROPERTY-001"],
                        relationships=relationship_delta,payload={"action_id":aid,"care_obligation_id":oid,
                            "support_kind":action["support_kind"],"reason":action.get("reason"),
                            "notice":"support-day timing/task are fixture calibration; continuing obligation remains active"},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Fulfilled a concrete support day for {beneficiary} under my continuing care obligation.",
                                 event_id=eid,memory_type="kin_care",salience=.82,relationship_relevance=.9,goal_relevance=.78,
                                 provenance={"assumption_id":"ASM-FIXTURE-023"})
                    self._memory(con,beneficiary,day,f"{actor_id} fulfilled another concrete support need under the continuing care arrangement.",
                                 event_id=eid,memory_type="kin_care",salience=.88,relationship_relevance=.94,goal_relevance=.9,
                                 provenance={"assumption_id":"ASM-FIXTURE-023"})
                    fulfilled=int(con.execute(
                        "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='kin_care_fulfilled' "
                        "AND json_extract(payload_json,'$.care_obligation_id')=?",(self.run_id,oid)).fetchone()[0])
                    if self.db.schema_version() >= 3 and fulfilled >= 2:
                        existing_pref=con.execute("SELECT 1 FROM property_preferences WHERE run_id=? AND household_id='H-WIDOW' AND status='active'",(self.run_id,)).fetchone()
                        existing_review=con.execute("SELECT 1 FROM scenes WHERE run_id=? AND trigger_type='property_preference_review'",(self.run_id,)).fetchone()
                        if not existing_pref and not existing_review:
                            review_scene=stable_id("SCENE",self.run_id,"property_preference_review","P15","P16",day)
                            review_stakes={"situation_id":"SIT-019","holder_person_id":"P15","beneficiary_person_id":"P16",
                                "household_id":"H-WIDOW","fulfilled_care_episodes":fulfilled,
                                "preference_type":"care_informed_priority","scope":"household_property_if_later_negotiated",
                                "fixture_notice":"Repeated care can inform a non-binding property preference under ASM-FIXTURE-023; no inheritance, ownership transfer, or Ugaritic succession rule is implied."}
                            con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                        (review_scene,self.run_id,day,scene["place_id"],"household","property_preference_review",canonical_json(review_stakes),"{}",
                                         canonical_json({"care_history_matters":True,"preference_nonbinding":True,"no_transfer":True}),
                                         canonical_json(["I-MEDIATION"]),"open"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(review_scene,"P15","decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(review_scene,"P16","potential_beneficiary"))
                            self._event(con,day,"property_preference_review_opened",scene_id=review_scene,actors=["P15","P16"],
                                        rules=["ASM-FIXTURE-023","RULE-KIN-CARE-PROPERTY-001"],payload=review_stakes,discriminator=review_scene)
                            followups.append((review_scene,"P15",["record_property_preference","wait","communicate"]))

                elif typ == "defer_kin_care":
                    oid=action["care_obligation_id"]
                    beneficiary=scene_stakes["beneficiary_person_id"]
                    relationship_delta={
                        f"{actor_id}->{beneficiary}":self._adjust_relationship(con,actor_id,beneficiary,trust=-.01),
                        f"{beneficiary}->{actor_id}":self._adjust_relationship(con,beneficiary,actor_id,trust=-.02),
                    }
                    eid=self._event(con,day,"kin_care_deferred",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,beneficiary],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-023","RULE-KIN-CARE-PROPERTY-001"],
                                    relationships=relationship_delta,payload={"action_id":aid,"care_obligation_id":oid,"reason":action.get("reason")},discriminator=aid)
                    self._memory(con,actor_id,day,f"Deferred a concrete support need for {beneficiary}: {action.get('reason','competing obligations')}.",
                                 event_id=eid,memory_type="kin_care",salience=.72,relationship_relevance=.84,goal_relevance=.78,provenance={"assumption_id":"ASM-FIXTURE-023"})
                    self._memory(con,beneficiary,day,f"{actor_id} deferred a concrete support need under the continuing care arrangement.",
                                 event_id=eid,memory_type="kin_care",salience=.8,relationship_relevance=.9,goal_relevance=.82,provenance={"assumption_id":"ASM-FIXTURE-023"})

                elif typ == "record_property_preference":
                    pref_id=stable_id("PREF",self.run_id,scene_stakes["household_id"],actor_id,action["beneficiary_person_id"],day)
                    basis={"fulfilled_care_episodes":scene_stakes["fulfilled_care_episodes"],"care_history":True,
                           "notice":"preference only; later property/succession decision remains open"}
                    provenance={"assumption_id":"ASM-FIXTURE-023","rule_id":"RULE-KIN-CARE-PROPERTY-001",
                                "notice":"non-binding simulation preference, not a Ugaritic inheritance rule or property transfer"}
                    con.execute("INSERT INTO property_preferences VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (pref_id,self.run_id,scene_stakes["household_id"],actor_id,action["beneficiary_person_id"],action["preference_type"],
                                 action["scope"],day,None,"active",canonical_json(basis),canonical_json(provenance)))
                    eid=self._event(con,day,"property_preference_recorded",scene_id=job["scene_id"],decision_id=decision_id,
                                    actors=[actor_id,action["beneficiary_person_id"]],knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),
                                    rules=["ASM-FIXTURE-023","RULE-KIN-CARE-PROPERTY-001"],
                                    payload={"action_id":aid,"preference_id":pref_id,"preference_type":action["preference_type"],
                                             "scope":action["scope"],"binding":False,"reason":action.get("reason")},discriminator=aid)
                    self._memory(con,actor_id,day,f"Recorded a non-binding household property preference favoring {action['beneficiary_person_id']} if property is later negotiated, based on remembered care.",
                                 event_id=eid,memory_type="property_preference",salience=.9,relationship_relevance=.9,goal_relevance=.94,provenance=provenance)
                    self._memory(con,action["beneficiary_person_id"],day,f"{actor_id} recorded a non-binding future property preference in my favor based on fulfilled care; no property has transferred.",
                                 event_id=eid,memory_type="property_preference",salience=.9,relationship_relevance=.94,goal_relevance=.9,provenance=provenance)

                elif typ == "request_reciprocal_labor":
                    helper=action["target_person_id"]
                    request_scene=stable_id("SCENE",self.run_id,day,"reciprocal_labor_request",decision_id,idx)
                    request_stakes={**scene_stakes,"requester_person_id":actor_id,"helper_person_id":helper,
                                    "request_event_id":None,"request_reason":action.get("reason"),
                                    "fixture_notice":"One bounded winter labor request under ASM-FIXTURE-025; the earlier sowing favor has no fixed exchange price or historical equivalence."}
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (request_scene,self.run_id,day,scene["place_id"],"household","reciprocal_labor_request",canonical_json(request_stakes),
                                 canonical_json({"service_days":scene_stakes["service_days"],"draft_team_condition":scene_stakes["draft_team_condition"]}),
                                 canonical_json({"private_negotiation_first":True,"reciprocity_open_ended":True}),
                                 canonical_json(["I-MEDIATION"]),"open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,actor_id,"requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,helper,"decision_actor"))
                    eid=self._event(con,day,"reciprocal_labor_requested",scene_id=request_scene,decision_id=decision_id,actors=[actor_id,helper],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],
                                    payload={"action_id":aid,"service_days":action["service_days"],"reason":action.get("reason")},discriminator=aid)
                    request_stakes["request_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(request_stakes),request_scene))
                    self._memory(con,actor_id,day,f"Asked {helper} for one bounded winter maintenance labor service in light of the earlier sowing help.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.84,relationship_relevance=.9,goal_relevance=.8,provenance={"assumption_id":"ASM-FIXTURE-025"})
                    self._memory(con,helper,day,f"{actor_id} asked me for one bounded winter maintenance labor service, invoking the remembered sowing-season favor without assigning it a fixed price.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.86,relationship_relevance=.92,goal_relevance=.8,provenance={"assumption_id":"ASM-FIXTURE-025"})
                    followups.append((request_scene,helper,["fulfill_reciprocal_labor","refuse_proposal","seek_mediation","communicate"]))

                elif typ == "handle_winter_maintenance_internally":
                    row=con.execute("SELECT amount FROM resource_stocks WHERE household_id='H-FARM' AND resource_type='draft_team_condition'").fetchone()
                    current=float(row[0]) if row else 0.0
                    restored=max(0.0,min(0.10,1.0-current))
                    if restored>0:
                        self._change_resource(con,"H-FARM","draft_team_condition",restored,assumption_id="ASM-FIXTURE-025")
                    eid=self._event(con,day,"winter_maintenance_handled_internally",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],
                                    material={"H-FARM":{"draft_team_condition":restored}} if restored else {},
                                    payload={"action_id":aid,"condition_restored":restored,"reason":action.get("reason"),
                                             "notice":"fixture internal maintenance effort; no historical animal-care rate"},discriminator=aid)
                    self._memory(con,actor_id,day,"Kept the winter draft-team maintenance burden inside my own household rather than calling in the remembered favor.",
                                 event_id=eid,memory_type="winter_maintenance",salience=.7,relationship_relevance=.5,goal_relevance=.76,provenance={"assumption_id":"ASM-FIXTURE-025"})

                elif typ == "fulfill_reciprocal_labor":
                    effective=scene_stakes.get("source_stakes",scene_stakes) if scene["trigger_type"]=="informal_mediation_review" else scene_stakes
                    requester=action["requester_person_id"]
                    requester_household=effective.get("beneficiary_household_id","H-FARM")
                    due=day+int(action["service_days"])
                    oid=stable_id("O",self.run_id,"fixture_winter_reciprocal_labor",actor_id,requester,day)
                    provenance={"assumption_id":"ASM-FIXTURE-025","rule_id":"RULE-WINTER-RECIPROCAL-LABOR-001",
                                "request_event_id":effective.get("request_event_id"),"condition_restore":float(effective.get("condition_restore",0.15)),
                                "notice":"bounded reciprocal labor; no fixed historical equivalence to the sowing favor"}
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (oid,actor_id,actor_household,requester,requester_household,"fixture_winter_reciprocal_labor",
                                 "Provide one bounded winter draft-team care/maintenance labor service in answer to earlier sowing help.",due,"scheduled",canonical_json(provenance)))
                    eid=self._event(con,day,"reciprocal_labor_accepted",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,requester],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-025","RULE-WINTER-RECIPROCAL-LABOR-001"],
                                    payload={"action_id":aid,"obligation_id":oid,"service_due_day":due,"reason":action.get("reason"),
                                             "notice":"acceptance schedules labor; favor balances clear only on completed service"},discriminator=aid)
                    self._memory(con,actor_id,day,f"Agreed to provide {requester} one bounded winter maintenance labor service in answer to the earlier sowing help.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.86,relationship_relevance=.92,goal_relevance=.8,provenance=provenance)
                    self._memory(con,requester,day,f"{actor_id} agreed to answer the earlier sowing favor with one bounded winter maintenance labor service due on day {due}.",
                                 event_id=eid,memory_type="reciprocal_labor",salience=.84,relationship_relevance=.92,goal_relevance=.82,provenance=provenance)

                elif typ == "request_draft_access":
                    holder=action["target_person_id"]
                    request_scene=stable_id("SCENE",self.run_id,day,"draft_access_request",decision_id,idx)
                    request_stakes={**scene_stakes,"requester_person_id":actor_id,"access_holder_person_id":holder,
                                    "request_event_id":None,"request_reason":action.get("reason"),
                                    "fixture_notice":"One bounded draft-team service request under ASM-FIXTURE-024; no ownership transfer or historical plowing contract is implied."}
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (request_scene,self.run_id,day,scene["place_id"],"economic","draft_access_request",canonical_json(request_stakes),
                                 canonical_json({"service_days":scene_stakes["service_days"]}),
                                 canonical_json({"private_negotiation_first":True,"grant_has_opportunity_cost":True}),
                                 canonical_json(["I-MEDIATION"]),"open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,actor_id,"requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,holder,"decision_actor"))
                    eid=self._event(con,day,"draft_access_requested",scene_id=request_scene,decision_id=decision_id,actors=[actor_id,holder],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-024","RULE-SOWING-DRAFT-ACCESS-001"],
                                    payload={"action_id":aid,"service_days":action["service_days"],"reason":action.get("reason")},discriminator=aid)
                    request_stakes["request_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(request_stakes),request_scene))
                    self._memory(con,actor_id,day,f"Asked {holder} for one bounded draft-team service during the sowing window.",
                                 event_id=eid,memory_type="agricultural_access",salience=.84,relationship_relevance=.84,goal_relevance=.92,provenance={"assumption_id":"ASM-FIXTURE-024"})
                    self._memory(con,holder,day,f"{actor_id} asked for one bounded draft-team service during the sowing window.",
                                 event_id=eid,memory_type="agricultural_access",salience=.8,relationship_relevance=.84,goal_relevance=.82,provenance={"assumption_id":"ASM-FIXTURE-024"})
                    followups.append((request_scene,holder,["grant_draft_access","refuse_proposal","seek_mediation","communicate"]))

                elif typ == "grant_draft_access":
                    effective = scene_stakes.get("source_stakes", scene_stakes) if scene["trigger_type"] == "informal_mediation_review" else scene_stakes
                    requester=action["requester_person_id"]
                    requester_household=effective["requester_household_id"]
                    due=day+int(action["service_days"])
                    oid=stable_id("O",self.run_id,"fixture_draft_team_service",actor_id,requester,day)
                    provenance={"assumption_id":"ASM-FIXTURE-024","rule_id":"RULE-SOWING-DRAFT-ACCESS-001",
                                "request_event_id":effective.get("request_event_id"),
                                "service_sowing_progress":float(effective.get("service_sowing_progress",0.10)),
                                "access_holder_opportunity_cost_progress":float(effective.get("access_holder_opportunity_cost_progress",0.05)),
                                "notice":"fixture service/progress transfer; not historical ownership/rate"}
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (oid,actor_id,actor_household,requester,requester_household,"fixture_draft_team_service",
                                 "Provide one bounded draft-team service during the sowing window.",due,"scheduled",canonical_json(provenance)))
                    relationship_delta={
                        f"{actor_id}->{requester}":self._adjust_relationship(con,actor_id,requester,trust=.02,favors_given=1),
                        f"{requester}->{actor_id}":self._adjust_relationship(con,requester,actor_id,trust=.03,respect=.01,favors_owed=1),
                    }
                    eid=self._event(con,day,"draft_access_granted",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,requester],
                                    knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-024","RULE-SOWING-DRAFT-ACCESS-001"],
                                    relationships=relationship_delta,payload={"action_id":aid,"obligation_id":oid,"service_due_day":due,
                                    "reason":action.get("reason")},discriminator=aid)
                    self._memory(con,actor_id,day,f"Agreed to provide {requester} one bounded draft-team service due on day {due}.",
                                 event_id=eid,memory_type="agricultural_access",salience=.82,relationship_relevance=.9,goal_relevance=.72,provenance=provenance)
                    self._memory(con,requester,day,f"{actor_id} agreed to provide my household one bounded draft-team service due on day {due}; I now owe a favor.",
                                 event_id=eid,memory_type="agricultural_access",salience=.88,relationship_relevance=.94,goal_relevance=.94,provenance=provenance)

                elif typ == "request_household_reserve_agreement":
                    target_person = action["target_person_id"]
                    reserve_floor = float(action["reserve_floor"])
                    request_scene = stable_id("SCENE", self.run_id, day, "household_reserve_request", decision_id, idx)
                    request_stakes = {
                        "situation_id":"SIT-013","requester_person_id":actor_id,"merchant_person_id":target_person,
                        "household_id":actor_household,"resource":"silver","reserve_floor":reserve_floor,
                        "completed_trade_exchanges":scene_stakes.get("completed_trade_exchanges"),
                        "request_reason":action.get("reason","protect a household reserve before further trade commitments"),
                        "fixture_notice":scene_stakes.get("fixture_notice"),
                    }
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene,self.run_id,day,scene["place_id"],"household","household_reserve_request",
                         canonical_json(request_stakes),canonical_json({"resource":"silver","reserve_floor":reserve_floor}),
                         canonical_json({"private_negotiation_first":True,"household_strategy":True}),
                         canonical_json(["I-MEDIATION"]),"open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,actor_id,"requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,target_person,"decision_actor"))
                    eid=self._event(
                        con,day,"household_reserve_requested",scene_id=request_scene,decision_id=decision_id,
                        actors=[actor_id,target_person],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-016","RULE-HOUSEHOLD-RESOURCE-PRIORITY-001"],
                        payload={"action_id":aid,"reserve_floor":reserve_floor,"reason":action.get("reason")},discriminator=aid,
                    )
                    request_stakes["request_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(request_stakes),request_scene))
                    self._memory(con,actor_id,day,f"Asked {target_person} to keep at least {reserve_floor:g} silver in household reserve before further trade exposure.",
                                 event_id=eid,memory_type="household_strategy",salience=.78,relationship_relevance=.82,goal_relevance=.9,
                                 provenance={"assumption_id":"ASM-FIXTURE-016"})
                    self._memory(con,target_person,day,f"{actor_id} asked that our household preserve at least {reserve_floor:g} silver before further trade commitments.",
                                 event_id=eid,memory_type="household_strategy",salience=.76,relationship_relevance=.82,goal_relevance=.86,
                                 provenance={"assumption_id":"ASM-FIXTURE-016"})
                    followups.append((request_scene,target_person,["accept_household_reserve","refuse_proposal","seek_mediation","communicate"]))

                elif typ == "accept_household_reserve":
                    effective = scene_stakes.get("source_stakes", scene_stakes) if scene["trigger_type"] == "informal_mediation_review" else scene_stakes
                    reserve_floor=float(action["reserve_floor"])
                    requester=effective["requester_person_id"]
                    oid=stable_id("O",self.run_id,"household_reserve_commitment",actor_household,"silver",decision_id)
                    provenance={
                        "assumption_id":"ASM-FIXTURE-016","rule_id":"RULE-HOUSEHOLD-RESOURCE-PRIORITY-001",
                        "resource":"silver","reserve_floor":reserve_floor,"requester_person_id":requester,
                        "notice":"reserve floor is household-strategy calibration, not a historical Ugaritic minimum capital rule",
                    }
                    con.execute(
                        "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid,actor_id,actor_household,requester,actor_household,"household_reserve_commitment",
                         f"Preserve at least {reserve_floor:g} silver in household reserve before discretionary trade commitments.",
                         None,"active",canonical_json(provenance)),
                    )
                    relationship_delta={
                        f"{actor_id}->{requester}":self._adjust_relationship(con,actor_id,requester,trust=.02,respect=.01),
                        f"{requester}->{actor_id}":self._adjust_relationship(con,requester,actor_id,trust=.02,respect=.01),
                    }
                    eid=self._event(
                        con,day,"household_reserve_agreed",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id,requester],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-016","RULE-HOUSEHOLD-RESOURCE-PRIORITY-001"],relationships=relationship_delta,
                        payload={"action_id":aid,"obligation_id":oid,"resource":"silver","reserve_floor":reserve_floor,
                                 "reason":action.get("reason")},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Agreed with {requester} to protect a household silver reserve of {reserve_floor:g}.",
                                 event_id=eid,memory_type="household_strategy",salience=.82,relationship_relevance=.86,goal_relevance=.9,provenance=provenance)
                    self._memory(con,requester,day,f"{actor_id} agreed to protect our household silver reserve at {reserve_floor:g} before further trade exposure.",
                                 event_id=eid,memory_type="household_strategy",salience=.84,relationship_relevance=.88,goal_relevance=.92,provenance=provenance)

                elif typ == "request_apprenticeship_progression":
                    target_person=action["target_person_id"]
                    request_scene=stable_id("SCENE",self.run_id,day,"apprenticeship_progression_request",decision_id,idx)
                    request_stakes={
                        "situation_id":"SIT-014","requester_person_id":actor_id,"apprentice_person_id":actor_id,
                        "master_person_id":target_person,"requested_recognition":action["requested_recognition"],
                        "work_cycles_as_apprentice":scene_stakes.get("work_cycles_as_apprentice"),
                        "apprenticeship_days":scene_stakes.get("apprenticeship_days"),
                        "household_finished_metalwork":scene_stakes.get("household_finished_metalwork"),
                        "request_reason":action.get("reason","accumulated workshop work merits a progression review"),
                        "fixture_notice":scene_stakes.get("fixture_notice"),
                    }
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene,self.run_id,day,scene["place_id"],"household","apprenticeship_progression_request",
                         canonical_json(request_stakes),canonical_json({"accumulated_work_cycles":request_stakes["work_cycles_as_apprentice"]}),
                         canonical_json({"master_apprentice_negotiation":True,"recognition_not_automatic":True}),
                         canonical_json(["I-MEDIATION"]),"open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,actor_id,"requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(request_scene,target_person,"decision_actor"))
                    eid=self._event(
                        con,day,"apprenticeship_progression_requested",scene_id=request_scene,decision_id=decision_id,
                        actors=[actor_id,target_person],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-017","RULE-APPRENTICESHIP-PROGRESSION-001"],
                        payload={"action_id":aid,"requested_recognition":action["requested_recognition"],"reason":action.get("reason")},discriminator=aid,
                    )
                    request_stakes["request_event_id"]=eid
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?",(canonical_json(request_stakes),request_scene))
                    self._memory(con,actor_id,day,f"Asked {target_person} to recognize my progression from supervised apprenticeship to a recognized workshop worker role.",
                                 event_id=eid,memory_type="life_course",salience=.9,relationship_relevance=.9,goal_relevance=.95,provenance={"assumption_id":"ASM-FIXTURE-017"})
                    self._memory(con,target_person,day,f"{actor_id} asked for recognition as a workshop craft worker after sustained apprenticeship work.",
                                 event_id=eid,memory_type="life_course",salience=.86,relationship_relevance=.9,goal_relevance=.86,provenance={"assumption_id":"ASM-FIXTURE-017"})
                    followups.append((request_scene,target_person,["grant_apprenticeship_progression","refuse_proposal","seek_mediation","communicate"]))

                elif typ == "grant_apprenticeship_progression":
                    effective = scene_stakes.get("source_stakes", scene_stakes) if scene["trigger_type"] == "informal_mediation_review" else scene_stakes
                    apprentice_id=effective["apprentice_person_id"]
                    role_id="R-RECOGNIZED_CRAFT_WORKER"
                    con.execute(
                        "UPDATE person_roles SET end_day=? WHERE person_id=? AND role_id=(SELECT role_id FROM roles WHERE name='craft_apprentice') AND end_day IS NULL",
                        (day,apprentice_id),
                    )
                    con.execute(
                        "INSERT OR IGNORE INTO person_roles(person_id,role_id,priority,start_day,end_day) VALUES (?,?,?,?,NULL)",
                        (apprentice_id,role_id,1,day),
                    )
                    current_membership=con.execute(
                        "SELECT household_id,since_day FROM household_memberships WHERE person_id=? AND until_day IS NULL ORDER BY since_day DESC LIMIT 1",
                        (apprentice_id,),
                    ).fetchone()
                    if current_membership:
                        con.execute("UPDATE household_memberships SET until_day=? WHERE household_id=? AND person_id=? AND since_day=?",
                                    (day,current_membership["household_id"],apprentice_id,current_membership["since_day"]))
                        con.execute("INSERT INTO household_memberships VALUES (?,?,?,?,?)",
                                    (current_membership["household_id"],apprentice_id,"attached_worker",day,None))
                    status={"workshop_recognition":"recognized_craft_worker","progressed_day":day,
                            "notice":"simulation workshop progression under ASM-FIXTURE-017; not a reconstructed Ugaritic legal rank"}
                    con.execute("UPDATE persons SET legal_status='dependent_craft_worker',status_json=? WHERE person_id=?",
                                (canonical_json(status),apprentice_id))
                    con.execute("UPDATE relationships SET relationship_type='workshop_mentor' WHERE from_person_id=? AND to_person_id=?",(actor_id,apprentice_id))
                    con.execute("UPDATE relationships SET relationship_type='craft_mentor' WHERE from_person_id=? AND to_person_id=?",(apprentice_id,actor_id))
                    relationship_delta={
                        f"{actor_id}->{apprentice_id}":self._adjust_relationship(con,actor_id,apprentice_id,trust=.03,respect=.04),
                        f"{apprentice_id}->{actor_id}":self._adjust_relationship(con,apprentice_id,actor_id,trust=.04,respect=.03),
                    }
                    eid=self._event(
                        con,day,"apprenticeship_progressed",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id,apprentice_id],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-017","RULE-APPRENTICESHIP-PROGRESSION-001"],relationships=relationship_delta,
                        payload={"action_id":aid,"old_role":"craft_apprentice","new_role":"recognized_craft_worker",
                                 "legal_status":"dependent_craft_worker","reason":action.get("reason")},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Recognized {apprentice_id} as a workshop craft worker after sustained supervised work.",
                                 event_id=eid,memory_type="life_course",salience=.9,relationship_relevance=.92,goal_relevance=.9,provenance={"assumption_id":"ASM-FIXTURE-017"})
                    self._memory(con,apprentice_id,day,f"{actor_id} recognized my progression from apprentice to a workshop craft worker role.",
                                 event_id=eid,memory_type="life_course",salience=.96,relationship_relevance=.94,goal_relevance=.98,provenance={"assumption_id":"ASM-FIXTURE-017"})

                elif typ == "recycle_finished_metalwork":
                    input_amount=float(action["input_finished_metalwork"]); output_amount=float(action["output_metal"])
                    self._change_resource(con,actor_household,"finished_metalwork",-input_amount,assumption_id="ASM-FIXTURE-027")
                    self._change_resource(con,actor_household,"metal",output_amount,assumption_id="ASM-FIXTURE-027")
                    eid=self._event(con,day,"finished_metalwork_recycled",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-027","RULE-METAL-RECYCLING-001"],
                        material={actor_household:{"finished_metalwork":-input_amount,"metal":output_amount}},
                        payload={"action_id":aid,"input_finished_metalwork":input_amount,"output_metal":output_amount,
                                 "notice":"lossy fixture remelting; not a historical Ugaritic recovery rate or value equivalence"},discriminator=aid)
                    self._memory(con,actor_id,day,f"Sacrificed {input_amount:g} finished metalwork to recover {output_amount:g} raw metal in fixture units.",
                        event_id=eid,memory_type="craft_recycling",salience=.86,relationship_relevance=.2,goal_relevance=.95,provenance={"assumption_id":"ASM-FIXTURE-027"})

                elif typ == "request_market_introduction":
                    merchant=action["target_person_id"]; contact=action["requested_contact_person_id"]
                    req_scene=stable_id("SCENE",self.run_id,day,"market_introduction_request",decision_id,idx)
                    req_stakes={"situation_id":"SIT-021","requester_person_id":actor_id,"merchant_person_id":merchant,"contact_person_id":contact,
                                "reason":action.get("reason"),
                                "fixture_notice":"P7 asks an existing merchant relationship for an introduction; P3 must independently grant or refuse under ASM-FIXTURE-028."}
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (req_scene,self.run_id,day,scene["place_id"],"economic","market_introduction_request",canonical_json(req_stakes),"{}",
                         canonical_json({"introduction_not_supplier_guarantee":True}),canonical_json(["I-MARKET"]),"open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(req_scene,actor_id,"requester")); con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(req_scene,merchant,"decision_actor"))
                    eid=self._event(con,day,"market_introduction_requested",scene_id=req_scene,decision_id=decision_id,actors=[actor_id,merchant],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-028","RULE-ALTERNATE-METAL-SOURCING-001"],
                        payload={"action_id":aid,"contact_person_id":contact,"reason":action.get("reason")},discriminator=aid)
                    self._memory(con,actor_id,day,f"Asked {merchant} to introduce me to harbor contact {contact} for alternate metal sourcing information.",
                        event_id=eid,memory_type="trade_network",salience=.82,relationship_relevance=.9,goal_relevance=.94,provenance={"assumption_id":"ASM-FIXTURE-028"})
                    followups.append((req_scene,merchant,["grant_market_introduction","refuse_proposal","communicate"]))

                elif typ == "grant_market_introduction":
                    requester=action["requester_person_id"]; contact=action["contact_person_id"]
                    self._ensure_relationship_pair(con,requester,contact,relationship_type="market_introduction_contact")
                    prop_id=stable_id("PROP",self.run_id,"market_introduction",requester,contact,day)
                    text=f"{actor_id} introduced {requester} to {contact} as a harbor contact who can be asked about alternate metal market leads; no supply is guaranteed."
                    con.execute("INSERT OR IGNORE INTO propositions VALUES (?,?,?,?)",(prop_id,text,"simulation_contingent",canonical_json({"origin":"market_introduction","assumption_id":"ASM-FIXTURE-028"})))
                    kid=stable_id("K",requester,prop_id,decision_id,day)
                    con.execute("INSERT OR IGNORE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (kid,requester,prop_id,day,"direct_communication",decision_id,canonical_json([actor_id,requester]),"direct",.92,"ordinary",None))
                    rel={f"{actor_id}->{requester}":self._adjust_relationship(con,actor_id,requester,trust=.01,respect=.01),
                         f"{requester}->{actor_id}":self._adjust_relationship(con,requester,actor_id,trust=.02,respect=.01)}
                    eid=self._event(con,day,"market_introduction_granted",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,requester,contact],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-028","RULE-ALTERNATE-METAL-SOURCING-001"],relationships=rel,
                        payload={"action_id":aid,"contact_person_id":contact,"knowledge_id":kid},discriminator=aid)
                    self._memory(con,requester,day,f"{actor_id} introduced me to {contact} as a harbor contact for alternate metal-market information.",
                        event_id=eid,memory_type="trade_network",salience=.9,relationship_relevance=.94,goal_relevance=.96,provenance={"assumption_id":"ASM-FIXTURE-028"})
                    inquiry_scene=stable_id("SCENE",self.run_id,"harbor_metal_inquiry_opportunity",requester,contact)
                    inquiry_stakes={"situation_id":"SIT-021","contact_person_id":contact,"introduction_knowledge_id":kid,
                        "fixture_notice":"The introduction permits an inquiry only; P7 still does not know P11's private market lead."}
                    con.execute("INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (inquiry_scene,self.run_id,day,scene["place_id"],"economic","harbor_metal_inquiry_opportunity",canonical_json(inquiry_stakes),"{}",
                         canonical_json({"private_contact_knowledge_hidden":True}),canonical_json(["I-MARKET"]),"open"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(inquiry_scene,requester,"decision_actor")); con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(inquiry_scene,contact,"harbor_contact"))
                    followups.append((inquiry_scene,requester,["send_message","wait"]))

                elif typ == "accept_alternate_metal_exchange":
                    silver=float(action["silver_cost"]); metal=float(action["metal_amount"]); delay=int(action["delivery_days"]); intermediary=scene_stakes["market_intermediary_person_id"]
                    intermediary_household=self._household_for_person(intermediary)
                    self._ensure_relationship_pair(con,actor_id,intermediary,relationship_type="market_contact")
                    self._change_resource(con,actor_household,"silver",-silver,assumption_id="ASM-FIXTURE-028")
                    if intermediary_household:
                        self._change_resource(con,intermediary_household,"silver",silver,assumption_id="ASM-FIXTURE-028")
                    oid=stable_id("O",self.run_id,"fixture_alternate_metal_exchange",decision_id,idx)
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid,intermediary,intermediary_household,actor_id,actor_household,"fixture_alternate_metal_exchange",
                         "Arrange the accepted alternate raw-metal market lot after the modeled delay.",day+delay,"scheduled",
                         canonical_json({"assumption_id":"ASM-FIXTURE-028","rule_id":"RULE-ALTERNATE-METAL-SOURCING-001","metal_amount":metal,"silver_cost":silver,
                                         "notice":"external fixture lot; terms and delay are not historical price/cargo evidence"})))
                    rel={f"{actor_id}->{intermediary}":self._adjust_relationship(con,actor_id,intermediary,trust=.02,respect=.01),
                         f"{intermediary}->{actor_id}":self._adjust_relationship(con,intermediary,actor_id,trust=.01,respect=.01)}
                    eid=self._event(con,day,"alternate_metal_exchange_committed",scene_id=job["scene_id"],decision_id=decision_id,actors=[actor_id,intermediary],
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids",[]),rules=["ASM-FIXTURE-028","RULE-ALTERNATE-METAL-SOURCING-001"],
                        material={actor_household:{"silver":-silver},intermediary_household:{"silver":silver} if intermediary_household else {}},relationships=rel,
                        payload={"action_id":aid,"obligation_id":oid,"silver_cost":silver,"metal_amount":metal,"arrival_day":day+delay},discriminator=aid)
                    self._memory(con,actor_id,day,f"Accepted alternate market terms and paid {silver:g} silver; {metal:g} metal is due after {delay} days in fixture units.",
                        event_id=eid,memory_type="trade",salience=.94,relationship_relevance=.84,goal_relevance=.99,provenance={"assumption_id":"ASM-FIXTURE-028"})

                    self._memory(con,intermediary,day,f"{actor_id} accepted my reported alternate-metal terms; {silver:g} silver entered my household and the fixture lot is due after {delay} days.",
                        event_id=eid,memory_type="trade",salience=.82,relationship_relevance=.86,goal_relevance=.78,provenance={"assumption_id":"ASM-FIXTURE-028"})

                elif typ == "commit_trade_exchange":
                    amount = float(action["silver_amount"])
                    transit_days = int(scene_stakes.get("transit_days",7))
                    goods_ratio = float(scene_stakes.get("exchange_goods_ratio",1.0))
                    goods = amount * goods_ratio
                    self._change_resource(con,actor_household,"silver",-amount,assumption_id="ASM-FIXTURE-012")
                    oid = stable_id("O",self.run_id,"fixture_trade_exchange",decision_id,idx)
                    con.execute(
                        "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid,actor_id,actor_household,None,None,"fixture_trade_exchange",
                         "Committed weighed-metal trade capital to a delayed port exchange.",day+transit_days,"scheduled",
                         canonical_json({"assumption_id":"ASM-FIXTURE-012","rule_id":"RULE-PORT-TRADE-CYCLE-001",
                                         "silver_amount":amount,"trade_goods_amount":goods,"trade_cycle":scene_stakes.get("trade_cycle"),
                                         "notice":"amount/ratio/delay are engineering calibration, not a historical price or profit rate"})),
                    )
                    rel = {"P3->P11":self._adjust_relationship(con,"P3","P11",trust=.01)} if actor_id=="P3" else {}
                    eid = self._event(
                        con,day,"trade_exchange_committed",scene_id=job["scene_id"],decision_id=decision_id,
                        actors=[actor_id,"P11"],knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-012","RULE-PORT-TRADE-CYCLE-001"],
                        material={actor_household:{"silver":-amount}},relationships=rel,
                        institutions={"I-MARKET":{"delayed_exchange":"committed"}},
                        payload={"action_id":aid,"obligation_id":oid,"silver_amount":amount,"expected_trade_goods":goods,
                                 "arrival_day":day+transit_days,"declared_basis":action.get("reason")},discriminator=aid,
                    )
                    self._memory(con,actor_id,day,f"Committed {amount:g} silver in fixture units to a delayed port exchange due on day {day+transit_days}.",
                                 event_id=eid,memory_type="trade",salience=.8,relationship_relevance=.45,goal_relevance=.9,
                                 provenance={"assumption_id":"ASM-FIXTURE-012"})
                    self._memory(con,"P11",day,f"{actor_id} committed trade capital through the current port cycle.",
                                 event_id=eid,memory_type="trade",salience=.55,relationship_relevance=.55,goal_relevance=.5,
                                 provenance={"assumption_id":"ASM-FIXTURE-012"})

                elif typ == "send_message":
                    target = action["target_person_id"]
                    content = action["content"].strip()
                    intent = action["sender_intent"]
                    proposition_id = action.get("proposition_id")
                    route = self._direct_message_route(actor_id, target)
                    if not route:
                        raise ValueError("message route precondition changed")
                    arrival_day = day + int(route["travel_days"])
                    message_id = stable_id("MSG", self.run_id, actor_id, target, proposition_id or "inquiry", day, content)
                    route_provenance = {
                        "decision_id": decision_id,
                        "action_id": aid,
                        "route_id": route["route_id"],
                        "route_mode": route["mode"],
                        "route_travel_days": int(route["travel_days"]),
                        "rule": "direct accessible route chosen deterministically by engine",
                    }
                    con.execute(
                        "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (message_id, actor_id, target, proposition_id, content, None, "Ugaritic_or_mediated", intent,
                         None, route["route_id"], day, arrival_day, None, canonical_json(route_provenance),
                         action.get("secrecy", "ordinary")),
                    )
                    eid = self._event(
                        con, day, "message_sent", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["RULE-MESSAGE-DELAY-001"],
                        payload={"action_id": aid, "message_id": message_id, "recipient": target,
                                 "sender_intent": intent, "proposition_id": proposition_id,
                                 "route_id": route["route_id"], "arrival_day": arrival_day}, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Sent {intent} to {target}: {content}", event_id=eid,
                        memory_type="message_sent", salience=.58, relationship_relevance=.4, goal_relevance=.65,
                        provenance=route_provenance,
                    )

                elif typ == "communicate":
                    target = action["target_person_id"]
                    content = action["content"].strip()
                    proposition_id = stable_id("PROP", self.run_id, day, actor_id, target, content)
                    con.execute(
                        "INSERT OR IGNORE INTO propositions VALUES (?,?,?,?)",
                        (proposition_id, content, "simulation_contingent", canonical_json({"origin": "character_communication"})),
                    )
                    message_id = stable_id("MSG", self.run_id, actor_id, target, proposition_id, day)
                    con.execute(
                        "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (message_id, actor_id, target, proposition_id, content, content, "Ugaritic_or_mediated", "communicate",
                         None, None, day, day, day, "{}", action.get("secrecy", "ordinary")),
                    )
                    kid = stable_id("K", target, proposition_id, message_id, day)
                    con.execute(
                        "INSERT OR IGNORE INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (kid, target, proposition_id, day, "direct_communication", message_id,
                         canonical_json([actor_id, target]), "direct", .9, action.get("secrecy", "ordinary"), None),
                    )
                    eid = self._event(
                        con, day, "direct_communication", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id, target], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["RULE-MESSAGE-DELAY-001"], payload={"action_id": aid, "message_id": message_id,
                                                                    "proposition_id": proposition_id, "content": content},
                        discriminator=aid,
                    )
                    self._adjust_relationship(con, actor_id, target)
                    self._adjust_relationship(con, target, actor_id)
                    self._memory(con, actor_id, day, f"Told {target}: {content}", event_id=eid, memory_type="conversation", salience=.55)
                    self._memory(con, target, day, f"{actor_id} told me: {content}", event_id=eid, memory_type="conversation", salience=.6)

                elif typ == "enter_obligation":
                    oid = stable_id("O", self.run_id, decision_id, idx)
                    con.execute(
                        "INSERT INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (oid, actor_id, actor_household, action.get("beneficiary_person_id"), action.get("beneficiary_household_id"),
                         action.get("obligation_type", "promised_aid"), action["description"], action.get("due_day"), "active",
                         canonical_json({"decision_id": decision_id, "scene_id": job["scene_id"]})),
                    )
                    eid = self._event(
                        con, day, "obligation_entered", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id] + ([action["beneficiary_person_id"]] if action.get("beneficiary_person_id") else []),
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "obligation_id": oid, "description": action["description"]}, discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Accepted obligation: {action['description']}", event_id=eid,
                                 memory_type="obligation", salience=.8, relationship_relevance=.7, goal_relevance=.75)

                elif typ == "request_resource":
                    target_person = action["target_person_id"]
                    target_household = con.execute(
                        "SELECT household_id FROM household_memberships WHERE person_id=? AND until_day IS NULL", (target_person,)
                    ).fetchone()[0]
                    request_scene = stable_id("SCENE", self.run_id, day, "resource_request", decision_id, idx)
                    con.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (request_scene, self.run_id, day, scene["place_id"], "economic", "resource_request", "{}",
                         canonical_json({"requested_resource": action["resource"], "requested_amount": float(action["amount"]),
                                         "requester_household_id": actor_household, "target_household_id": target_household}),
                         canonical_json({"requester_person_id": actor_id, "target_person_id": target_person,
                                         "reason": action.get("reason", "household need")}),
                         canonical_json(["I-MARKET"]), "open"),
                    )
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, actor_id, "requester"))
                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)", (request_scene, target_person, "decision_actor"))
                    eid = self._event(
                        con, day, "resource_request_made", scene_id=request_scene, decision_id=decision_id,
                        actors=[actor_id, target_person], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "resource": action["resource"], "amount": float(action["amount"]),
                                 "reason": action.get("reason"), "requester_household_id": actor_household,
                                 "target_household_id": target_household}, discriminator=aid,
                    )
                    stakes = {
                        "request_event_id": eid,
                        "requester_person_id": actor_id,
                        "requester_household_id": actor_household,
                        "resource": action["resource"],
                        "amount": float(action["amount"]),
                        "reason": action.get("reason", "household need"),
                    }
                    con.execute("UPDATE scenes SET stakes_json=? WHERE scene_id=?", (canonical_json(stakes), request_scene))
                    self._memory(
                        con, actor_id, day,
                        f"Asked {target_person} for {float(action['amount']):g} {action['resource']} because {action.get('reason', 'of household need')}.",
                        event_id=eid, memory_type="resource_request", salience=.78, relationship_relevance=.8, goal_relevance=.9,
                    )
                    followups.append((request_scene, target_person, ["transfer_resource", "communicate", "refuse_proposal", "enter_obligation", "seek_mediation"]))

                elif typ == "seek_mediation":
                    iid = action["institution_id"]
                    eid = self._event(
                        con, day, "mediation_sought", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-018","RULE-INFORMAL-DISPUTE-LADDER-001"] if iid == "I-MEDIATION" else [],
                        institutions={iid: {"requested": True}}, payload={"action_id": aid, "issue": action.get("issue")},
                        discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Sought mediation through {iid}: {action.get('issue', 'a dispute')}.",
                                 event_id=eid, memory_type="institutional_action", salience=.7, relationship_relevance=.65, goal_relevance=.7,
                                 provenance={"assumption_id":"ASM-FIXTURE-018"} if iid == "I-MEDIATION" else None)
                    if iid == "I-MEDIATION":
                        if scene["trigger_type"] == "proposal_refusal_followup":
                            source_trigger = scene_stakes.get("source_trigger")
                            source_stakes = scene_stakes.get("source_stakes", {})
                            review_actor = scene_stakes.get("responder_person_id")
                        elif scene["trigger_type"] == "informal_mediation_review":
                            source_trigger = scene_stakes.get("source_trigger")
                            source_stakes = scene_stakes.get("source_stakes", {})
                            review_actor = actor_id
                        else:
                            source_trigger = scene["trigger_type"]
                            source_stakes = scene_stakes
                            # The current decision actor is usually the party with authority
                            # to answer the proposal; mediation asks that actor to review it
                            # again rather than inventing an omniscient mediator decision.
                            review_actor = actor_id
                        if review_actor:
                            mediation_scene = stable_id("SCENE",self.run_id,day,"informal_mediation_review",job["scene_id"],actor_id,review_actor)
                            if not con.execute("SELECT 1 FROM scenes WHERE scene_id=?",(mediation_scene,)).fetchone():
                                mediation_stakes={
                                    "situation_id":"SIT-015","mediation_requester_person_id":actor_id,
                                    "responder_person_id":review_actor,"source_scene_id":job["scene_id"],
                                    "source_trigger":source_trigger,"source_stakes":source_stakes,
                                    "issue":action.get("issue","unresolved household/economic disagreement"),
                                    "fixture_notice":"The informal mediation interface is ASM-FIXTURE-018: kin/patron/elder mediation is research-supported broadly, while the exact Ugaritic mediator/procedure remains unspecified.",
                                }
                                con.execute(
                                    "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (mediation_scene,self.run_id,day,scene["place_id"],"legal","informal_mediation_review",
                                     canonical_json(mediation_stakes),"{}",
                                     canonical_json({"private_negotiation_precedes_escalation":True,"exact_mediator_unspecified":True}),
                                     canonical_json(["I-MEDIATION"]),"open"),
                                )
                                con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(mediation_scene,actor_id,"mediation_requester"))
                                if review_actor != actor_id:
                                    con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(mediation_scene,review_actor,"decision_actor"))
                                else:
                                    con.execute("INSERT OR REPLACE INTO scene_participants VALUES (?,?,?)",(mediation_scene,review_actor,"decision_actor"))
                                self._event(
                                    con,day,"informal_mediation_review_opened",scene_id=mediation_scene,actors=list(dict.fromkeys([actor_id,review_actor])),
                                    rules=["ASM-FIXTURE-018","RULE-INFORMAL-DISPUTE-LADDER-001"],
                                    institutions={"I-MEDIATION":{"review":"opened"}},payload=mediation_stakes,discriminator=mediation_scene,
                                )
                                if source_trigger == "household_reserve_request":
                                    allowed=["accept_household_reserve","enter_obligation","communicate","refuse_proposal"]
                                elif source_trigger == "apprenticeship_progression_request":
                                    allowed=["grant_apprenticeship_progression","enter_obligation","communicate","refuse_proposal"]
                                elif source_trigger == "resource_request":
                                    allowed=["transfer_resource","enter_obligation","communicate","refuse_proposal"]
                                elif source_trigger == "draft_access_request":
                                    allowed=["grant_draft_access","enter_obligation","communicate","refuse_proposal"]
                                elif source_trigger == "reciprocal_labor_request":
                                    allowed=["fulfill_reciprocal_labor","enter_obligation","communicate","refuse_proposal"]
                                elif source_trigger == "marriage_household_terms_review":
                                    allowed=["accept_marriage_household_terms","enter_obligation","communicate","refuse_proposal"]
                                else:
                                    allowed=["enter_obligation","communicate","refuse_proposal"]
                                followups.append((mediation_scene,review_actor,allowed))

                elif typ == "travel":
                    dest = action["to_place_id"]
                    con.execute("UPDATE persons SET current_place_id=? WHERE person_id=?", (dest, actor_id))
                    eid = self._event(
                        con, day, "travel_started", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], payload={"action_id": aid, "to_place_id": dest,
                                                   "note": "V0.1 travel action changes place after validated adjacent-route move"},
                        discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Traveled to {dest}.", event_id=eid, memory_type="travel", salience=.4)

                elif typ == "wait":
                    eid = self._event(
                        con, day, "decision_to_wait", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "reason": action.get("reason"), "until_day": action.get("until_day")},
                        discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Chose to wait: {action.get('reason', 'no external action yet')}.",
                        event_id=eid, memory_type="decision", salience=.5, relationship_relevance=.1, goal_relevance=.65,
                    )

                elif typ == "refuse_proposal":
                    effective = scene_stakes.get("source_stakes", scene_stakes) if scene["trigger_type"] == "informal_mediation_review" else scene_stakes
                    requester = effective.get("requester_person_id")
                    actors = [actor_id] + ([requester] if requester and requester != actor_id else [])
                    relationship_delta: dict[str, Any] = {}
                    if requester and requester != actor_id:
                        relationship_delta[f"{actor_id}->{requester}"] = self._adjust_relationship(
                            con, actor_id, requester, trust=-.02, conflicts=1
                        )
                        relationship_delta[f"{requester}->{actor_id}"] = self._adjust_relationship(
                            con, requester, actor_id, trust=-.02, conflicts=1
                        )
                    eid = self._event(
                        con, day, "proposal_refused", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=actors, knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        rules=["ASM-FIXTURE-018","RULE-INFORMAL-DISPUTE-LADDER-001"] if requester else [],
                        relationships=relationship_delta,
                        payload={"action_id": aid, "reason": action.get("reason"), "requester_person_id": requester}, discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Refused: {action.get('reason', 'proposal not accepted')}.",
                                 event_id=eid, memory_type="decision", salience=.6, relationship_relevance=.65, goal_relevance=.6)
                    if requester and requester != actor_id:
                        self._memory(
                            con, requester, day, f"{actor_id} refused my proposal: {action.get('reason', 'proposal not accepted')}.",
                            event_id=eid, memory_type="decision", salience=.7, relationship_relevance=.82, goal_relevance=.7,
                        )
                        available_institutions=set(json.loads(scene["institution_ids_json"]))
                        if "I-MEDIATION" in available_institutions and scene["trigger_type"] not in {"informal_mediation_review","proposal_refusal_followup"}:
                            follow_scene=stable_id("SCENE",self.run_id,day,"proposal_refusal_followup",job["scene_id"],requester)
                            follow_stakes={
                                "situation_id":"SIT-015","requester_person_id":requester,"responder_person_id":actor_id,
                                "source_scene_id":job["scene_id"],"source_trigger":scene["trigger_type"],"source_stakes":effective,
                                "refusal_event_id":eid,"refusal_reason":action.get("reason"),
                                "fixture_notice":"One bounded informal-mediation opportunity after direct refusal under ASM-FIXTURE-018; no automatic settlement is imposed.",
                            }
                            con.execute(
                                "INSERT INTO scenes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (follow_scene,self.run_id,day,scene["place_id"],"legal","proposal_refusal_followup",
                                 canonical_json(follow_stakes),"{}",
                                 canonical_json({"private_negotiation_failed":True,"mediation_optional":True}),
                                 canonical_json(["I-MEDIATION"]),"open"),
                            )
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(follow_scene,requester,"decision_actor"))
                            con.execute("INSERT INTO scene_participants VALUES (?,?,?)",(follow_scene,actor_id,"responder"))
                            followups.append((follow_scene,requester,["seek_mediation","communicate","wait"]))

                else:
                    self._event(
                        con, day, "typed_action", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "type": typ, "action": action}, discriminator=aid,
                    )

            con.execute("UPDATE cognition_jobs SET status='accepted' WHERE job_id=?", (job_id,))
            con.execute("UPDATE scenes SET status='resolved' WHERE scene_id=?", (job["scene_id"],))
            self._event(
                con, day, "decision_accepted", scene_id=job["scene_id"], decision_id=decision_id,
                actors=[job["actor_person_id"]], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                payload={"intent": envelope.get("selected_intent"), "basis_tags": envelope.get("decision_basis_tags", []),
                         "declared_uncertainty": envelope.get("declared_uncertainty")}, discriminator=decision_id,
            )

        for scene_id, actor_person_id, allowed_actions in followups:
            self.enqueue_job(scene_id, actor_person_id, allowed_actions)
        return result

    def send_message(self, originator: str, recipient: str, proposition_id: str, content: str, travel_days: int) -> str:
        if travel_days < 0:
            raise ValueError("travel_days cannot be negative")
        departure = self.day
        arrival = departure + travel_days
        mid = stable_id("MSG", self.run_id, originator, recipient, proposition_id, departure, content)
        with self.db.transaction() as con:
            con.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (mid, originator, recipient, proposition_id, content, None, "Ugaritic_or_mediated", "inform", None, None,
                 departure, arrival, None, "{}", "ordinary"),
            )
            self._event(
                con, departure, "message_sent", actors=[originator], rules=["RULE-MESSAGE-DELAY-001"],
                payload={"message_id": mid, "recipient": recipient, "arrival_day": arrival}, discriminator=mid,
            )
        return mid
