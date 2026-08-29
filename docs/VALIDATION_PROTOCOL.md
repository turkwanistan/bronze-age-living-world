# Validation Protocol

This project distinguishes **exact replay**, **semantic policy-transfer validation**, **fresh cognition**, and **paired counterfactuals**. They answer different questions and must not be conflated.

## Exact replay

Exact replay rebuilds one accepted run from its seed and already-recorded accepted decisions. It must use zero new cognition and reproduce the canonical state hash exactly. This remains the acceptance requirement for the canonical strict history.

## Semantic policy-transfer validation

`scripts/semantic_seed_validation.py` is validation-only. It is not replay and it is not an independent cognition sample.

It initializes another RNG seed under the same accepted scenario and attempts to hold the accepted source run's **semantic decision policy** constant when comparable scenes recur.

A comparable scene is matched by the same actor plus scene trigger. Source decisions are used in source occurrence order. Run-derived scene/obligation/message values are rebound only through corresponding destination packet stakes. Decisive knowledge is rebound only to knowledge that is actually present in the destination packet, first by proposition identity and, for dynamically generated proposition IDs, by exact canonical proposition text.

The harness fails closed if:

- a destination scene has no semantically comparable source decision and no explicit reviewed override;
- required knowledge is absent from the destination packet;
- a transferred or override action fails normal engine validation;
- simulation time cannot progress.

### Repeated minor-illness exception

RNG seeds can produce more `minor_illness` episodes for one actor than the accepted source seed. After that actor's accepted source templates are exhausted, the latest same-actor accepted minor-illness response may be reused. If the destination run has an explicit reviewed illness override for that actor, later repeated episodes may reuse the latest **earlier** override. Future overrides never apply retroactively.

The normal action validator remains authoritative. A repeated response can therefore become invalid when destination resources or state differ; that failure is evidence, not something the harness silently repairs.

## Explicit seed overrides

`runs/VALIDATION_SEED1702_OVERRIDES.json` contains reviewed fresh decisions for situations that the source policy cannot legitimately cover. Overrides must be grounded in the destination actor's sealed packet and must still pass the normal validator.

They are validation decisions, not additions to the canonical seed-1701 history.

## Paired counterfactuals

`scripts/paired_harbor_progression_validation.py` restores the same pre-decision state and runs two declared branches. The tested outcome may differ, but unrelated structural invariants must remain true.

The v016 harbor pair changes only P12's response to P11's work-specialization request:

- accept branch: porter ends, `harbor_coordinator` begins, sailor remains;
- refuse branch: porter+sailor remain unchanged.

Both branches must preserve P11's `free_laborer` legal status, H-HARBOR senior membership, material non-negativity, and zero rejected/pending/open cognition state.

## Interpretation boundary

A second seed with semantic policy transfer tests robustness to stochastic history while approximately holding decision policy constant. It does **not** measure human or model behavior frequency. Fresh cognition on selected paired situations is still required before making claims about cognition-run stability.

Two seeds are never a historical population sample.

## Fresh-cognition paired evaluation

From v017, `scripts/build_fresh_cognition_pairs.py` creates disposable branches from accepted state and seals paired cognition packets that differ in one declared control variable. `scripts/apply_fresh_cognition_pairs.py` then applies reviewed **fresh cognition decisions** from `runs/VALIDATION_V017_FRESH_PAIR_DECISIONS.json` through the normal action validator.

Fresh cognition here means the decision was produced anew from the sealed validation packet; it was not copied or semantically transferred from the canonical decision history. The decisions remain validation evidence only and do not enter canonical seed-1701 history.

The v017 pairs control:

- P10 minor illness: adequate vs nearly depleted household ritual goods;
- P7 recycling: buffered vs nearly exhausted finished-metalwork stock;
- P16 continuing care: no competing duty vs an explicit same-day recovery-rest obligation;
- P16 property stewardship: enough vs insufficient liquid silver to fund the already-negotiated reserve;
- P3 shipping information: one unconfirmed report vs two delivered discordant reports.

Each pair keeps the actor/personality and unrelated state fixed as far as the fixture permits. The changed input must be visible in the sealed packet. Every proposed action must pass the same engine validator used by canonical cognition. A branch is discarded after its packet/result evidence is frozen; validation SQLite files are never promoted to canonical state.

The purpose is causal sensitivity, not answer matching. A useful result is a valid, socially coherent action that changes for a reason supported by the controlled packet difference. Exact choice identity is not required and choice frequency is never interpreted as historical probability.

### Repeated fresh cognition

A single fresh decision per packet does not measure model instability. The next validation layer should rerun a selected subset of the **same sealed packets** across several independent cognition attempts, preserving packet bytes and validation rules, then compare:

- action validity;
- sensitivity to the controlled factor;
- unsupported factual invention;
- persona/goal continuity;
- relationship/obligation continuity;
- variance in action family and stated rationale.

Repeated-run frequencies remain model-behavior diagnostics only, never estimates of Bronze Age human behavior.

## Repeated same-packet fresh cognition

From v018, `scripts/repeated_fresh_cognition_validation.py` rebuilds selected v017 packet fixtures and applies several independently authored fresh cognition attempts to byte-identical sealed packets. Each attempt runs on its own disposable branch and must pass the ordinary engine validator.

The v018 subset uses six packets, three attempts each (18 decisions total):

- P10 minor illness with adequate ritual stock;
- P10 minor illness with depleted ritual stock;
- P7 recycling with buffered finished output;
- P7 recycling with near-exhausted finished output;
- P3 with one unconfirmed shipping report;
- P3 with two discordant delivered reports.

The diagnostic asks whether controlled-factor effects are stronger than within-packet answer variance. Stable action family is useful but not mandatory when more than one action is causally and epistemically defensible. In particular, asking for clarification and waiting are both acceptable conservative responses to unresolved contradictory reports if neither invents a shipment outcome.

All repeated-choice frequencies are **model-configuration diagnostics only**. They are not historical probabilities, population estimates, or evidence that Bronze Age people would choose an action at the observed rate.
