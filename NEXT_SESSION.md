# NEXT SESSION

Start from the accepted strict v003 day-60 checkpoint in `STATUS.md` and `runs/ACCEPTED_DAY60_V003_SOCIAL.md`.

1. Verify permanent repository/Git state, authority hashes, `state/current.json`, and the host-local `state/ugarit_living_v003.sqlite` before changing behavior.
2. Run the full test suite and exact recorded-decision replay of v003 before extending it. Replay must preserve source decision application sequence (`RULE-RECORDED-REPLAY-ORDER-001`).
3. Preserve v002 and v003 accepted histories. If scene-generation rules change, rebuild a fresh candidate from seed rather than mutating either accepted DB.
4. Broaden ordinary life without simply adding more mandatory cognition. Highest-value next families are:
   - feast/status/reciprocity where attendance, contribution, reputation, household security, and prior favors can conflict;
   - palace/institutional labor or resource request where rank, obligation, household cost, and access are consequential;
   - craft/work complication or market exchange that makes occupation materially meaningful;
   - household/kin disagreement that can produce compromise, refusal, obligation, or later relationship effects.
5. Generalize situation eligibility gradually. The day-14 outside-work and day-18 water-pressure scenes are accepted benchmark fixtures, but future ordinary situations should increasingly arise from state/relationships/schedules rather than fixed calendar days. Do not sacrifice replayability or evidence labeling to make them feel emergent.
6. Continue testing persistent consequences. Later packets should reflect relevant remembered work, aid, debt, water favors, relationship changes, obligations, information provenance, and material state while unrelated characters remain contained.
7. Move toward the Phase-5 behavioral gate of **50–100 inspected cognition decisions**, using paired/counterfactual situations where useful. Do not interpret LLM choice frequency as historical prevalence.
8. Deepen Ugarit research only where it changes an active rule, especially ordinary debt/property/household procedure, institution access, labor obligations, feast/status behavior, and names. Preserve uncertainty where evidence is weak.
9. Add observer/inspection tooling only when the simulation itself needs it. Do not add generic agent infrastructure, new databases, model APIs, microservices, or a new SBC generation without demonstrated reusable need.
10. At the next coherent accepted checkpoint, update evidence mappings, tests, `STATUS.md`, `NEXT_SESSION.md`, derived state, and a new acceptance manifest. Exact replay with zero new cognition calls remains mandatory.

Current accepted v003 gate facts:

- day 60, seed 1701;
- state hash `96994dcc063475fb2cc449d933d71510b6f99e6af23563bbfcbf393be7a9ce8c`;
- 30/30 tests passing;
- 12 accepted cognition decisions, 0 rejected/pending;
- exact recorded-decision replay with 12 stored decisions and 0 new cognition calls;
- 0 resource-shortfall scenes;
- 10 situation trigger types;
- accepted work chain: request → agreement → scheduled completion → household receipt/memory/relationship effects;
- accepted water chain: pressure → request → bounded grant → favor/relationship effects → deterministic expiry;
- replay preserves same-day source decision application order.

The governing principle remains: **The world is structured. The people are not scripted.**
