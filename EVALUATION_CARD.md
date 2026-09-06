# Evaluation Card

## Intended use

MedEval-DataOps is a portfolio-grade, reproducible evaluation of constrained Chinese medical-search language-understanding tasks. It is intended to demonstrate benchmark design, model evaluation, statistical analysis, error diagnosis, and data-priority planning.

It is not intended for diagnosis, treatment recommendation, patient triage, or clinical deployment.

## Evaluation unit and sample

- Independent evaluation unit: one PromptCBLUE validation item.
- Tasks: KUAKE-QIC (440), KUAKE-QQR (400), KUAKE-QTR (400).
- Total unique items: 1,240.
- Repeated condition: every item is evaluated under both prompt strategies.
- Raw text policy: source text is downloaded locally and excluded from Git; public outputs use IDs, labels, metadata, and hashes.

## Model and inference

- Model: `Qwen/Qwen3-0.6B`.
- Inference: deterministic forced choice.
- Choice score: mean conditional log-probability across the tokens of each allowed label.
- KUAKE-QIC choice policy: row-level candidates plus PromptCBLUE's documented implicit `非上述类型` reject option.
- KUAKE-QIC alias policy: canonicalize upstream `疾病表述` to the PromptCBLUE evaluator vocabulary `疾病描述`.
- Prediction: allowed label with the highest normalized score.
- Confidence: softmax of the per-choice scores; this is an evaluation proxy, not a clinically calibrated probability.
- Prompt strategies: a minimal direct instruction and a task-specific rubric instruction.

## Metrics

- Accuracy: fraction of exact label matches.
- Macro-F1: unweighted mean of label-level F1 scores.
- Balanced accuracy: unweighted mean recall across observed labels.
- ECE-10: expected calibration error using ten equal-width bins.
- Multiclass Brier score: sum of squared probability error across allowed choices, averaged over items.
- Prompt disagreement: fraction of items receiving different predictions across the two prompt strategies.

## Statistical analysis

- 95% confidence intervals use 2,000 percentile bootstrap resamples of evaluation items.
- Strategy comparisons are paired because both strategies evaluate the same items.
- Task-level changes use two-sided exact McNemar tests on discordant correctness outcomes.
- Three task-level p values are adjusted with the Benjamini-Hochberg procedure.
- The confidence intervals quantify item-sampling uncertainty. They do not include model-training, checkpoint, hardware, or stochastic decoding variation.

## Data-priority heuristic

The operational priority score is:

```text
0.45 × rubric-prompt error rate
+ 0.20 × within-task support gap
+ 0.20 × normalized predictive entropy
+ 0.15 × prompt disagreement rate
```

This score is an explicit triage heuristic for annotation planning, not an optimized objective and not a medical risk score.

## Known limitations

- Public benchmarks may overlap with model training data.
- The selected tasks evaluate query understanding and relevance, not long-form consultation quality or clinical reasoning.
- Labels inherit the upstream annotation policy; this project does not perform independent clinician adjudication.
- One small open model is evaluated; results do not establish rankings across model families.
- Forced-choice likelihood is reproducible but differs from an unconstrained production chat interface.
- Regex-based privacy screening cannot prove de-identification.
