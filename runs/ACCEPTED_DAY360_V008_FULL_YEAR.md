# Accepted Day-360 v008 Full Ordinary-Year Gate

## Canonical runtime

- DB: `state/ugarit_living_v008.sqlite`
- run: `RUN-3dda7920595c1748`
- seed: 1701
- scenario: 0.6.0
- schema: 3
- day: 360
- state hash: `66afa78360be1ba12b67639e844aee71079480d1df562df45f450e514796f6ce`
- events: 5,073
- cognition: 106 accepted / 0 rejected / 0 pending
- open scenes: 0
- tests: 58/58
- replay: exact 106 stored decisions, 0 new cognition calls

## Full-year acceptance evidence

1. The strict run traverses all six modeled seasonal phases and returns to the starting cereal-harvest phase on day 360.
2. Routine life dominates the event record: 2,880 consumption events, 816 occupation cycles, 408 household labor allocations, 408 weekly receipts, 96 household rituals, and 51 port cycles.
3. Global neutral provisioning remains exactly conserved at 5.08 fixture units/day despite the accepted marriage residence change; no resource-shortfall scene/event occurs.
4. No message is delivered before arrival and no message-sourced knowledge appears before delivery.
5. No resource stock is negative; no scheduled obligation is overdue at the gate.
6. Kothar fulfills six concrete continuing-care episodes. Bat-Rapiu's care-informed property preference remains active and non-binding; no ownership/inheritance transfer occurs.
7. The P16/P10 marriage and normalized kinship remain canonical; Šapšu remains resident in H-WIDOW with ritual/healing roles intact.
8. The H-FARM→H-DEPEND sowing draft service creates a remembered favor; in winter Ilimilku calls that favor in for one bounded maintenance service, Arhalbu accepts, and the favor clears only after actual completion.
9. The draft-team winter episode records exactly two condition-loss cycles, restores condition to 1.0 on completion, and then stops degrading for the remainder of that modeled winter.
10. Six P7↔P3 metal social-credit cycles are fully repaid. Smaller support amounts produce conservatively capped later return suggestions rather than an invariant 0.3 return.
11. Urtenu adapts requests downward as supplier stock shrinks: 0.6 → 0.3 → 0.15 → a 0.12 deficit request.
12. Yabninu naturally refuses the day-308 0.12 request because his household has only 0.15 raw metal left. The relationship incurs modest strain but remains intact.
13. The recent refusal remains in Urtenu's sealed packets despite older high-salience workshop history; Urtenu waits on days 322, 336 and 350 instead of pretending the scarcity refusal never happened.
14. Yabninu's 16.5 silver reserve remains binding through later port opportunities.
15. All cognition is replayable from stored decisions with zero new model calls and exact final hash equality.

## Calibration / historical boundaries

- Seasonal ordering is research-constrained; exact phase lengths/day offset are fixture calibration.
- Routine provisioning is an engineering stability substrate, not a historical ration or yield model.
- Draft-team condition, winter maintenance cadence, restoration, service duration and household pairing are fixture values.
- Reciprocal social credit is qualitative; no return suggestion is a historical price, interest rate or exchange equivalence.
- Marriage residence/care terms and Bat-Rapiu's property preference are bounded simulation choices, not a universal Ugaritic marriage/inheritance procedure.
- Runtime illness frequency is unhistorical fixture calibration.
- One successful year for seed 1701 is an architecture/stability result, not a claim about Bronze Age behavioral frequencies.

## Accepted v008 rules

- `RULE-WINTER-RECIPROCAL-LABOR-001` / `ASM-FIXTURE-025`
- `RULE-RECIPROCAL-RETURN-CAP-001` / `ASM-FIXTURE-026`
- `RULE-RECENT-CONFLICT-MEMORY-001`

See `STATUS.md` and evidence mappings `MAP-029` through `MAP-031` for implementation/test traceability.
