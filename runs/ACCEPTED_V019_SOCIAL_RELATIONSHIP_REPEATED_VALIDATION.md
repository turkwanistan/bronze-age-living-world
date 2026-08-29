# ACCEPTED V019 — Social/Relationship Repeated Fresh-Cognition Validation

v019 is validation-only. Canonical simulation remains accepted v015 day 462.

## Method

`scripts/social_repeated_fresh_cognition_validation.py` rebuilds six sealed packet groups and applies three independently authored fresh decisions to each group on separate disposable branches (18 attempts total).

Four packet groups reuse accepted v017 controls for continuing care and property stewardship. The fifth/sixth form a new Yabninu workshop-request pair reconstructed from accepted v008 state immediately before the day-308 scarcity refusal. The P3/P7 relationship history, six fulfilled reciprocal returns, request size (0.12 metal), actor traits/goals and scene remain fixed; only H-MERCH raw-metal reserve changes from 0.60 to 0.15.

## Results

All 18 fresh decisions validate with zero rejected branch jobs and zero negative resources. Packet hashes are identical within each three-attempt group.

- P16 care/no conflict: `fulfill_kin_care` 3/3.
- P16 care/recovery conflict: `defer_kin_care` 3/3.
- P16 stewardship/funded: `accept_property_stewardship` 3/3.
- P16 stewardship/underfunded: `decline_property_stewardship` 3/3.
- P3 workshop request/0.60 metal: `transfer_resource` 3/3.
- P3 workshop request/last 0.15 metal: `refuse_proposal` 3/3.

## Relationship and obligation consequences

The repeated outcomes remain structurally coherent:

- care fulfillment/deferment leaves the continuing-care obligation active;
- funded property consent creates the 0.40 maintenance reserve and active stewardship obligation;
- underfunded consent creates neither reserve nor stewardship obligation;
- abundant P3 branches transfer exactly 0.12 metal, retain 0.48, create one reciprocal-exchange obligation and preserve the `exchange_contact` relationship;
- scarce P3 branches preserve all 0.15 metal, create no reciprocal obligation, preserve the `exchange_contact` relationship, and apply only the modeled refusal strain (trust -0.02, conflicts +1, respect unchanged).

The P3 result is the strongest v019 control: identical strong repayment/trust history produces assistance when household reserve is adequate and refusal when the same request would nearly exhaust the supplier. Reciprocity matters, but it is not scripted into unconditional generosity.

## Reproducibility

- frozen decisions: `runs/VALIDATION_V019_SOCIAL_REPEATED_DECISIONS.json`
- frozen results: `runs/VALIDATION_V019_SOCIAL_REPEATED_RESULTS.json`
- harness: `scripts/social_repeated_fresh_cognition_validation.py`
- regression: `tests/test_v019_social_repeated_fresh_cognition.py`

No v019 SQLite branch is canonical or committed.

## Interpretation

Three attempts per packet are model diagnostics, not historical frequencies. The result supports relationship/obligation continuity under changing constraints; it does not estimate how often a Bronze Age merchant or household member would choose any action.

Next validation should focus on **repair/reconciliation and negotiated compromise after disagreement**, because current repeated tests show stable refusal/fulfillment boundaries more clearly than post-conflict relationship recovery.
