# ACCEPTED V020 — Long-Horizon Relationship Memory + Recovery Validation

v020 is a **packet-policy and validation checkpoint**. It does not replace canonical seed-1701 history at day 462.

## Canonical authority preserved

Canonical runtime remains accepted v015:

- `state/ugarit_living_v015.sqlite`
- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- day `462`
- 6,608 events
- 157 accepted / 0 rejected / 0 pending / 0 open
- hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`

The repository's **next-scenario** configuration is now `0.14.0`, with `v020_relationship_memory_start_day=463`.

## Modeling gap found

The day-308 P3→P7 scarcity refusal remained in canonical memory and the relationship retained `conflicts=1`, but by day 360 the refusal memory had fallen out of P3's sealed packet. The existing v008 conflict-memory rule retained recent decision/refusal memories for only 30 days.

A future character could therefore see that conflict existed without receiving the causal decision that created it.

## v020 packet rule

From the v020 boundary onward, when an actor has a directed relationship with recorded conflict, packet compilation may retain **at most two older relationship-relevant decision memories** beyond the recent-memory window.

A retained memory must:

- be a `decision` memory;
- have `relationship_relevance >= 0.5`;
- have a causal event;
- have that causal event include the specific conflicted counterparty.

This prevents an unrelated relationship dispute from being pulled into the wrong relationship context.

The rule preserves history. It does not imply the conflict remains unresolved, does not increase conflict by itself, and does not create an automatic grudge or reconciliation state.

## Compatibility gate

`scripts/relationship_recovery_validation.py` rebuilds the accepted v015 policy under current scenario `0.14.0` through day 462.

Result:

- all **157** recorded decisions applied;
- **6,608** events;
- 0 pending / 0 rejected;
- no new pre-day-463 cognition boundaries;
- validation branch hash `22f77b40799dcd664be02fd9e754480ba451ab019921453ac02acc6ebb09b9aa`.

The hash differs from canonical v015 because scenario configuration is canonical state. Behavioral history through day 462 is unchanged.

## Day-463 controlled branches

Both branches begin with the same P3↔P7 history, including six completed reciprocal exchanges, one recorded scarcity conflict and the old day-308 refusal memory visible in the sealed packet.

### Unchanged scarcity

H-MERCH still has only `0.15` raw metal. P7 requests `0.12`.

Fresh validation decision: P3 refuses again because the material reason for the prior refusal has not changed.

Result:

- merchant metal remains `0.15`;
- no new reciprocal obligation;
- no negative resource stock;
- repeated unchanged request adds the normal modeled refusal strain rather than pretending the old conflict disappeared.

### Recovered capacity

Only H-MERCH metal changes to `0.60`; relationship and repayment history remain the same. P7 again requests `0.12`.

Fresh validation decision: P3 resumes bounded reciprocal supply.

Result:

- merchant metal `0.60 → 0.48`;
- craft metal increases by exactly `0.12`;
- one bounded reciprocal obligation is created;
- no negative resource stock;
- old refusal memory remains visible, demonstrating that remembered conflict does not lock the character into permanent refusal.

## Existing canonical repair evidence

No new explicit reconciliation action is required merely to make relationship recovery possible.

Accepted v009 already contains a lower-cost cooperation step after the day-308 refusal: P3 grants P7 a harbor-market introduction on day 361 while still refusing to spend the last raw-metal reserve.

P3→P7 changes across accepted v008→v009:

- trust `0.77 → 0.78`;
- respect `0.67 → 0.68`;
- conflicts remain `1`.

P7→P3:

- trust `0.83 → 0.85`;
- respect `0.61 → 0.62`;
- conflicts remain `1`.

Thus later useful cooperation can improve the relationship without deleting disagreement history.

## Interpretation

The desired behavior is **memory without grudge lock-in**:

- past conflict remains causally intelligible;
- present material constraints can still justify refusal;
- changed conditions can justify a different choice;
- later low-cost cooperation can repair trust/respect;
- historical conflict is not magically erased.

No new historical claim is introduced, so the evidence claim/assumption index is unchanged.
