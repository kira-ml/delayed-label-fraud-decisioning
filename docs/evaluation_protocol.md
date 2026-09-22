# Evaluation Protocol

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Evaluation Protocol  
> **Status:** v0.4 — restructured around three-algorithm comparison with supplementary cost-sensitive analysis  
> **Last updated:** 2026-09-22

---

## 1. Purpose

This document defines how the project is evaluated **before** any model is
trained.

It exists to prevent:

- Cherry-picking metrics after seeing results
- Using random splits that leak future information
- Reporting AUC without context
- Comparing models under different preprocessing or folds
- Claiming success without a fair, reproducible comparison
- Ignoring the operational cost of false positives and false negatives

**Rule:** If a result is not produced by this protocol, it does not go in the
report.

The protocol has two layers:

1. **Primary — three-algorithm classification comparison.** The course
   requirement. Compare Logistic Regression, Random Forest, and LightGBM
   under identical data, preprocessing, folds, and primary metric.
2. **Supplementary — cost-sensitive decision policy.** A project-depth
   extension that maps the classification output to an operational
   `approve` / `review` / `block` decision under delayed labels.

---

## 2. Core Evaluation Questions

### 2.1 Primary

> Which of three traditional machine learning algorithms performs best at
> predicting `fraud_bool` under a fair, reproducible experimental design, and
> which should be deployed?

The primary metric is **Macro F1**, chosen because the class distribution is
heavily imbalanced (~1.1% fraud) and because both false positives and false
negatives carry real operational cost.

### 2.2 Supplementary

> Given the best classifier's predicted probability, how much operational
> utility does a cost-sensitive decision policy create compared to realistic
> baselines under delayed and censored labels?

Utility is not accuracy. Utility is not AUC. Utility is:

```text
utility = fraud loss avoided
        − false-positive cost
        − review cost
```

---

## 3. Evaluation Principles

### 3.1 Primary Principles

1. **Same data split.** All three algorithms use the identical train/test
   split.
2. **Same preprocessing logic.** Missing-value handling, encoding, scaling,
   and feature selection are identical across algorithms except where the
   algorithm's mathematical requirements differ (e.g. Logistic Regression
   requires scaling; tree models do not). Any difference is documented.
3. **Same cross-validation strategy.** 5-fold time-series CV on the training
   data, identical folds for all three algorithms.
4. **Same primary metric.** Macro F1, reported with mean and variability
   across folds.
5. **Test set untouched until final evaluation.** No model selection,
   threshold tuning, or feature decisions on the test set.
6. **Reproducible.** Fixed seeds, documented library versions.
7. **Honest.** Report failures, per-class errors, and limitations.

### 3.2 Supplementary Principles

1. **Temporal only.** No random splits. No shuffling.
2. **Delay-aware.** A label may only be used after `label_time`.
3. **Cost-based.** Every decision is scored by realized cost.
4. **Baseline-anchored.** Every improvement must beat a named baseline.
5. **Pre-registered.** Metrics and cost matrix fixed before modeling.

If any of these principles is violated, the corresponding result is discarded.

---

## 4. Primary Evaluation — Three-Algorithm Classification

This is the course-required comparison. All content in this section applies
to the primary deliverable.

### 4.1 Dataset and Split

| Property | Value |
|---|---|
| Dataset | Bank Account Fraud (BAF) `Base.csv` |
| Rows | 1,000,000 |
| Target | `fraud_bool` (binary) |
| Train split | Months 0–5 (~80%) |
| Test split | Months 6–7 (~20%) |
| Split type | Chronological (justified alternative to random 80/20) |
| Cross-validation | 5-fold time-series CV on training data |

The chronological split is used instead of a random 80/20 split because the
course explicitly requires chronological splits for time-ordered data:

> "Time ordered data must use a chronological split rather than random
> shuffling."

Full split details are in `docs/data_card.md` §5.

### 4.2 Algorithms

Exactly three traditional algorithms are compared. All three are explicitly
permitted by the course.

| # | Algorithm | Role | Class imbalance handling |
|---|---|---|---|
| 1 | Logistic Regression | Linear baseline; interpretable | `class_weight='balanced'` |
| 2 | Random Forest | Non-linear ensemble; robust | `class_weight='balanced_subsample'` |
| 3 | LightGBM | Gradient boosting; strong tabular performance | `is_unbalance=True` |

**Prohibited algorithms** (explicitly disallowed by the course): neural
networks, deep learning, CNNs, RNNs, transformers, LLMs, pretrained
foundation models, AutoML-generated solutions.

**Rule:** Changing hyperparameters of the same algorithm does not count as a
different algorithm. The three algorithms above are distinct model families.

### 4.3 Preprocessing

Preprocessing is fit **within each cross-validation fold's training portion**
to prevent leakage. The same pipeline is applied to the test set at the end.

| Step | Logistic Regression | Random Forest | LightGBM |
|---|---|---|---|
| Missing values | Handled per column | Handled per column | Handled per column |
| Categorical encoding | One-hot | Ordinal | Native categorical |
| Numeric scaling | StandardScaler | None | None |
| Feature selection | All features | All features | All features |

Any deviation from this table must be documented and justified.

### 4.4 Hyperparameter Tuning

Each algorithm receives a small, documented grid search. Tuning is performed
**on training folds only**, using the same 5-fold time-series CV.

The grids are documented in `reports/model_comparison.md`. The following
rules apply:

- Grids are small (a handful of configurations per algorithm) to keep the
  comparison fair and reproducible.
- Tuning never touches the test set.
- The best configuration per algorithm is selected by mean Macro F1 across
  folds.
- The final model for each algorithm is retrained on the full training split
  with the selected configuration.

### 4.5 Primary Metric — Macro F1

**Why Macro F1:**

- The dataset is heavily imbalanced (~1.1% fraud).
- Raw accuracy is misleading: a model that predicts "not fraud" for every
  transaction achieves 98.9% accuracy while catching no fraud.
- Macro F1 treats both classes equally, so recall on the fraud class counts
  as much as precision on the non-fraud class.
- Both false positives (friction, revenue loss) and false negatives (fraud
  loss) carry real operational cost, so a metric that balances both is
  appropriate.

**Supporting metrics (reported for all three algorithms):**

- Accuracy (informational only)
- Per-class precision, recall, F1
- Confusion matrix
- ROC-AUC (informational)

### 4.6 Validation Protocol

| Step | Detail |
|---|---|
| Cross-validation | 5-fold, time-series, contiguous folds |
| Folds | Identical across all three algorithms |
| Primary metric | Mean Macro F1 across folds |
| Variability | Standard deviation of Macro F1 across folds |
| Reporting | Full table: mean and SD per algorithm |
| Model selection | Highest mean Macro F1, with interpretability, speed, and practical suitability as tiebreakers |

### 4.7 Final Test Evaluation

After model selection:

1. The selected model is retrained on the full training split with its best
   hyperparameters.
2. The test set is scored **once**.
3. The following are reported on the test set:
   - Primary metric: Macro F1
   - Supporting metrics: accuracy, per-class precision/recall/F1, confusion
     matrix, ROC-AUC
   - Interpretation: which errors dominate, and what they mean operationally
4. No further tuning is permitted after the test evaluation.

### 4.8 Forbidden Practices (Primary)

- Using the test set for model selection, threshold selection, or feature
  decisions
- Random splits on time-ordered data
- K-fold cross-validation that mixes time boundaries (e.g. random K-fold)
- Counting hyperparameter variants of one algorithm as different algorithms
- Using neural networks, deep learning, transformers, or LLMs
- AutoML-generated solutions
- Reporting accuracy as the sole success criterion

---

## 5. Supplementary Evaluation — Cost-Sensitive Decision Policy

This section applies to the supplementary analysis. It extends the primary
classification into an operational decision under a cost structure.

### 5.1 Cost Matrix

The cost matrix is fixed in `configs/costs.yaml` and must not change between
runs unless the change is documented as a separate experiment.

#### 5.1.1 Decision Outcomes

| Action | True label = fraud (y=1) | True label = legit (y=0) |
|---|---|---|
| approve | `fraud_loss` | `0` |
| review | `review_cost + residual_fraud_loss` | `review_cost` |
| block | `0` | `false_positive_cost` |

#### 5.1.2 Cost Values as Implemented

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: true
fraud_loss_rate: 0.0019187869
```

#### 5.1.3 Notes

- Costs are **relative units**. Absolute calibration is out of scope.
- `residual_fraud_loss` reflects that review does not catch all fraud.
- Amount scaling was tested and adopted. Under constant `fraud_loss`, the
  policy's advantage over the strongest baseline was 26.4%. Under amount
  scaling (train-calibrated rate) it is 56.9%. Both met the stop criterion
  in `docs/architecture.md` §9.2.
- `fraud_loss_rate = 0.0019187869` is derived from **training-window**
  amounts: `1 / mean(amount_proxy on train) = 1 / 521.1626`. This keeps
  `mean(fraud_loss_rate × amount_proxy) = 1.0` on train, matching the
  constant-loss comparison scale without using test data. No test-window
  leakage.
- Sensitivity analysis on all four parameters is complete (see §9).

### 5.2 Decision Policy Under Evaluation

For each transaction, the policy chooses the action minimizing expected cost:

```text
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

Where `p` is the model's predicted fraud probability.

When `amount_scaled: true`, `fraud_loss` becomes per-row:
`fraud_loss(amount) = amount × fraud_loss_rate`. The formula is otherwise
unchanged.

Evaluation is of the **policy**, not the raw score. A model with better AUC
but worse policy cost is a worse model for this supplementary analysis.

### 5.3 Label Delay Regime

BAF exposes **month-level granularity only** (integer `month` field, values
0–7). There is no day-level timestamp. Delay regimes are therefore defined in
**months**, not days.

**Supplementary scope:** a **single regime — 1 month.**

Multiple regimes (2-month, 3-month) are documented as future work.

#### 5.3.1 Delay Simulation Rules

- `decision_time = month`
- `label_time = month + Δ`
- Fixed Δ per regime — not sampled per transaction
- Fraud and non-fraud share the same fixed Δ within a regime
- A label is **observed** only if `label_time <= evaluation_end`
- Unobserved labels are treated as **censored**, not negative

#### 5.3.2 Delay Assumptions

- Delay is fixed per regime.
- Sampled delay distributions are out of scope.
- All delay assumptions are documented in `docs/data_card.md` §6.
- Results are reported for the single 1-month regime only. No averaging
  across regimes.

### 5.4 Temporal Backtest Protocol

#### 5.4.1 Splits

Chronological splits only:

```text
train:  decision_time < T_train
val:    T_train <= decision_time < T_val
test:   decision_time >= T_val
```

Constraints:

- Train uses only labels where `label_time <= T_train`
- Val uses only labels where `label_time <= T_val`
- Test uses only labels where `label_time <= test_end`
- Censored labels are excluded from training and evaluation
- Censored counts are reported
- No shuffling
- No stratification that breaks time order

**Implementation:** month-based splits, defined in `src/data/split.py`:

| Split | Months | Rows |
|---|---|---|
| train | 0, 1, 2 | 397,039 |
| val | 3, 4 | 278,627 |
| test | 5, 6 | 227,491 |
| censored (month 7, never observed) | | 96,843 (9.68%) |
| **observed total** | | **903,157** |

An assertion in `split.py` verifies `train + val + test == observed`. This
guards against off-by-one month boundaries leaking rows.

#### 5.4.2 Forbidden (Supplementary)

- K-fold cross-validation on time-series fraud data
- Random oversampling before splitting
- SMOTE applied across time boundaries
- Feature computation using future transactions
- Using post-decision fields (e.g. `device_fraud_count`) as features
- Treating censored labels as negatives

The feature exclusion list in `src/common.py` enforces the post-decision
column exclusion. Censored rows are marked and excluded, never treated as
negative.

### 5.5 Supplementary Metrics

#### 5.5.1 Operational Metrics

| Metric | Definition | Status |
|---|---|---|
| Cost per transaction | Mean realized cost | Reported for all 5 baselines |
| Total cost | Sum of realized cost | Reported for all 5 baselines |
| Fraud dollars saved | Fraud loss avoided vs approve-all | Reported for all 5 baselines |
| Fraud dollars saved at fixed FPR | Value at fixed friction | Not reported |
| Fraud dollars saved at fixed review budget | Value at fixed capacity | Not reported |

#### 5.5.2 Ranking Metrics

| Metric | Definition | Status |
|---|---|---|
| Precision@N | Fraction of top-N alerts that are fraud | Reported at N ∈ {1%, 5%, 10%} |
| Recall@N | Fraction of fraud captured in top-N alerts | Reported at N ∈ {1%, 5%, 10%} |

#### 5.5.3 Probabilistic Metrics

| Metric | Definition | Status |
|---|---|---|
| ROC-AUC | Threshold-independent discrimination | Reported (0.8834, informational) |
| Brier score | Probability calibration | Reported (0.011881 test, 0.010050 val) |
| Expected calibration error (ECE) | Calibration quality | Reported (0.0040 val, null stop) |

**Rule:** AUC may be reported but never used as the sole success criterion.

#### 5.5.4 Data Integrity Metrics (Required)

| Metric | Definition | Value |
|---|---|---|
| Censored-label count | Transactions with `label_time > split cutoff` | **96,843** |
| Censored-label rate | Censored count ÷ total transactions | **9.68%** |
| Evaluated fraction | 1 − censored-label rate | **90.32%** |

### 5.6 Supplementary Baselines

| # | Baseline | Implementation |
|---|---|---|
| 1 | Random decision | Seeded `random.choice(['approve','review','block'])` |
| 2 | Approve-all | `action = 'approve'` for every row |
| 3 | Block-all | `action = 'block'` for every row |
| 4 | LightGBM + static 0.5 | `action = 'block' if p_fraud >= 0.5 else 'approve'` |
| 5 | Cost-sensitive policy | argmin of expected cost |

All baselines use the same temporal split, cost matrix, and delay regime.
No baseline is tuned on the test set.

---

## 6. Reporting Format

Every experiment report follows this format.

### 6.1 Primary — Classification Report

```markdown
# Model Comparison: <date>

## Setup
- Dataset:
- Train split:
- Test split:
- CV strategy:
- Primary metric:

## Cross-Validation Results
| Algorithm | Macro F1 (mean ± SD) | Precision (fraud) | Recall (fraud) | ROC-AUC |

## Final Test Results
| Algorithm | Macro F1 | Precision (fraud) | Recall (fraud) | Confusion Matrix |

## Selected Model
- Algorithm:
- Hyperparameters:
- Justification:

## Failure Analysis
- Dominant error type
- Per-class analysis
```

### 6.2 Supplementary — Cost-Sensitive Report

```markdown
# Experiment: <name>

## Setup
- Dataset:
- Delay regime:
- Splits:
- Model:
- Policy:
- Cost matrix:

## Data Integrity
- Censored-label count:
- Censored-label rate:
- Evaluated fraction:

## Results
| Baseline | Cost/txn | Fraud $ saved | Precision@1% | Recall@1% | Brier |

## Comparison
- Best baseline:
- Improvement:
- Statistical notes:

## Failure Cases
- Where the policy failed
- Why

## Next Steps
```

No report is valid without a baseline comparison, a censored-label count,
and a failure section.

---

## 7. Statistical Rigor

### 7.1 Primary

- **Cross-validation variability:** standard deviation of Macro F1 across
  the 5 folds is reported for each algorithm.
- **Test-set confidence:** bootstrap confidence intervals on the test set
  for the primary metric may be reported as supplementary evidence.
- **No claims smaller than noise:** differences between algorithms are only
  claimed as meaningful if they exceed fold-level variability.

### 7.2 Supplementary

- **Bootstrap CIs on test set:** 1,000 resamples of the test set
  (n = 227,491) with replacement give a 95% CI on the policy's advantage of
  **[52.77%, 60.91%]**, excluding zero.
- **Noise-floor discipline:** all comparisons use 95% bootstrap confidence
  intervals on the test set for the primary metric (realized cost per
  transaction).
- **Documented seeds:** `seed=42` for training, `SEED=42` for the random
  baseline.
- **Documented library versions:** LightGBM 4.7.0, pandas 2.3.3,
  numpy 2.2.6, pyarrow 19.0.1, scikit-learn 1.7.2, PyYAML 6.0.3.

### 7.3 Reproducibility as a Proxy

The pipeline reproduces byte-for-byte from one command. Model AUC, action
distribution, and backtest costs are identical across runs. This is stronger
than a point estimate — it means the result is not seed-dependent.

---

## 8. Calibration Evaluation

### 8.1 Why

The supplementary decision policy depends on `p` being a real probability.
An uncalibrated model produces wrong expected costs.

### 8.2 Methods

- Reliability diagram (10 quantile bins)
- Brier score
- Expected calibration error (ECE)
- Platt scaling or isotonic regression if needed — **not applied**

### 8.3 Result — Null Stop

| Metric | Value |
|---|---:|
| ECE (10 quantile bins) | **0.0040** |
| Brier (model, val) | 0.010050 |
| Brier (trivial, predict val mean) | 0.010103 |

**Stop criterion (`docs/architecture.md` §9.2):** ECE < 0.05 → null stop.

**Verdict: null stop.** ECE of 0.0040 is well below the 0.05 threshold. No
calibration step was applied.

**Reliability note:** the model is well calibrated in bins 0–8 (where 90% of
transactions live). It is mildly overconfident in bin 9 (predicted 9.5%,
actual 7.0%), but those scores fall inside the review band and do not affect
block decisions.

### 8.4 Cadence

Recalibrate whenever the model is retrained, or when calibration drifts
beyond a defined threshold. The ECE diagnostic is not part of the pipeline;
run manually after retraining.

---

## 9. Sensitivity Analysis (Supplementary)

The protocol requires varying four cost parameters:

- `false_positive_cost`
- `review_cost`
- `residual_fraud_loss`
- `fraud_loss` — constant vs amount-scaled

### 9.1 Coverage

| Parameter | Status |
|---|---|
| Amount-scaled `fraud_loss` | ✅ Run, success stop, adopted |
| `false_positive_cost` | ✅ Run — policy advantage 55.6–59.6% across 2× range |
| `review_cost` | ✅ Run — policy advantage 46.5–64.6% across 2× range |
| `residual_fraud_loss` | ✅ Run — policy advantage 49.9–62.1% across 2× range |

All four parameters are tested. Amount scaling was adopted as the default.
Minimum advantage across all variations: 46.46%.

### 9.2 Amount-Scaled Sensitivity Result

**Setup:** `amount_scaled: true`, `fraud_loss_rate = 0.0019187869`. Same
model, same split, same test set. Only the cost assumption changed.

**Stop criterion:** flips ≥ 2% OR cost/txn change ≥ 1% relative.

| Config | Policy cost/txn | Strongest baseline | Advantage |
|---|---:|---:|---:|
| Constant `fraud_loss = 1.0` | 0.008901 | 0.012088 | 26.4% |
| Amount-scaled (train-cal) | **0.007566** | 0.017543 | **56.9%** |

- Cost/txn change: **−15.0%** relative (satisfies the ≥ 1% stop criterion)

**Verdict: success stop.** Amount scaling is adopted.

**Mechanism:** with per-row fraud loss, the argmin routes large transactions
to review instead of approve. Under constant loss those transactions were
approved.

### 9.3 Rate Calibration

`fraud_loss_rate` is derived from **training-window** amounts
(`1 / mean(amount_proxy on train)`). No test data is used.

---

## 10. Budget-Constrained Evaluation (Supplementary)

### 10.1 Budgets

| Budget | Meaning |
|---|---|
| Top 1% of transactions | Tight capacity |
| Top 5% of transactions | Moderate capacity |
| Top 10% of transactions | Loose capacity |

### 10.2 Implementation

| Budget | Precision | Recall |
|---|---:|---:|
| @1% | 0.2347 | 0.1866 |
| @5% | 0.1201 | 0.4775 |
| @10% | 0.0798 | 0.6344 |

These budgets are pure ranking metrics on the scored test set. They do not
change the policy's actions. Capacity-aware decisioning is a post-course
extension.

---

## 11. Reproducibility Requirements

### 11.1 Primary

- Fixed random seeds (42)
- Fixed chronological split documented in `docs/data_card.md` §5
- Fixed CV folds
- Environment pinned in `requirements.txt`
- One command reproduces the full primary pipeline

### 11.2 Supplementary

- Fixed cost matrix in `configs/costs.yaml`
- Fixed delay regime (1 month)
- One command reproduces the supplementary pipeline

### 11.3 Deviations

- **Splits are hardcoded** in `src/data/split.py` and documented in
  `docs/data_card.md`, rather than loaded from a `configs/splits.yaml`.
  Documented as a deviation.
- **No `cost_config_hash` in the action log.** With one cost matrix in use,
  there is nothing to disambiguate.

---

## 12. Definition of Done

### 12.1 Primary (Course Requirement)

- [ ] Three algorithms implemented: Logistic Regression, Random Forest, LightGBM
- [ ] Chronological 80/20 split defined
- [ ] 5-fold time-series CV folds defined
- [ ] Preprocessing fit within each fold's training portion
- [ ] Hyperparameter grids documented per algorithm
- [ ] Cross-validation results table complete (mean ± SD)
- [ ] Best model selected on validation
- [ ] Final test evaluation run once
- [ ] Test-set metrics reported: Macro F1, accuracy, per-class precision/recall/F1, confusion matrix, ROC-AUC
- [ ] Failure analysis complete
- [ ] Model comparison report written (`reports/model_comparison.md`)
- [ ] Results reproducible from one command

### 12.2 Supplementary (Project Depth)

- [x] Cost matrix defined and frozen in `configs/costs.yaml`
- [x] Delay regime implemented (1-month month-based fallback)
- [x] Baselines implemented: random, approve-all, block-all, LightGBM + static 0.5
- [x] Primary supplementary metrics computed (cost/txn, total cost, fraud $ saved)
- [x] Ranking metrics computed (precision@1/5/10%, recall@1/5/10%)
- [x] Calibration measured: Brier and ECE
- [x] Censored-label counts reported (96,843 / 9.68%)
- [x] Sensitivity analysis complete across all four cost parameters
- [x] Bootstrap confidence intervals computed
- [x] Failure cases documented
- [x] Results reproducible (verified byte-for-byte)
- [x] Supplementary report written (`reports/mvp_backtest.md`)

---

## 13. Guiding Rules

### 13.1 Primary

> Three algorithms are only comparable if they use the **same split, same
> preprocessing, same folds, and same primary metric.** Any deviation must
> be documented and justified.

> The test set is used **once**, after model selection. Any result that
> touches the test set before that is invalid.

### 13.2 Supplementary

> A model is only better if it produces **lower realized cost** under the
> **same temporal split, same delay regime, same cost matrix, and same
> budget** as the baseline.

### 13.3 Primary Result

Primary success criterion:

```text
selected model (by Macro F1)
    achieves the highest validation Macro F1 among the three algorithms,
    and its test Macro F1 is reported once on the untouched test set.
```

### 13.4 Supplementary Result

Supplementary success criterion:

```text
realized cost per transaction (policy)
    <
realized cost per transaction (every canonical baseline)
```

under identical split, delay regime, cost matrix, and budget.

**Result:** the cost-sensitive policy beats every implemented baseline on
realized cost per transaction under the same split, delay regime, and cost
matrix. See `reports/mvp_backtest.md` for the full table.

---

## 14. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | Initial evaluation protocol | Project start |
| 2026-09-22 | Added cost matrix, temporal backtest, canonical baselines, forbidden metrics | Align with Week 1 MVP |
| 2026-09-22 | Recorded amount-scaled sensitivity as adopted; recorded calibration null stop; documented MVP deviations | Reconcile with built MVP |
| 2026-09-22 | Restructured into primary (three-algorithm classification) and supplementary (cost-sensitive policy); added Macro F1 justification; added 5-fold time-series CV; added preprocessing and tuning rules; added test-set discipline; separated DoD into primary and supplementary | Align with course requirements |
