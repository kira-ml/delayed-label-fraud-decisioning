# Evaluation Protocol

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Evaluation Protocol  
> **Status:** v1.0 — first-principles revision; decision-centric evaluation  
> **Last updated:** 2026-09-24

---

## 0. Derivation From Problem Framing

This protocol is derived from `docs/problem_framing.md` §5 and §10. It does
not introduce any metric, split, or claim that is not required by the
problem decomposition stated there.

**Rule:** If a metric, baseline, or procedure in this document cannot be
traced to a sentence in `problem_framing.md`, it is either wrong or the
framing is incomplete. Both are defects. Fix the framing first.

**Rule:** If a result is not produced by this protocol, it does not go in
the report. There is no post-hoc metric.

This revision replaces v0.4, which evaluated a classification task
(macro F1) and a decision task (cost) as two separate layers. That
separation was inherited from course deliverables, not from the problem. It
is reversed here. There is **one** evaluation: the policy's realized cost
on a temporal backtest, with classification metrics as supporting evidence.

---

## 1. Purpose

This document defines, before any model is trained, **how the project
decides whether the system works**.

It exists to prevent:

- Selecting a classifier by a metric that is not the objective
- Measuring the policy on a split that leaks future information
- Reporting AUC or F1 as if it were the success criterion
- Deploying an uncalibrated probability into a cost-sensitive decision
- Claiming an improvement inside the noise band
- Omitting censored labels from the reported evaluation

**Primary objective (from `problem_framing.md` §5):**

```text
minimize realized cost per transaction
    over the test window,
    under a frozen cost matrix,
    a 1-month delay regime,
    and a chronological split.
```

Every metric, baseline, and procedure in this document serves that
objective or is explicitly labeled as supporting evidence.

---

## 2. Core Evaluation Question

> Given a calibrated P(fraud) from a traditional classifier, and a frozen
> cost matrix, does an expected-cost-minimizing decision policy produce
> **lower realized cost per transaction** than every canonical baseline on
> the test window — and does the advantage survive a 2× sensitivity sweep
> on every cost parameter?

This is a single question. It is not split into a "classification question"
and a "decision question."

---

## 3. Evaluation Principles

These principles are inherited directly from the problem framing and apply
to every experiment in the project. They are not scoped to a "layer."

1. **Temporal only.** No random splits. No shuffling. No K-fold CV that
   mixes time boundaries.
2. **Delay-aware.** A label may only be used after `label_time`. Unobserved
   labels are censored, never treated as negative.
3. **Cost-based.** Every decision is scored by realized cost under the
   frozen cost matrix. Classification metrics are supporting evidence.
4. **Calibrated.** A classifier is only admissible as a policy input if its
   ECE is below the gate in §7, or a documented calibration step brings it
   below the gate.
5. **Baseline-anchored.** Every improvement is measured against the
   **strongest** canonical baseline, not the weakest.
6. **Pre-registered.** The cost matrix, the split, the baselines, and the
   primary metric are fixed before modeling and do not change.
7. **Noise-aware.** Claims of improvement are only made when the 95%
   bootstrap CI on the cost advantage excludes zero.
8. **Reproducible.** Fixed seeds, documented library versions, one command
   reproduces the pipeline.
9. **Honest.** Failures, non-findings, and limitations are reported, not
   hidden.

If any of these principles is violated, the corresponding result is
discarded. It is not reported with a caveat.

---

## 4. The Single Chronological Split

There is one split for the entire project. It is the split in
`problem_framing.md` §8.3 and `docs/data_card.md` §5.

| Split | Months | Rows | Fraud rate | Purpose |
|---|---|---:|---:|---|
| Train | 0, 1, 2 | 397,039 | ~1.10% | Fit classifier and preprocessing |
| Validation | 3, 4 | 278,627 | 1.0207% | Calibration gate, hyperparameter selection |
| Test | 5, 6 | 227,491 | 1.2576% | Policy evaluation, backtest |
| Censored | 7 | 96,843 | — | Excluded from training and evaluation |
| **Observed total** | | **903,157** | | |

**Delay regime:** 1 month. `decision_time = month`, `label_time = month + 1`.
A label is observed iff `label_time <= 7`.

**Rules:**

- No shuffling. Ever.
- No stratification that breaks time order.
- Preprocessing is fit on the training months only.
- The test window is touched exactly once, after model and policy are
  frozen.
- Censored rows are excluded from training and evaluation. Their count is
  reported in every results table.
- An assertion in `src/data/split.py` verifies
  `train + val + test == observed`.

**Why not an 80/20 split:** the 80/20 split in the earlier protocol was
selected to satisfy a course phrasing. It is not required by the problem.
The three-way split above is required, because the validation window is
where the calibration gate and hyperparameter selection happen, and the
test window is where the policy is evaluated. Collapsing validation into
training would either leak the calibration gate into the test window or
force calibration to be evaluated on training data.

---

## 5. Classifiers Under Comparison

Three traditional classifiers are compared. This is a **methodology step**,
not the research question. The purpose is to select the classifier that
produces the best policy input.

| # | Classifier | Role | Class imbalance handling |
|---|---|---|---|
| 1 | Logistic Regression | Linear baseline; interpretable | **None** — calibration must be preserved |
| 2 | Random Forest | Non-linear ensemble; robust | **None** — calibration must be preserved |
| 3 | LightGBM | Gradient boosting; strong tabular | **None** — calibration must be preserved |

**Rule:** Any weighting that distorts calibrated probabilities is rejected.
The policy depends on `p` being a real probability, not a reweighted score.
If a weighting improves ranking but worsens ECE, the weighting is dropped.

**Prohibited:** neural networks, deep learning, CNNs, RNNs, transformers,
LLMs, pretrained foundation models, AutoML.

**Rule:** Hyperparameter variants of the same algorithm do not count as
distinct algorithms.

---

## 6. Preprocessing

Preprocessing is fit **within each training window only**. The same fitted
pipeline is applied unchanged to validation and test.

| Step | Logistic Regression | Random Forest | LightGBM |
|---|---|---|---|
| Missing values | Handled per column | Handled per column | Handled per column |
| Categorical encoding | One-hot | Ordinal | Native categorical |
| Numeric scaling | StandardScaler | None | None |
| Feature selection | All features | All features | All features |

**Feature exclusion list** (enforced in `src/common.py`):

- `transaction_id` — identifier
- `month` — used for splits only
- `fraud_bool` — target
- `label_month`, `observed` — derived from the delay simulation
- `amount_proxy`, `proposed_credit_limit` — reserved as cost inputs
- `device_fraud_count` — may include post-decision information

**Rule:** Any deviation from this table or this exclusion list is documented
in `docs/data_card.md` and justified before it is applied.

---

## 7. Calibration Gate

The decision policy assumes `p` is a probability. An uncalibrated score
produces wrong expected costs and therefore wrong decisions.

**Gate:** ECE (10 quantile bins) < 0.05 on the validation window.

**Procedure:**

1. Train each classifier on the training window.
2. Score the validation window.
3. Compute Brier and ECE per classifier.
4. **If ECE < 0.05 for all three classifiers:** proceed. No calibration
   step is applied.
5. **If any classifier has ECE ≥ 0.05:** apply exactly one calibration
   method (Platt scaling or isotonic regression), fit on validation only.
   Re-compute ECE. If ECE drops below 0.05, the classifier remains
   admissible. If not, the classifier is rejected as a policy input.
6. Report the ECE and Brier for every classifier, whether or not a
   calibration step was applied.

**Rule:** Only one calibration method is attempted per classifier. Chaining
methods is out of scope.

**Rule:** Calibration is fit on validation data, never on the test window.

---

## 8. Hyperparameter Selection

Hyperparameter selection is by **validation realized cost after the
policy**, not by validation macro F1.

**Procedure:**

1. Define a small, documented grid per classifier.
2. For each configuration, train on the training window.
3. Score the validation window.
4. Feed the scores into the decision policy.
5. Compute realized cost per transaction on the validation window.
6. Select the configuration with the lowest realized cost per transaction.
7. Ties are broken by: (a) calibration quality (lower ECE), (b) inference
   speed, (c) interpretability.

**Rule:** The grid is small enough that the selection is reproducible and
the comparison is fair. Grid contents are documented in
`reports/model_comparison.md`.

**Rule:** Tuning never touches the test window.

**Rule:** Classification metrics (macro F1, ROC-AUC, per-class precision,
recall, F1) are recorded for every configuration as **supporting evidence**
and reported alongside the cost result. They do not decide the selection.

---

## 9. Decision Policy

### 9.1 Policy Under Evaluation

For each transaction:

```text
E[cost(approve)] = p * fraud_loss(amount)
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action* = argmin over {approve, review, block}
```

When `amount_scaled: true`, `fraud_loss(amount) = amount * fraud_loss_rate`.

The argmin rule is the source of truth. Thresholds derived from the cost
matrix are a diagnostic view for reporting; they are not the implementation.

### 9.2 Cost Matrix

Frozen in `configs/costs.yaml`. Values as implemented:

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: true
fraud_loss_rate: 0.0019187869
```

`fraud_loss_rate` is derived from **training-window** amounts only:
`1 / mean(amount_proxy on train)`. No test-window information is used.

The cost matrix does not change between runs unless the change is registered
as a separate experiment with its own reported result.

### 9.3 What Is Being Evaluated

The policy, not the raw score. A classifier with better ROC-AUC but worse
policy cost is a worse classifier **for this project**.

---

## 10. Primary Metric

**Realized cost per transaction** on the test window, under the frozen cost
matrix and the 1-month delay regime.

Realized cost is computed from matured labels only. Censored rows are
excluded and counted.

The primary comparison is:

```text
cost/txn(policy)
    vs.
cost/txn(strongest canonical baseline)
```

The advantage is reported as a percentage and as a 95% bootstrap confidence
interval. The CI must exclude zero for the advantage to count as a finding.

---

## 11. Supporting Metrics

Reported alongside the primary metric. They are evidence, not the claim.

### 11.1 Operational

| Metric | Definition |
|---|---|
| Cost per transaction | Mean realized cost (also reported per baseline) |
| Total cost | Sum of realized cost over the test window |
| Fraud dollars saved vs. approve-all | Fraud loss avoided |

### 11.2 Ranking

| Metric | Reported at |
|---|---|
| Precision@N | N ∈ {1%, 5%, 10%} |
| Recall@N | N ∈ {1%, 5%, 10%} |

Ranking metrics are computed on the scored test window as it stands. They
do not change the policy's actions.

### 11.3 Calibration

| Metric | Purpose |
|---|---|
| Brier score | Probability calibration |
| Expected calibration error (ECE) | Decision-relevant calibration |
| Reliability table (10 quantile bins) | Diagnostic |

### 11.4 Classification Context

Reported for all three classifiers, side by side:

| Metric | Purpose |
|---|---|
| Macro F1 | Balanced classification quality |
| Accuracy | Informational only |
| Per-class precision, recall, F1 | Error breakdown by class |
| Confusion matrix | Full error breakdown |
| ROC-AUC | Threshold-independent discrimination |

These metrics are reported so the paper can compare the classifiers as
classifiers as well as policy inputs. They are **not** the selection
criterion.

### 11.5 Data Integrity (Required in Every Table)

| Metric | Definition |
|---|---|
| Censored-label count | Rows with `label_time > 7` |
| Censored-label rate | Censored ÷ total |
| Evaluated fraction | 1 − censored-label rate |

A results table without these rows is invalid.

---

## 12. Baselines

Every baseline uses the same split, the same cost matrix, and the same
delay regime. No baseline is tuned on the test window.

| # | Baseline | Implementation |
|---|---|---|
| 1 | Random decision | Seeded `random.choice(['approve','review','block'])` |
| 2 | Approve-all | `action = 'approve'` for every row |
| 3 | Block-all | `action = 'block'` for every row |
| 4 | LR + static 0.5 | `block` if `p >= 0.5`, else `approve` |
| 5 | RF + static 0.5 | `block` if `p >= 0.5`, else `approve` |
| 6 | LGBM + static 0.5 | `block` if `p >= 0.5`, else `approve` |
| 7 | **Cost-sensitive policy** | argmin of expected cost (system under test) |

The policy under test is compared against the **strongest** of baselines
1–6, not the weakest.

The three static-threshold baselines (4–6) are included so the comparison
shows that the policy advantage is not a byproduct of choosing the best
classifier, but of the decision rule itself.

---

## 13. Statistical Rigor

### 13.1 Noise Floor

All comparisons use a **95% bootstrap confidence interval** on the test
window for realized cost per transaction.

- Resamples: 1,000, with replacement
- Seed: `42`
- CI reported on: policy cost/txn, strongest-baseline cost/txn, advantage

### 13.2 Minimum Effect Size

An improvement counts as a finding only if:

1. The 95% bootstrap CI on the advantage excludes zero, **and**
2. The relative cost reduction exceeds **5%**.

Below either threshold, the result is reported as a non-finding.

### 13.3 Reproducibility as Evidence

The pipeline reproduces byte-for-byte from one command. Model output, action
distribution, and backtest cost are identical across runs. This is
documented in the reproducibility section and reported as evidence that
the result is not seed-dependent.

### 13.4 Documented Seeds and Versions

- `seed = 42` for training
- `SEED = 42` for the random baseline
- Library versions recorded in `requirements.txt` and reported in the paper

---

## 14. Sensitivity Analysis

The protocol requires varying each cost parameter over a 2× range and
re-running the backtest. The conclusion of the project is only valid if the
policy advantage survives this sweep.

| Parameter | Range tested | Status |
|---|---|---|
| `false_positive_cost` | 2× range | Run |
| `review_cost` | 2× range | Run |
| `residual_fraud_loss` | 2× range | Run |
| `fraud_loss` | constant vs. amount-scaled | Run; amount-scaled adopted |

**Rule:** A finding that reverses inside any 2× sweep is reported as a
non-finding for the affected regime, not quietly dropped.

**Rule:** The minimum advantage across the entire sweep is reported in the
paper, not just the nominal-case advantage.

---

## 15. Forbidden Practices

- Random splits on temporal data
- K-fold CV that mixes time boundaries
- Test-window tuning of any kind (hyperparameters, thresholds, features,
  calibration)
- Treating censored labels as negatives
- Reporting macro F1, ROC-AUC, or accuracy as the primary success criterion
- Deploying a classifier that failed the calibration gate without a
  documented calibration step
- Counting hyperparameter variants as distinct algorithms
- Using neural networks, deep learning, transformers, LLMs, or AutoML
- Reporting a non-finding as a finding, or vice versa

---

## 16. Reporting Format

Every reported experiment follows this format. The primary report is
`reports/model_comparison.md`.

```markdown
# Experiment: <name>

## Setup
- Dataset: BAF Base.csv
- Delay regime: 1 month
- Splits: train 0-2 / val 3-4 / test 5-6 / censored 7
- Cost matrix: configs/costs.yaml (hash)
- Policy: argmin of expected cost
- Calibration gate: ECE < 0.05

## Data Integrity
- Censored-label count:
- Censored-label rate:
- Evaluated fraction:

## Classifier Comparison (supporting)
| Classifier | Macro F1 | ROC-AUC | Precision (fraud) | Recall (fraud) | ECE | Brier |

## Policy Comparison (primary)
| Policy / Baseline | Cost/txn | 95% CI | Fraud $ saved | Precision@1% | Recall@1% |
| Random | | | | | |
| Approve-all | | | | | |
| Block-all | | | | | |
| LR + static 0.5 | | | | | |
| RF + static 0.5 | | | | | |
| LGBM + static 0.5 | | | | | |
| Cost-sensitive policy | | | | | |

## Comparison
- Strongest baseline:
- Policy advantage (%):
- 95% bootstrap CI on advantage:
- Excludes zero: yes / no

## Sensitivity
- Minimum advantage across 2× sweep:
- Parameters that reverse the finding:

## Failure Cases
- Dominant error type:
- Why:

## Conclusion
- Success stop / null stop / blocked stop:
```

**Rule:** A report is invalid without: (a) the censored-label count, (b) the
bootstrap CI on the advantage, (c) the sensitivity sweep minimum, (d) the
failure section, and (e) the stop verdict.

---

## 17. Stop Criteria

Every phase ends with exactly one of four verdicts. The verdict is recorded
in the report.

- **Success stop.** The improvement exceeds the effect size and the CI
  excludes zero. Adopt the change.
- **Null stop.** The improvement is inside the noise band or below the
  effect size. Report as a non-finding. Do not adopt.
- **Blocked stop.** A prerequisite is missing. Do not proceed. Diagnose.
- **Scope stop.** The phase is out of scope for this submission.

### 17.1 Per-Phase Criteria

| Phase | Success stop | Null stop |
|---|---|---|
| Calibration gate | ECE < 0.05 without a calibration step | ECE stays ≥ 0.05 after one calibration method → reject the classifier |
| Classifier selection | A classifier produces lower validation cost after the policy, CI excludes zero | All three classifiers are within the noise band → select the simplest and most interpretable; report as non-finding |
| Policy advantage | Policy cost/txn < strongest baseline cost/txn, CI excludes zero, ≥ 5% relative reduction | Policy does not beat the strongest baseline → report the null result; investigate before adding complexity |
| Sensitivity sweep | Advantage remains ≥ 5% across the 2× range | Advantage reverses inside the range → report the regime where it reverses; do not claim a general finding |
| Amount scaling | ≥ 2% decision flips OR ≥ 1% relative change in cost/txn | Below both thresholds → keep constant loss, report as non-finding |

### 17.2 Overall Stop

The project stops when:

- All phases have a recorded verdict.
- The calibration gate is passed or a classifier is rejected with a
  documented reason.
- The policy advantage is either a finding or a reported non-finding.
- The sensitivity sweep minimum is reported.
- No measured failure remains that is not explicitly listed as future work.

If a phase keeps iterating without moving between verdicts, it is not
following this protocol.

---

## 18. Reproducibility Requirements

- Fixed random seeds (42) for training and (42) for the random baseline
- Fixed chronological split defined in `src/data/split.py` and documented
  in `docs/data_card.md` §5
- Fixed expanding-window folds on the training window
- Frozen cost matrix in `configs/costs.yaml`
- Environment pinned in `requirements.txt`
- One command reproduces the full pipeline

**Documented deviations:**

- Splits are hardcoded in `src/data/split.py` rather than read from a
  `configs/splits.yaml`. Documented in `docs/data_card.md`.
- The action log does not carry a `cost_config_hash`. With one frozen cost
  matrix in use, there is nothing to disambiguate. Add it when a second
  cost matrix is introduced.

---

## 19. Definition of Done

### 19.1 Framing

- [x] Protocol derived from `problem_framing.md` §5 and §10
- [x] Single chronological split adopted
- [x] Realized cost per transaction promoted to primary metric
- [x] Classification metrics demoted to supporting evidence
- [x] Calibration gate made mandatory

### 19.2 Execution (tracked in the roadmap)

- [ ] Cost matrix frozen in `configs/costs.yaml`
- [ ] Delay regime (1 month) implemented; censored counts reported
- [ ] Chronological split (0-2 / 3-4 / 5-6 / censored 7) implemented
- [ ] Three classifiers trained under identical conditions
- [ ] Calibration gate (ECE < 0.05) run per classifier
- [ ] Hyperparameter grids documented per classifier
- [ ] Selection performed on validation realized cost after the policy
- [ ] Test window evaluated once, after model and policy are frozen
- [ ] Primary report written with the required sections (§16)
- [ ] Bootstrap CIs computed on the test window
- [ ] Sensitivity sweep over 4 cost parameters run
- [ ] Stop verdict recorded for every phase
- [ ] Results reproducible from one command

---

## 20. Guiding Rules

> The evaluation is of the **policy**, not the classifier. A classifier is
> better if and only if the policy it feeds produces lower realized cost.

> Three classifiers are only comparable if they use the same split, the
> same preprocessing, the same folds, and the same cost criterion. Any
> deviation is documented and justified.

> The test window is used **once**. Any result that touches it before model
> and policy are frozen is invalid.

> A claim is only a finding if its 95% bootstrap CI on the cost advantage
> excludes zero and the relative reduction exceeds 5%. Everything else is a
> non-finding, reported as such.

---

## 21. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | v0.4 — restructured into primary classification and supplementary policy layers | Align with course deliverables |
| 2026-09-24 | v1.0 — first-principles revision; two-layer architecture removed; primary metric changed to realized cost; macro F1 demoted to supporting evidence; calibration promoted to a mandatory gate; single chronological split adopted; stop criteria restated in cost terms | Derive the protocol from `problem_framing.md` v1.0, per the professor's confirmed autonomy |
