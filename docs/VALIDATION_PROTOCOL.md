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
