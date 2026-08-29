# Accepted strict day-60 checkpoint — v003 ordinary social slice

This is the accepted successor to `runs/ACCEPTED_DAY60.md`. The earlier v002 day-60 history remains a preserved baseline; scene-generation changes were evaluated in a fresh DB rebuilt from seed rather than by mutating it.

## Canonical strict run

- DB: `state/ugarit_living_v003.sqlite` (host-local canonical SQLite; intentionally ignored by Git)
- run_id: `RUN-3dda7920595c1748`
- seed: `1701`
- accepted day: **60**
- state hash: `96994dcc063475fb2cc449d933d71510b6f99e6af23563bbfcbf393be7a9ce8c`
- events: **593**
- cognition: **12 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- full test suite: **30/30 passing**
- recorded-decision replay: **12 stored decisions applied, 0 new cognition calls, exact state-hash match**

## New accepted ordinary-life chains

### Household work negotiation

A fixture work opportunity is presented to P16/Kothar without exposing P15/Bat-Rapiu's private preferences. Kothar asks the household senior rather than acting unilaterally. Bat-Rapiu receives her own sealed packet, accepts the one-day opportunity, and the engine schedules completion rather than paying immediately.

On day 15 the engine deterministically completes the accepted work, fulfills its scheduled obligation, adds the explicit 1.0 abstract-grain fixture receipt to H-WIDOW, and writes memories for both people. Their directed trust/respect changes persist into later state. Timing, duration, compensation, and contract form are explicitly `ASM-FIXTURE-006`, not historical wage evidence.

### Unequal water-access negotiation

A fixture disruption makes H-FARM's shared access temporarily consequential while P6/Talmiyanu's H-SCRIBE household has private access. P2/Ahatmilku asks the specifically known neighbor for two days of negotiated access rather than treating access as an entitlement or immediately escalating.

Talmiyanu receives a separate sealed packet and grants the bounded request. The engine records an `I-WATER` institutional grant, creates a temporary permission, changes reciprocal favor/relationship state, writes memories for both people, and deterministically expires the permission after its last allowed day. The disruption, neighbor pairing, duration, and exact procedure are explicit `ASM-FIXTURE-007` simulation circumstances; they are not claims about a specific historical Ugaritic event or legal rule.

## Causal/containment audit

- `household_resource_shortfall` scenes: **0**
- `projected_resource_shortfall_detected` events: **0**
- work opportunity/request/agreement/completion events: exactly **1 each**
- water pressure/request/grant/expiry events: exactly **1 each**
- scheduled outside-work obligation ends `fulfilled`
- temporary water-access permission ends `expired`
- later P15 packets contain Kothar's request/agreement/completion memories and the changed kin relationship
- later P2 packets contain request/grant/expiry water memories plus a favor owed to P6
- unrelated P14 and P13 sealed packets remain byte-identical to the prior accepted baseline at their day-27/day-28 boundaries
- no rejected cognition and no unresolved scenes at day 60

## Replay defect found and fixed during acceptance

The first v003 recorded replay correctly reconstructed material outcomes but failed exact hashing because two accepted day-8 decisions had been applied in source order P12 → P11 while replay used destination cognition-job creation order P11 → P12. Event and memory IDs are sequence-sensitive, so exact replay must reproduce canonical decision application order.

`RULE-RECORDED-REPLAY-ORDER-001` now uses source decision insertion/application sequence and reapplies one currently available cognition decision at a time, re-querying after every action so same-day follow-up jobs can interleave correctly. A regression test deliberately records P12 before P11 and proves exact replay preserves that order.

## Interpretation limits

This checkpoint demonstrates richer causal ordinary-life behavior, not historical calibration. All resource/work timing values and the temporary water disruption remain explicit fixture abstractions. The day-14 work and day-18 water situations are currently deterministic benchmark fixtures, not yet a generalized stochastic/emergent situation generator.
