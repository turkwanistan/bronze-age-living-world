# Accepted Day-240 v007 Care / Property / Sowing Gate

## Canonical runtime

- DB: `state/ugarit_living_v007.sqlite`
- run: `RUN-3dda7920595c1748`
- seed: 1701
- scenario: 0.5.0
- schema: 3
- day: 240
- state hash: `7cd79256a5affcff0b65b8c98f22be5078e46ab0bd2b3e0ce014e778f4363f86`
- events: 3,412
- cognition: 80 accepted / 0 rejected / 0 pending
- open scenes: 0
- tests: 53/53
- replay: exact 80 stored decisions, 0 new cognition calls

## Accepted evidence

1. Archived replay is source-sealed: accepted v006 still reproduces its exact day-180 hash under current code despite repository scenario/schema advancement.
2. Neutral provisioning follows current living household composition while conserving the global fixture baseline at exactly 5.08 daily units.
3. Šapšu's residence change therefore moves neutral burden/receipt from H-RITUAL to H-WIDOW rather than leaving both households economically frozen at day-0 composition.
4. Kothar fulfills concrete continuing-care episodes on days 184 and 214.
5. Bat-Rapiu independently records a non-binding care-informed property preference on day 214. No ownership, inheritance, or resource transfer occurs; the continuing care obligation remains active.
6. Arhalbu requests one bounded sowing-season draft service from Ilimilku on day 182. Ilimilku grants it without manufactured conflict.
7. The day-183 service transfers modeled field capacity: H-DEPEND +0.10 sowing progress, H-FARM −0.05 opportunity-cost progress; a social favor is recorded.
8. Arhalbu's day-210 palace obligation collides with agricultural intensity 0.98 and is moved to day 240. It completes deterministically when the calendar reaches wet-winter growth at intensity 0.55.
9. Yabninu's 16.5 silver reserve remains binding through later port opportunities.
10. Urtenu/Yabninu complete the fourth reciprocal metal cycle. On the fifth cycle, shrinking supplier stock changes behavior: Urtenu requests only 0.3 rather than 0.6, Yabninu retains 0.3, and Urtenu later refuses to stack another request while that fifth obligation remains open.
11. Runtime illness continues to interrupt ordinary plans independently; no illness is retroactively attributed to new care/sowing mechanics.
12. No resource-shortfall scene/event, rejected cognition, open scene, or knowledge-before-arrival violation exists at acceptance.

## Calibration boundaries

- Composition-neutral provisioning is an engineering stability model, not a historical ration/consumption estimate.
- Care episode timing/task and the two-episode preference review threshold are fixtures.
- `property_preferences` are living, non-binding preferences only; no Ugaritic succession law is inferred.
- H-FARM/H-DEPEND draft-access asymmetry, one-day service, +0.10 beneficiary progress and −0.05 holder opportunity cost are fixtures, not livestock ownership/plowing-rate claims.
- Sowing progress is not crop yield.
- All workshop exchange quantities remain abstract fixture units; repeated reciprocity is not a price or standing contract.

## Gate result

**ACCEPTED.** The v007 slice adds material household composition, active kin care, care-informed but non-binding property strategy, and socially negotiated sowing capacity while preserving exact replay, containment, baseline stability, and prior accepted histories.
