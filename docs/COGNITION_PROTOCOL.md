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
- from the v008 packet-policy boundary onward, recent refusal/decision memories are retained when an active relationship conflict exists so current strain cannot be hidden by older high-salience history;
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
- `request_reciprocal_labor` / `fulfill_reciprocal_labor` — call in and answer one bounded practical labor favor; the social favor clears only when the scheduled service actually completes
- `handle_winter_maintenance_internally` — resolve the current fixture winter-maintenance episode without consuming an outstanding social favor
- `request_fuel_haul` / `accept_fuel_haul` / `decline_fuel_haul` — negotiate one bounded paid fuel-feedstock haul; payment and material delivery occur only after scheduled completion
- `prepare_charcoal_fuel` — consume finite household fuel feedstock to prepare workshop charcoal under explicit fixture calibration; no free fuel
- `repair_workshop_tool` — consume the exact sealed finished-work input and schedule a bounded repair; tool condition restores only when the repair obligation completes
- `accept_alternate_metal_exchange` — may also accept a sealed disrupted repeat-market lot when the changed terms have actually arrived through the information network
- `recycle_finished_metalwork` — sacrifice bounded finished output for a smaller raw-metal recovery under explicit fixture calibration
- `request_market_introduction` / `grant_market_introduction` — ask an existing merchant relationship for a contact introduction without implying hidden supplier knowledge or guaranteed supply
- `accept_alternate_metal_exchange` — accept only terms already delivered into the actor packet; silver moves immediately and metal arrives later through a scheduled exchange
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
- `protect_exposed_stores` / `accept_weather_storage_loss` — resolve one bounded local weather/storage exposure affecting only exposed seasonal produce; protection commits one modeled household labor day and reduces, but does not eliminate, fixture loss.
