# Accepted strict day-140 Ugarit v005 household/life-course gate

## Identity

- canonical DB: `state/ugarit_living_v005.sqlite` (host-local, Git-ignored)
- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.3.0`
- accepted day: **140**
- state hash: `959421734528a6c59c0cfe84494c4d9556d29988d9df7424ef773b217056d0df`
- events: **1966**
- cognition: **40 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **43/43 passing**
- recorded-decision replay: **40 stored decisions / 0 new cognition / exact hash match**

## Accepted additions after v004

### Household strategy becomes canonical

After repeated completed port exchanges, Pidduya can open a private household resource-priority negotiation with Yabninu. On day 91 she asked that the merchant household preserve 16.5 abstract silver units. Yabninu accepted. The result is an active `household_reserve_commitment`, not flavor text.

The constraint later matters: Yabninu made one final 0.5 fixture exchange on day 98, leaving exactly 16.5. At the next port opportunity on day 126 he waited because a new standard commitment would violate the household agreement. Validation independently rejects a trade that crosses the floor.

The reserve threshold/floor are `ASM-FIXTURE-016` engineering calibration, not a reconstructed Ugaritic property or capital rule.

### Apprenticeship produces a real life-course transition

Niqmepa's day-91 progression opportunity arose only after accumulated canonical apprenticeship history: 91 simulation days, at least twelve recorded apprenticeship work cycles, and workshop output. He asked Urtenu for recognition rather than changing his own status unilaterally. Urtenu accepted.

Canonical consequences:

- active `craft_apprentice` role ended day 91;
- active `recognized_craft_worker` role began day 91;
- household membership changed from `apprentice` to `attached_worker`;
- simulation legal status became `dependent_craft_worker`;
- Urtenu↔Niqmepa relationship types became workshop/craft mentor;
- trust/respect and autobiographical memories changed;
- subsequent weekly occupation cycles use the new role and its material workflow.

These labels/thresholds are `ASM-FIXTURE-017` simulation mechanics, not a claim about universal Ugaritic apprenticeship law, rank, emancipation, or duration.

### Informal dispute ladder exists without forcing conflict

`I-MEDIATION` represents a bounded abstract kin/patron/elder-style mediation interface. Direct proposal refusal can create relationship strain and exactly one optional mediation review. The review does not invent a neutral omniscient verdict; the relevant party receives a new typed decision. Regression tests prove refusal -> conflict delta -> optional mediation -> reviewed settlement.

The strict v005 history did **not** contain a proposal refusal or mediation review: both new day-91 negotiations resolved consensually. This is intentional. The engine has the capability but does not manufacture conflict merely to exercise it.

`ASM-FIXTURE-018` explicitly leaves exact mediator identity, authority and Ugaritic procedure unspecified.

### Persistent exchange relationship

Urtenu/Yabninu now demonstrate repeated specialist supply with social consequences:

1. first metal support -> reciprocal obligation -> workshop output return -> fulfilled;
2. second support day 98 -> Urtenu later waits rather than stack a third unpaid advance -> second return day 128 -> fulfilled;
3. third support begins day 140 only after the second obligation is cleared.

Trust/respect increase across the relationship while each new advance remains a separate bounded obligation rather than entitlement or a standing contract.

### Seasonal institutional behavior fixed

A v005 development run exposed that palace rescheduling only knew the cereal-harvest boundary. During the later grape/olive/field-preparation phase it would have proposed another still-high-intensity day. `RULE-SEASONAL-LABOR-CONFLICT-001` now searches the modeled calendar for the next genuinely lower-intensity phase.

In the accepted strict history, Arhalbu chose differently by season: he deferred during the original 1.00 cereal-harvest bottleneck, but on day 140 accepted palace service during the 0.88 grape/olive/field-preparation phase. This demonstrates seasonal context affecting judgment without scripting one universal response.

## Qualitative gate

- 0 `household_resource_shortfall` scenes.
- 0 message-before-delivery knowledge violations.
- 40 decisions across 140 days remain sparse relative to 1,966 canonical events.
- 20 weekly port/market cycles and 320 occupation work cycles occurred.
- 32 recurring household ritual observances occurred.
- 8 stochastic minor-illness scenes generated differentiated responses rather than one universal template.
- day-126 port trade visibly obeyed the day-91 household reserve agreement.
- Niqmepa's new role is visible in current roles, membership, status, memories, mentor relation and later occupational workflow.
- informal mediation is test-proven but was not invoked in strict history because no accepted disagreement required it.

## Evidence/rules

- `MAP-018` / `RULE-HOUSEHOLD-RESOURCE-PRIORITY-001` / `ASM-FIXTURE-016`
- `MAP-019` / `RULE-APPRENTICESHIP-PROGRESSION-001` / `ASM-FIXTURE-017`
- `MAP-020` / `RULE-INFORMAL-DISPUTE-LADDER-001` / `ASM-FIXTURE-018`
- `MAP-021` / `RULE-SEASONAL-LABOR-CONFLICT-001` / `ASM-FIXTURE-008,011`

The governing principle remains: **The world is structured. The people are not scripted.**
