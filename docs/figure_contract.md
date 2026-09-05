# Figure contract

## Figure 1 - controlled navigation benchmark

- **Core conclusion:** Adding explicit structured eligibility and local-access
  gates removes the controlled false positives left by keyword retrieval and
  partial filtering.
- **Archetype:** quantitative grid with a dominant performance panel.
- **Backend:** Python / matplotlib only.
- **Final size:** 180 mm wide; editable SVG and PDF plus 300 dpi PNG.
- **Panel a:** balanced accuracy with 2,000-sample bootstrap 95% intervals.
- **Panel b:** false-positive and false-negative rates.
- **Evidence:** 477 synthetic, auditable cases derived from real registry fields.
- **Reviewer risk:** this is a software-correctness benchmark, not clinical
  validation. A perfect score must not be described as diagnostic accuracy.

## Figure 2 - trial landscape and ranking robustness

- **Core conclusion:** Cognitive-health trials in the snapshot are
  geographically concentrated, while Monte Carlo weighting identifies which
  top-ranked navigation options remain stable under preference uncertainty.
- **Archetype:** asymmetric quantitative grid.
- **Backend:** Python / matplotlib only.
- **Final size:** 180 mm wide; editable SVG and PDF plus 300 dpi PNG.
- **Panel a:** leading countries by number of registered trials.
- **Panel b:** registry status distribution.
- **Panel c:** top-10 selection probability by base rank in a lower-coverage
  access stress scenario (Brazil).
- **Panel d:** location reporting, multi-country representation and top-country share.
- **Evidence:** a paginated snapshot of all currently open matching public trial
  registrations and 2,000 Monte Carlo draws.
- **Reviewer risk:** country counts represent registered trial presence, not
  participants, sites, population need or treatment effectiveness.
