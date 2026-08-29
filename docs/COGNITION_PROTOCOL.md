# Cognition Protocol v1

## Boundary

The simulation engine decides **when** cognition is useful. ChatGPT never receives unrestricted database access while inhabiting a character.

## Pull workflow

1. advance routine world;
2. detect consequential situation;
3. create scene;
4. compile one character-scoped packet;
5. persist pending cognition job;
6. ChatGPT reads the pending packet;
7. ChatGPT returns a structured decision envelope;
8. engine validates factual premises and every typed action;
9. accepted actions and their events commit atomically;
10. rejected decisions remain rejected and may receive one bounded correction attempt;
11. later replay reuses the recorded validated decision instead of silently re-reasoning.

## Packet minimum

- protocol version;
- job/scene/run/time/place IDs;
- actor identity, life/status state, household;
- relevant roles;
- relevant persistent dispositions;
- current household-controlled resources;
- relevant directed relationships;
- normalized active marriage and kinship state when the run schema supports it;
- active non-binding property preferences when the run schema supports them;
- admissible knowledge/belief/rumor IDs only;
- relevant memories;
- active obligations and debts touching the actor or household;
- available institutions and constraints;
- active stakes/goals;
- allowed typed action families.

No hidden world facts are included merely because they would make the decision easier.

## Decision envelope

```json
{
  "decision_id": "...",
  "actor_id": "...",
  "selected_intent": "...",
  "proposed_actions": [
    {"type": "transfer_resource", "target_household_id": "...", "resource": "grain", "amount": 3}
  ],
  "optional_communicated_content": null,
  "decisive_knowledge_or_belief_ids": ["K-..."],
  "decision_basis_tags": ["household_security", "reciprocity"],
  "declared_uncertainty": "..."
}
```

Do not provide hidden chain-of-thought. A concise basis summary/tags is enough.

## Initial typed actions

- `transfer_resource`
- `communicate`
- `send_message` — delayed route-validated inquiry/report; reports require a proposition already present in the sender packet
- `enter_obligation`
- `repay_debt`
- `request_household_work_agreement` — ask a co-located household senior to decide a bounded fixture work opportunity
- `accept_fixture_work` / `decline_fixture_work` — resolve that specific work opportunity; accepted work completes later through engine time
- `request_water_access` — request bounded temporary access from the scene-designated private-access neighbor
- `grant_water_access` — create a temporary institution-linked permission that expires deterministically
- `request_household_reserve_agreement` / `accept_household_reserve` — negotiate a household-controlled reserve that later material actions must obey
- `request_apprenticeship_progression` / `grant_apprenticeship_progression` — negotiate a work/life-course role transition grounded in accumulated occupational history
- `request_marriage_discussion` / `accept_marriage_discussion` — open a bounded prospective-marriage negotiation without creating marriage state
- `propose_marriage_household_terms` / `accept_marriage_household_terms` — negotiate residence/care terms between two households
- `give_marriage_consent` / `decline_marriage_consent` — separate final individual consent; a decline creates no marriage and is not overridden by mediation
- `preserve_seasonal_surplus` — convert bounded exposed seasonal produce into stored seasonal goods under explicit fixture calibration
- `fulfill_kin_care` / `defer_kin_care` — resolve a concrete episode under an already-active continuing-care term without automatically ending that term
- `record_property_preference` — record a non-binding living property preference after supported care history; never transfers ownership by itself
- `request_draft_access` / `grant_draft_access` — negotiate a bounded sowing-season service whose delayed completion transfers modeled field capacity and records social obligation
- `seek_mediation`
- `perform_ritual`
- `accept_proposal`
- `refuse_proposal`
- `travel`

The grammar expands only when a real scene needs a reusable family.

## Fail-closed validation

As applicable, validate:

- actor alive and available;
- actor matches job;
- cited knowledge/belief IDs are present in the packet;
- target exists;
- place/reachability and time cost;
- resource ownership/control and non-negative result;
- debt/obligation consistency;
- institutional procedure/access/authority;
- language/communication feasibility when modeled;
- action is allowed for this scene;
- state update and event append occur in one transaction.

A fluent or historically plausible sentence cannot bypass these checks.
