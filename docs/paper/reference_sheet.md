# Paper Reference Sheet

One-page headline lookup for the paper team, followed by supporting tables.
Every number and claim used in the paper must be traceable to this sheet.

---

## 1. Key Numbers (exact — do not round without noting)

| Number | Value | Source |
|---|---:|---|
| Dataset size | 1,000,000 rows | reports/decision_backtest.md §Data Integrity |
| Fraud rate (overall) | 1.1029% | data_card.md §4.5 |
| Fraud rate (test) | 1.2576% | reports/decision_backtest.md §Data Integrity |
| Censored labels | 96,843 (9.68%) | reports/decision_backtest.md §Data Integrity |
| Train rows | 397,039 (months 0–2) | evaluation_protocol.md §4 |
| Val rows | 278,627 (months 3–4) | evaluation_protocol.md §4 |
| Test rows | 227,491 (months 5–6) | evaluation_protocol.md §4 |
| Features used | 28 | docs/data_card.md §10.4 |
| ECE (val) | 0.0033 | decision_policy.md §9.2 |
| Brier (test) | 0.011506 | reports/decision_backtest.md §Calibration |
| Policy cost/txn | 0.007491 | reports/decision_backtest.md §Results |
| Strongest static-0.5 (LGBM+0.5) cost/txn | 0.017798 | reports/decision_backtest.md §Results |
| Approve-all cost/txn | 0.018928 | reports/decision_backtest.md §Results |
| **Policy advantage** | **57.91%** | reports/decision_backtest.md §Interpretation |
| Advantage 95% CI | [53.95%, 62.13%] | reports/bootstrap.md |
| Min advantage across cost variations | 47.76% | reports/sensitivity.md |
| Approve / Review / Block counts | 205,395 / 21,371 / 725 | reports/decision_backtest.md §Action distribution |
| Test suite | 58 tests | pytest -q |

**The four numbers to preserve exactly: 57.91%, [53.95%, 62.13%], 96,843, 9.68%.**

### 1.1 Split Summary

| Split | Rows | Fraud rate | Source |
|---|---:|---:|---|
| Train (months 0–2) | 397,039 | 0.9813% | reports/decision_backtest.md §Data Integrity; eda_summary.json |
| Validation (months 3–4) | 278,627 | 1.0207% | reports/decision_backtest.md §Data Integrity; eda_summary.json |
| Test (months 5–6) | 227,491 | 1.2576% | reports/decision_backtest.md §Data Integrity; eda_summary.json |
| Censored (month 7) | 96,843 | — | reports/decision_backtest.md §Data Integrity |

### 1.2 EDA Findings (paper-relevant)

| Number | Value | Source |
|---|---:|---|
| Fraud rate (month 0) | 1.13% | eda_summary.json |
| Fraud rate (month 7) | 1.47% | eda_summary.json |
| `proposed_credit_limit` mean | 515.85 | eda_summary.json |
| `proposed_credit_limit` median | 200 | eda_summary.json |
| `proposed_credit_limit` skew | 1.30 | eda_summary.json |
| `proposed_credit_limit` IQR-flagged share | 24.17% | eda_summary.json |
| Point-biserial r (`credit_risk_score`) | 0.0706 | eda_summary.json |
| Point-biserial r (`proposed_credit_limit`) | 0.0689 | eda_summary.json |
| `mean(amount_proxy on train)` | 521.1626 | decision_policy.md §7.1 |
| `fraud_loss_rate` | 0.0019187869 | configs/costs.yaml; decision_policy.md §7.1 |

### 1.3 Classifier Cross-Validation

| Number | Value | Source |
|---|---:|---|
| LightGBM CV realized cost (mean ± SD) | 0.005852 ± 0.000300 | reports/model_comparison.md; reports/cv_results.json |
| Logistic Regression CV realized cost (mean ± SD) | 0.005915 ± 0.000338 | reports/model_comparison.md; reports/cv_results.json |
| Random Forest CV realized cost (mean ± SD) | 0.006515 ± 0.000579 | reports/model_comparison.md; reports/cv_results.json |
| Top gap (absolute) | 0.000063 | reports/model_comparison.md |
| Top gap (relative) | 1.07% | reports/model_comparison.md |
| Noise-band threshold | 5% | evaluation_protocol.md §8, §17.1 |

### 1.4 Selected Classifier Behavior at the 0.5 Cut (supporting)

These numbers describe the raw classifier at the naive 0.5 probability cut. **This is not the deployed operating point.** The deployed system is the argmin policy; see §1.8.

| Metric | Value | Source |
|---|---:|---|
| Macro F1 | 0.5031 | reports/model_comparison.md §Final Test Results |
| Accuracy | 0.9875 | reports/model_comparison.md §Final Test Results |
| Precision (fraud) | 0.7826 | reports/model_comparison.md §Final Test Results |
| Recall (fraud) | 0.0063 | reports/model_comparison.md §Final Test Results |
| ROC-AUC | 0.8753 | reports/model_comparison.md §Final Test Results |
| Confusion matrix (TN, FP, FN, TP) | (224,625, 5, 2,843, 18) | reports/model_comparison.md §Final Test Results |

### 1.5 Static-Threshold Baselines vs Approve-All

| Comparison | Reduction | Source |
|---|---:|---|
| LightGBM + 0.5 vs approve-all | 5.97% | reports/decision_backtest.md §Results |
| Logistic Regression + 0.5 vs approve-all | 1.01% | reports/decision_backtest.md §Results |
| Random Forest + 0.5 vs approve-all | 0% | reports/decision_backtest.md §Results |

### 1.6 Bootstrap Details (full)

| Quantity | Point estimate | 95% CI | Source |
|---|---:|---|---|
| Policy cost/txn | 0.007491 | [0.007196, 0.007797] | reports/bootstrap.md |
| LGBM+0.5 cost/txn | 0.017798 | [0.016967, 0.018670] | reports/bootstrap.md |
| Difference (baseline − policy) | 0.010307 | [0.009602, 0.011058] | reports/bootstrap.md |
| Advantage (%) | 57.91% | [53.95%, 62.13%] | reports/bootstrap.md |
| Resamples | 1,000 | — | reports/bootstrap.md |
| Seed | 42 | — | reports/bootstrap.md |

### 1.7 Cost Sensitivity Sweep (full)

| Configuration | Policy cost/txn | Strongest baseline | Advantage | Source |
|---|---:|---|---:|---|
| Baseline | 0.007491 | LGBM + 0.5 (0.017798) | 57.91% | reports/sensitivity.md |
| `false_positive_cost = 0.05` | 0.007037 | LGBM + 0.5 (0.017752) | 60.36% | reports/sensitivity.md |
| `false_positive_cost = 0.20` | 0.007625 | LGBM + 0.5 (0.017890) | 57.38% | reports/sensitivity.md |
| `review_cost = 0.01` | 0.006253 | LGBM + 0.5 (0.017798) | 64.87% | reports/sensitivity.md |
| `review_cost = 0.04` | 0.009298 | LGBM + 0.5 (0.017798) | 47.76% | reports/sensitivity.md |
| `residual_fraud_loss = 0.15` | 0.006588 | LGBM + 0.5 (0.017798) | 62.99% | reports/sensitivity.md |
| `residual_fraud_loss = 0.60` | 0.008700 | LGBM + 0.5 (0.017798) | 51.12% | reports/sensitivity.md |

### 1.8 Policy Operational Metrics

The metrics in §1.4 describe the classifier at 0.5. These describe the deployed policy, which routes by argmin.

| Metric | Value | Source |
|---|---:|---|
| Policy operational precision | 0.0654 | reports/model_comparison.md §Final Test Results |
| Policy operational recall | 0.5051 | reports/model_comparison.md §Final Test Results |
| Precision@1% | 0.2431 | reports/decision_backtest.md §Ranking metrics |
| Precision@5% | 0.1189 | reports/decision_backtest.md §Ranking metrics |
| Precision@10% | 0.0775 | reports/decision_backtest.md §Ranking metrics |
| Recall@1% | 0.1933 | reports/decision_backtest.md §Ranking metrics |
| Recall@5% | 0.4729 | reports/decision_backtest.md §Ranking metrics |
| Recall@10% | 0.6162 | reports/decision_backtest.md §Ranking metrics |

---

## 2. Claims You Can Make (with evidence)

| Claim | Evidence |
|---|---|
| Cost-sensitive policy outperforms strongest baseline | 0.007491 vs 0.017798, 57.91% reduction |
| Result is not statistical noise | Bootstrap CI [53.95%, 62.13%], excludes zero |
| Result is robust to cost assumptions | Min advantage 47.76% across 2× range on 3 parameters |
| Result does not depend on test-set tuning | fraud_loss_rate derived from train window |
| Calibration is adequate without post-hoc fix | ECE = 0.0033, below 0.05 threshold |
| Censored labels excluded, not treated as negative | 96,843 month-7 rows marked and excluded |
| Splits are temporal, not random | Chronological split; split.py asserts sum |
| Pipeline reproduces from one command | `python -m src.pipeline` byte-for-byte |
| Static threshold is near-null at this base rate | LGBM+0.5 reduces cost 5.97% vs approve-all (0.018928 → 0.017798) |

---

## 3. Claims You CANNOT Make (avoid these)

| Do NOT say | Why |
|---|---|
| "High accuracy" | Accuracy is meaningless at 1.26% base rate and is a forbidden metric (evaluation_protocol.md §15) |
| "The model detects fraud with X% accuracy" | Same reason; use cost reduction, not accuracy |
| "Production-ready" | Synthetic dataset, single delay regime, proxy amount column |
| "Real-time performance verified" | No latency measurement was done |
| "Handles all delay regimes" | Only 1-month regime was tested |
| "Outperforms on all metrics" | Ranking metrics (precision/recall) are modest; the win is on cost |
| "Tested on real bank data" | BAF is synthetic |
| "Generalizes to other fraud domains" | Not tested |
| "Capacity-aware" | No capacity constraint was modeled |
| "Statistically significant across all variations" | CIs computed only on the main test-set comparison |

---

## 4. Methodology Summary (2 sentences the paper can reuse)

At decision time, a LogisticRegression classifier produces a fraud
probability for each transaction. A cost-sensitive policy then selects the
action — approve, review, or block — that minimizes expected cost under a
fixed cost matrix, with transaction amount scaling the fraud loss term.

---

## 5. What Was NOT Done (state in Limitations)

- Single delay regime (1 month); no 2-month or 3-month
- Hyperparameter grid per algorithm evaluated on the same folds; selection by mean realized cost
- No calibration adjustment (ECE already below threshold)
- No capacity constraint on review queue
- Amount proxy = proposed_credit_limit; BAF has no clean amount column
- No bootstrap CIs on the sensitivity runs (only on the main comparison)
- No rule-based threshold baseline (deferred; 6 canonical baselines implemented: Random, Approve-all, Block-all, LR+0.5, RF+0.5, LGBM+0.5)
- Synthetic data; results are not production estimates

---

## 6. Section → Source Doc Map

| Paper section | Read this |
|---|---|
| Introduction | problem_framing.md §1–4 |
| Related Work | (paper team must write; cite Elkan 2001, Chapelle 2014, Jesus 2022, Dal Pozzolo 2015) |
| Methodology | decision_policy.md §5–6 |
| Dataset | data_card.md §2–5 |
| Experimental Setup | evaluation_protocol.md §7–9 |
| Results | reports/decision_backtest.md + reports/bootstrap.md + reports/sensitivity.md |
| Discussion | reports/decision_backtest.md §Interpretation |
| Limitations | reports/decision_backtest.md §Limitations |
| Conclusion | roadmap.md §5–7 |
| References | (paper team must build) |
