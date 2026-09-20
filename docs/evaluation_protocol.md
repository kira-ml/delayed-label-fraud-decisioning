# Evaluation Protocol

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** Evaluation Protocol  
> **Status:** v0.1 — LOCKED before modeling  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

This document defines how the project is evaluated **before** any model is trained.

It exists to prevent:

- Cherry-picking metrics after seeing results
- Using random splits that leak future information
- Reporting AUC without operational meaning
- Ignoring false-positive and review costs
- Comparing models under different label-delay regimes
- Claiming success without a cost-based, temporal backtest

**Rule:** If a result is not produced by this protocol, it does not go in the report.

---

## 2. Core Evaluation Question

> Given a decision policy that must act **now** with only delayed and partial labels, how much operational utility does the system create compared to realistic baselines?

Utility is not accuracy.  
Utility is not AUC.  
Utility is:

```text
utility = fraud loss avoided
        − false-positive cost
        − review cost
```

---

## 3. Evaluation Principles

1. **Temporal only.** No random splits. No shuffling. Ever.
2. **Delay-aware.** A label may only be used after `label_time`.
3. **Cost-based.** Every decision is scored by realized cost.
4. **Budget-aware.** Report at fixed alert and review budgets.
5. **Baseline-anchored.** Every improvement must beat a named baseline.
6. **Reproducible.** Fixed seeds, fixed splits, fixed cost matrix.
7. **Honest.** Report failures, not just wins.
8. **Pre-registered.** Metrics and thresholds are fixed before modeling.

---

## 4. Cost Matrix

The cost matrix is fixed in `configs/costs.yaml` and must not change between runs unless the change is documented as an experiment.

### 4.1 Decision Outcomes

| Action | True label = fraud (y=1) | True label = legit (y=0) |
|---|---|---|
| approve | `fraud_loss` | `0` |
| review | `review_cost + residual_fraud_loss` | `review_cost` |
| block | `0` | `false_positive_cost` |

### 4.2 Week 1 Cost Values (relative units)

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss_after_review: 0.3
```

### 4.3 Notes

- Costs are **relative units** in Week 1. Absolute calibration is out of scope.
- `residual_fraud_loss_after_review` reflects that review does not catch all fraud.
- Sensitivity analysis on `false_positive_cost` and `review_cost` is required in the final report.
- Do not silently change costs between baseline and improved model.

---

## 5. Decision Policy Under Evaluation

For each transaction, the policy chooses the action minimizing expected cost:

```text
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

Where `p` is the model's predicted fraud probability.

Evaluation is of the **policy**, not the raw score.  
A model with better AUC but worse policy cost is a worse model for this project.

---

## 6. Label Delay Regimes

Every experiment is run under three delay regimes:

| Regime | Delay Δ | Purpose |
|---|---|---|
| Short | 7 days | Near-realistic fast chargeback |
| Medium | 30 days | Typical dispute window |
| Long | 90 days | Worst-case delayed feedback |

### 6.1 Delay Simulation Rules

- `decision_time = t`
- `label_time = t + Δ`
- A label is **observed** only if `label_time <= evaluation_end`
- Unobserved labels are treated as **censored**, not negative

### 6.2 Delay Assumptions

- Fraud labels are sampled from a delay distribution, not fixed.
- Non-fraud labels use an observation window.
- All assumptions are documented in `data_card.md`.
- Results must be reported **separately per regime**. No averaging across regimes.

---

## 7. Temporal Backtest Protocol

### 7.1 Splits

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
- No shuffling
- No stratification that breaks time order

### 7.2 Rolling Evaluation (Week 3+)

Once Week 1 baseline is done, add rolling windows:

```text
window k: train on [T0, Tk), test on [Tk, Tk+1)
```

Report per-window metrics to expose drift.

### 7.3 Forbidden

- K-fold cross-validation on time-series fraud data
- Random oversampling before splitting
- SMOTE applied across time boundaries
- Feature computation using future transactions
- Using post-decision fields (e.g., chargeback reason code) as features

---

## 8. Metrics

All metrics are reported per delay regime and per baseline.

### 8.1 Primary Metrics (Operational)

| Metric | Definition | Why it matters |
|---|---|---|
| Cost per transaction | Mean realized cost | Direct business impact |
| Total cost | Sum of realized cost | Portfolio-level impact |
| Fraud dollars saved | Fraud loss avoided vs approve-all | Value created |
| Fraud dollars saved at fixed FPR | Value at fixed friction | Fair comparison |
| Fraud dollars saved at fixed review budget | Value at fixed capacity | Operational reality |

### 8.2 Ranking Metrics

| Metric | Definition |
|---|---|
| Precision@N | Fraction of top-N alerts that are fraud |
| Recall@N | Fraction of fraud captured in top-N alerts |
| Alerts per true fraud | Alert efficiency |
| Fraud caught per reviewer hour | Investigator productivity proxy |

### 8.3 Probabilistic Metrics

| Metric | Definition |
|---|---|
| PR-AUC | Precision-recall AUC |
| ROC-AUC | Reported but not primary |
| Brier score | Probability calibration |
| Expected calibration error (ECE) | Calibration quality |

**Rule:** AUC may be reported but never used as the sole success criterion.

### 8.4 Temporal Metrics

| Metric | Definition |
|---|---|
| Performance over time | Metric vs window |
| Time-to-detect drift | Windows until monitor fires |
| Recovery after retrain | Windows to return to baseline |
| Offline-vs-live gap | Offline estimate minus live estimate |

### 8.5 Forbidden Metrics

- Accuracy (meaningless under class imbalance)
- Raw F1 without cost context
- AUC-only claims
- Metrics computed on random splits

---

## 9. Baselines

Every improvement must be compared against **all** of the following:

| # | Baseline | Purpose |
|---|---|---|
| 1 | Random decision | Sanity floor |
| 2 | Rule-based threshold | Domain prior |
| 3 | Approve-all | Zero-friction reference |
| 4 | Block-all | Maximum-friction reference |
| 5 | Offline LightGBM + static threshold | Standard ML baseline |
| 6 | Cost-sensitive LightGBM | Week 2 improvement |

### 9.1 Rules

- All baselines use the same temporal splits.
- All baselines use the same cost matrix.
- All baselines use the same delay regimes.
- No baseline is tuned on the test set.
- If a baseline is missing, the comparison is invalid.

---

## 10. Budget-Constrained Evaluation

Real systems have finite capacity. Report at:

| Budget | Meaning |
|---|---|
| Top 1% of transactions | Tight capacity |
| Top 5% of transactions | Moderate capacity |
| Top 10% of transactions | Loose capacity |

At each budget, report:

- Precision@N
- Recall@N
- Fraud dollars saved
- Total cost

This prevents the "review everything" trivial solution.

---

## 11. Calibration Evaluation

### 11.1 Why

The decision policy depends on `p` being a real probability.  
An uncalibrated model produces wrong expected costs.

### 11.2 Methods

- Reliability diagram
- Brier score
- Expected calibration error (ECE)
- Platt scaling or isotonic regression if needed

### 11.3 Week 1 Rule

Raw LightGBM output is acceptable **if** calibration is measured and reported.  
Do not silently assume calibration.

---

## 12. Sensitivity Analysis

Required in the final report:

- Vary `false_positive_cost` across a range
- Vary `review_cost` across a range
- Vary `residual_fraud_loss_after_review`
- Report how policy choices change
- Report how rankings of models change

Purpose: show results are not artifacts of one arbitrary cost matrix.

---

## 13. Reporting Format

Every experiment report includes:

```markdown
# Experiment: <name>

## Setup
- Dataset:
- Delay regime:
- Splits:
- Model:
- Policy:
- Cost matrix:

## Results
| Baseline | Cost/txn | Fraud $ saved | Precision@1% | Recall@1% | ECE |

## Comparison
- Best baseline:
- Improvement:
- Statistical notes:

## Failure Cases
- Where the policy failed
- Why

## Next Steps
```

No report is valid without a baseline comparison and a failure section.

---

## 14. Statistical Rigor

- Report confidence intervals via bootstrap on the test set
- Report per-window variance for rolling evaluation
- Do not claim improvement smaller than noise
- Document seeds
- Document library versions

Week 1 may skip formal significance testing, but must state that limitation.

---

## 15. Reproducibility Requirements

- Fixed random seeds
- Fixed splits saved to disk
- Fixed cost matrix in config
- Pipeline runs with one command
- Environment pinned in `requirements.txt`
- Report references exact config hashes

If a result cannot be reproduced, it is not a result.

---

## 16. Week 1 Evaluation Scope

Week 1 evaluates:

- Baseline LightGBM + static threshold
- Cost-sensitive policy with fixed costs
- Temporal split
- 7 / 30 / 90 day delay regimes
- Cost per transaction, fraud dollars saved, precision@N, calibration

Week 1 does **not** evaluate:

- Online learning
- PU learning
- Delayed-label correction
- Drift detection
- Graph features
- Federated learning

Those are evaluated in later weeks with the same protocol.

---

## 17. Definition of Done for Evaluation

- [ ] Cost matrix defined and frozen
- [ ] Delay regimes implemented
- [ ] Temporal splits implemented
- [ ] Baselines implemented
- [ ] Primary metrics computed
- [ ] Ranking metrics computed
- [ ] Calibration measured
- [ ] Budget-constrained metrics computed
- [ ] Per-regime results reported
- [ ] Failure cases documented
- [ ] Results reproducible
- [ ] Report written

---

## 18. Guiding Rule

> A model is only better if it produces **lower realized cost** under the **same temporal split, same delay regime, same cost matrix, and same budget** as the baseline.

Everything else is noise.
