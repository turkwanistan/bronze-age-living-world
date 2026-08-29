# STATUS

**Checkpoint:** accepted strict Ugarit v015 adult harbor-work specialization gate at day 462.

## Authority

- `bronze-age-simulation-encyclopedia.md` SHA-256 `a57ac7e2b1d1b89e8a041d982f0a3b3c59d175a1792df051958e81206997f937`.
- `plan.md` SHA-256 `f4bf0d497c7beceec5b9bdb1bf1425e5b890d377e9dc3c1fbc54a2189c36a54d`.
- Repository state, tests, evidence mappings, canonical SQLite and acceptance manifests govern implementation beneath those authorities.

## Accepted strict runtime

Canonical DB: `state/ugarit_living_v015.sqlite`; v002-v014 are immutable prior accepted histories.

- run `RUN-3dda7920595c1748`, seed `1701`
- scenario `0.13.0`, schema `3`
- accepted day **462**
- state hash `a15e3ec7a0ae8ada835b3920acb370855e1443977abd7849040a336cf8b0e2f0`
- **6,608 events**
- **157 accepted cognition / 0 rejected / 0 pending / 0 open scenes**
- **83/83 tests**
- exact replay: **157 decisions / 0 new cognition / exact hash**
- zero negative stocks, false shortfalls or overdue scheduled obligations

Acceptance manifest: `runs/ACCEPTED_DAY462_V015_HARBOR_LIFE_COURSE.md`.

## v015 result

Abdi-Rashap (P11) now demonstrates a second independent life-course mechanism, distinct from Niqmepa's apprenticeship progression and from marriage.

By day 460 P11 has accumulated **65 recurring occupation cycles** and has twice acted as a provenance-preserving harbor information/report bridge. He requests that the H-HARBOR household recognize a revised division of labor: routine porter work should give way to **harbor coordination**, while sailor work continues. Dagan-beli (P12), the household manager/market trader, independently reviews and accepts.

Canonical consequences are deliberately narrow:

- P11's `porter` role ends at day 460;
- `harbor_coordinator` begins at day 460;
- `sailor` remains active;
- legal status remains `free_laborer`;
- H-HARBOR membership remains `senior`, unchanged from day 0;
- no new legal office, household formation, patronage tie or state promotion is inferred.

The change is behaviorally causal rather than label-only. On the next weekly occupation boundary, day 462, P11's work cycle contains `harbor_coordinator` activity (cargo/porter coordination, harbor information brokerage and voyage-work allocation) plus continuing sailor work; routine porter activity is absent.

An independent regression proves P12 can refuse the progression with no role, legal-status or household change. The same day also contains an unrelated minor illness for Talmiyanu, handled conservatively, and Yabninu again waits rather than violate the H-MERCH 16.5-silver reserve floor. The new life-course path therefore does not override older household constraints.

## Current limitations / next priorities

- `harbor_coordinator`, the 60-cycle threshold, P11/P12 pairing and review procedure are engineering fixtures, not a reconstructed Ugaritic title or promotion rule.
- The simulation now has two distinct state-based life-course paths, but frequency from one seed must not be treated as historically meaningful.
- **Highest-value next milestone: second-seed / paired-counterfactual validation.** Compare mechanism activation, invariants, containment and failure modes across another deterministic seed; do not require identical stochastic scenes or decision identity.
- Pair at least one mechanism-level counterfactual where a fixture parameter or response branch changes while structural invariants must remain true.
- H-WIDOW's 0.40 property-maintenance reserve remains earmarked and unspent; no succession/inheritance transfer is modeled.
- P12 market availability may recover only through new information, not automatic reset.
- Language/scribal constraints should be added only when a real multi-party transaction requires them.

**The world is structured. The people are not scripted.**
