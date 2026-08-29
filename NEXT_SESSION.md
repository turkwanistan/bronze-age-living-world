# NEXT SESSION

Start from the accepted strict day-60 checkpoint in `STATUS.md` and `runs/ACCEPTED_DAY60.md`.

1. Verify permanent repository/Git state, authority hashes, `state/current.json`, and `state/ugarit_living_v002.sqlite` before changing behavior.
2. Run the full test suite and an exact recorded-decision replay of the accepted day-60 run before extending it.
3. Preserve the accepted day-60 DB/history. If scene-generation rules change, branch/rebuild a fresh candidate from seed instead of mutating accepted history.
4. Broaden ordinary-life situation diversity rather than maximizing cognition/event count. Highest-value next families are:
   - household disagreement over outside work or resource priorities;
   - water-access negotiation/dispute with deliberately modest procedural claims;
   - feast/status/reciprocity situations;
   - palace labor/resource request where supported by the existing evidence model.
5. Keep consequential cognition pull-based and sparse. Resolve only genuinely consequential jobs from sealed character packets; do not use internet/research while inhabiting a character.
6. Continue testing persistent consequences: later choices should reflect delivered information, remembered aid/debt, changed relationships, obligations, reputation, and material state.
7. Deepen Ugarit research only where it changes an active rule, especially ordinary debt/property/household procedure, names, and institution access. Preserve uncertainty where evidence is weak.
8. Add observer/inspection tooling only after the simulation itself needs it; do not add generic agent infrastructure, new databases, model APIs, microservices, or a new SBC generation without demonstrated reusable need.
9. At the next coherent accepted checkpoint, update evidence mappings, tests, `STATUS.md`, `NEXT_SESSION.md`, derived state, and a new acceptance manifest. Exact replay must remain possible without new cognition calls.

Current accepted gate facts:

- day 60, seed 1701;
- state hash `2b59046401f398c24604eee4242e12865690a64749811b6c56d31c5c3eb0f504`;
- 27/27 tests passing;
- 8 accepted cognition decisions, 0 rejected/pending;
- exact recorded-decision replay with 0 new cognition calls;
- 0 resource-shortfall scenes in the accepted run;
- delayed merchant/harbor inquiry/reply flow passes epistemic containment.

The governing principle remains: **The world is structured. The people are not scripted.**
