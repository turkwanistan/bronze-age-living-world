from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any

from .cognition import _build_packet, packet_hash
from .db import WorldDB, canonical_json
from .ids import stable_id


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

    def _adjust_relationship(self, con, from_person: str, to_person: str, *, trust: float = 0,
                             respect: float = 0, favors_given: float = 0, favors_owed: float = 0) -> dict[str, float]:
        row = con.execute(
            "SELECT trust,respect,favors_given,favors_owed FROM relationships WHERE from_person_id=? AND to_person_id=?",
            (from_person, to_person),
        ).fetchone()
        if not row:
            return {}
        new_trust = max(0.0, min(1.0, float(row[0]) + trust))
        new_respect = max(0.0, min(1.0, float(row[1]) + respect))
        con.execute(
            "UPDATE relationships SET trust=?,respect=?,favors_given=favors_given+?,favors_owed=favors_owed+?,last_contact_day=? WHERE from_person_id=? AND to_person_id=?",
            (new_trust, new_respect, favors_given, favors_owed, self.day, from_person, to_person),
        )
        return {"trust": new_trust, "respect": new_respect, "favors_given_delta": favors_given, "favors_owed_delta": favors_owed}

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
                for h in con.execute(
                    "SELECT household_id,fixture_daily_food_need,fixture_weekly_receipt FROM households ORDER BY household_id"
                ).fetchall():
                    stock = con.execute(
                        "SELECT amount FROM resource_stocks WHERE household_id=? AND resource_type='grain'",
                        (h["household_id"],),
                    ).fetchone()[0]
                    consume = min(float(stock), float(h["fixture_daily_food_need"]))
                    con.execute(
                        "UPDATE resource_stocks SET amount=amount-? WHERE household_id=? AND resource_type='grain'",
                        (consume, h["household_id"]),
                    )
                    self._event(
                        con, target_day, "routine_consumption", rules=["ASM-FIXTURE-002"],
                        material={h["household_id"]: {"grain": -consume}},
                        payload={"notice": "abstract fixture unit"}, discriminator=h["household_id"],
                    )
                    if target_day % 7 == 0:
                        receipt = float(h["fixture_weekly_receipt"])
                        con.execute(
                            "UPDATE resource_stocks SET amount=amount+? WHERE household_id=? AND resource_type='grain'",
                            (receipt, h["household_id"]),
                        )
                        self._event(
                            con, target_day, "routine_weekly_receipt", rules=["ASM-FIXTURE-002"],
                            material={h["household_id"]: {"grain": receipt}},
                            payload={"notice": "abstract fixture unit"}, discriminator=h["household_id"],
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
            "SELECT h.fixture_daily_food_need,h.fixture_weekly_receipt,rs.amount "
            "FROM households h JOIN resource_stocks rs USING(household_id) "
            "WHERE h.household_id=? AND rs.resource_type='grain'",
            (household_id,),
        )
        if not row:
            raise KeyError(household_id)
        current = float(row["amount"])
        daily_need = float(row["fixture_daily_food_need"])
        weekly_receipt = float(row["fixture_weekly_receipt"])
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

        obligations = self.db.all(
            "SELECT * FROM obligations WHERE status='active' AND due_day IS NOT NULL AND due_day<=? ORDER BY obligation_id",
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
                    if obligation_id:
                        obligation = con.execute("SELECT * FROM obligations WHERE obligation_id=?", (obligation_id,)).fetchone()
                        con.execute("UPDATE obligations SET status='fulfilled' WHERE obligation_id=?", (obligation_id,))
                        target_person = obligation["beneficiary_person_id"] or target_person
                        if target_person:
                            relationship_delta[f"{actor_id}->{target_person}"] = self._adjust_relationship(
                                con, actor_id, target_person, trust=.03, respect=.01
                            )
                            relationship_delta[f"{target_person}->{actor_id}"] = self._adjust_relationship(
                                con, target_person, actor_id, trust=.04, respect=.02
                            )
                    elif target_person:
                        relationship_delta[f"{actor_id}->{target_person}"] = self._adjust_relationship(
                            con, actor_id, target_person, favors_given=1
                        )
                        relationship_delta[f"{target_person}->{actor_id}"] = self._adjust_relationship(
                            con, target_person, actor_id, trust=.02, favors_owed=1
                        )
                    eid = self._event(
                        con, day, "resource_transfer", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id] + ([target_person] if target_person else []), causes=causes,
                        knowledge=envelope.get("decisive_knowledge_or_belief_ids", []), rules=["RULE-ATOMIC-EVENT-001"],
                        material={actor_household: {resource: -amount}, target: {resource: amount}},
                        relationships=relationship_delta,
                        payload={"action_id": aid, "fulfills_obligation_id": obligation_id}, discriminator=aid,
                    )
                    self._memory(
                        con, actor_id, day, f"Transferred {amount:g} {resource} to {target}.", event_id=eid,
                        memory_type="resource_exchange", salience=.72, relationship_relevance=.7, goal_relevance=.7,
                    )
                    if target_person:
                        self._memory(
                            con, target_person, day, f"{actor_id} transferred {amount:g} {resource} to my household.",
                            event_id=eid, memory_type="resource_exchange", salience=.78,
                            relationship_relevance=.85, goal_relevance=.6,
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
                        institutions={iid: {"requested": True}}, payload={"action_id": aid, "issue": action.get("issue")},
                        discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Sought mediation through {iid}: {action.get('issue', 'a dispute')}.",
                                 event_id=eid, memory_type="institutional_action", salience=.7)

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
                    eid = self._event(
                        con, day, "proposal_refused", scene_id=job["scene_id"], decision_id=decision_id,
                        actors=[actor_id], knowledge=envelope.get("decisive_knowledge_or_belief_ids", []),
                        payload={"action_id": aid, "reason": action.get("reason")}, discriminator=aid,
                    )
                    self._memory(con, actor_id, day, f"Refused: {action.get('reason', 'proposal not accepted')}.",
                                 event_id=eid, memory_type="decision", salience=.6, relationship_relevance=.5, goal_relevance=.6)

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
