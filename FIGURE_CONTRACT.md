# Figure contract

## Core conclusion

Prompt strategy changes task performance and confidence reliability in task-specific ways, while error concentration, support gaps, uncertainty, and prompt disagreement identify concrete data-operation priorities.

## Design

- Archetype: quantitative grid.
- Target: public technical report and interview portfolio.
- Backend: Python / matplotlib only.
- Final width: 183 mm equivalent (7.2 in).
- Minimum font size: 5 pt; editable SVG and TrueType PDF text.

## Panel map

- Figure 1a-b: accuracy and Macro-F1 with item-bootstrap 95% CIs.
- Figure 1c: paired accuracy changes with paired-bootstrap 95% CIs.
- Figure 1d: ECE and multiclass Brier score.
- Figure 2a-c: row-normalized confusion structure for the rubric prompt.
- Figure 3a: highest-priority task-label slices.
- Figure 3b: error versus uncertainty, with item support encoded by marker area.

## Statistical contract

- `n` is the number of independent benchmark items.
- The same items are evaluated under both prompts; between-prompt comparisons are paired.
- Confidence intervals use 2,000 percentile bootstrap resamples of items.
- McNemar tests are exact and two-sided; three task-level tests use Benjamini-Hochberg correction.
- No random-generation uncertainty is shown because forced-choice inference is deterministic.

## Reviewer risks

- Public-benchmark contamination may inflate apparent performance.
- Item-bootstrap intervals do not cover checkpoint or model-family uncertainty.
- The data-priority score is a transparent operational heuristic, not a validated medical-risk score.
