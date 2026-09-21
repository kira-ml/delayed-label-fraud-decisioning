# MVP Backtest Report

_Generated: 2026-09-21 13:31:41 UTC_

## Setup

- Dataset: BAF `Base.csv`
- Delay regime: 1 month (`label_month = month + 1`)
- Split: train months {0,1,2}, val {3,4}, test {5,6}
- Model: LightGBM binary classifier, library defaults, early stopping on val
- Policy: `argmin` of expected cost over `{approve, review, block}`
- Cost matrix: `fraud_loss=1.0` (fallback; overridden by amount scaling), `false_positive_cost=0.1`, `review_cost=0.02`, `residual_fraud_loss=0.3`
- Amount scaling: **enabled**, `fraud_loss(amount) = amount * 0.0019187869`
- Rate calibration: `1 / mean(amount_proxy on train) = 1 / 521.1626`, train-window only, no test-set leakage

## Data Integrity

- Total transactions: 1,000,000
- Censored (`label_month > 7`): 96,843 (9.68%)
- Evaluated test rows (observed labels, months 5-6): 227,491

## Results

| Baseline | Cost/txn | Total cost | Fraud $ saved vs approve-all |
|---|---:|---:|---:|
| Random | 0.046931 | 10,676.27 | −6,370.40 |
| Approve-all | 0.018928 | 4,305.87 | 0.00 |
| Block-all | 0.098742 | 22,463.00 | −18,157.13 |
| LightGBM + static 0.5 | 0.017543 | 3,990.93 | 314.95 |
| **Cost-sensitive policy** | **0.007566** | **1,721.21** | **2,584.67** |

## Ranking metrics (on the policy's scores)

| Budget | Precision | Recall |
|---|---:|---:|
| @1%  | 0.2347 | 0.1866 |
| @5%  | 0.1201 | 0.4775 |
| @10% | 0.0798 | 0.6344 |

## Calibration

- Brier score (test): **0.011881**
- Brier score (val): 0.010050
- ECE (val, 10 quantile bins): **0.0040** — null stop, no calibration step applied
- ROC-AUC (informational only): 0.8834

## Action distribution

- `approve`: 206,724
- `review`: 19,155
- `block`: 1,612

## Interpretation

The cost-sensitive policy achieves **0.007566** cost per transaction against
the strongest non-policy baseline, **LightGBM + static 0.5**, at **0.017543**.
That is a **56.87% reduction in realized cost per transaction** under the
same split, delay regime, and cost matrix.

The ranking of baselines confirms the project's core premise: a static 0.5
threshold on a 1.26%-base-rate problem is nearly equivalent to approve-all
(0.017543 vs 0.018928 — a 7.3% reduction). The value comes from the cost
structure, not the classifier. The policy routes large transactions to
review and small ones to approve based on expected cost, which the
threshold policy cannot do.

Bootstrap 95% CI on the advantage is **[52.77%, 60.91%]**, excluding zero.
The policy and baseline confidence intervals are disjoint — the policy's
worst-case (0.007874) is less than half the baseline's best-case (0.016732).

## Sensitivity Analysis

Full cost sensitivity is required by `evaluation_protocol.md` §12.1. Three
cost parameters — `false_positive_cost`, `review_cost`, `residual_fraud_loss` —
were varied one at a time across a 2× range while holding everything else
fixed. The model was not retrained; decisions were recomputed via argmin at
each setting.

**Pre-registered stop criterion:** success if the policy remains the
lowest-cost action at every variation; null if its advantage drops below 5%
relative at any variation.

| Config | Policy | Strongest baseline | Baseline cost | Advantage |
|---|---:|---|---:|---:|
| baseline | 0.007566 | LightGBM+0.5 | 0.017543 | 56.87% |
| false_positive_cost=0.05 | 0.007055 | LightGBM+0.5 | 0.017480 | 59.64% |
| false_positive_cost=0.20 | 0.007845 | LightGBM+0.5 | 0.017670 | 55.60% |
| review_cost=0.01 | 0.006217 | LightGBM+0.5 | 0.017543 | 64.56% |
| review_cost=0.04 | 0.009393 | LightGBM+0.5 | 0.017543 | 46.46% |
| residual_fraud_loss=0.15 | 0.006644 | LightGBM+0.5 | 0.017543 | 62.13% |
| residual_fraud_loss=0.60 | 0.008783 | LightGBM+0.5 | 0.017543 | 49.94% |

**Verdict: success stop.** The policy is the lowest-cost action in every
configuration. The minimum advantage across all 6 variations is 46.46%,
which is 9× the 5% effect-size threshold in `architecture.md` §9.1. The
ranking of baselines does not change under any tested cost assumption.

`review_cost` is the most influential parameter (advantage range 46–65%);
`false_positive_cost` is the least influential (advantage range 56–60%),
because only ~1,612 test transactions are routed to block.

## Statistical Rigor

Bootstrap confidence intervals are required by `evaluation_protocol.md` §14.
1,000 resamples of the test set (n = 227,491) with replacement, seed = 42.

**Pre-registered stop criterion:** success if the 95% CI on the difference
(baseline − policy) excludes zero; null if it includes zero.

| Quantity | Point estimate | 95% CI |
|---|---:|---|
| Policy cost/txn | 0.007566 | [0.007277, 0.007874] |
| LightGBM + 0.5 cost/txn | 0.017543 | [0.016732, 0.018336] |
| Difference (baseline − policy) | 0.009977 | [0.009257, 0.010686] |
| Advantage (%) | 56.87% | [52.77%, 60.91%] |

**Verdict: success stop.** The 95% CI on the difference excludes zero. The
policy and baseline CIs are disjoint — the policy's worst-case (0.007874) is
less than half the baseline's best-case (0.016732). The lower bound of the
advantage (52.77%) still clears the constant-loss MVP advantage (26.4%),
so the result is not a statistical artifact.

## Stopping Decisions

Per `architecture.md` §9.5, every phase's stop criterion is reported.

| Phase | Criterion | Measured | Verdict |
|---|---|---|---|
| Baseline model | LightGBM + static 0.5 beats approve-all on cost/txn | 0.017543 vs 0.018928 | success stop |
| Calibration | ECE < 0.05 | ECE = 0.0040 (val) | success stop (null stop — no calibration applied) |
| Amount-scaled cost sensitivity | cost/txn change ≥ 1% relative | −15.0% relative | success stop — amount scaling adopted |
| Full cost sensitivity | policy remains lowest-cost at every variation | min advantage 46.46% | success stop |
| Bootstrap CIs | 95% CI on difference excludes zero | [0.009257, 0.010686] | success stop |
| Feature engineering | batch improves val cost/txn ≥ 1% relative | not attempted — no measured failure | scope stop |
| Policy tuning | explicit thresholds beat derived by ≥ 5% | not attempted — argmin is source of truth | scope stop |
| Capacity simulation | not in MVP scope | — | scope stop |

## Limitations

- Single delay regime (1 month). Multiple regimes (2-month, 3-month) deferred to post-MVP work.
- Amount-scaled `fraud_loss` uses `amount_proxy = proposed_credit_limit`, a documented proxy. BAF has no clean transaction amount column.
- BAF is synthetic data; results are not production estimates.
- Censored labels are excluded, not modelled. 96,843 month-7 transactions (9.68%) are never observed.
- `false_positive_cost` is modeled as constant; in production it plausibly scales with amount (lost revenue, customer value). Documented as out of scope.
- No hyperparameter tuning, no calibration step (ECE = 0.0040, null stop), no capacity constraint.
- Only the LightGBM + static 0.5 baseline uses the model's scores; the random baseline is seeded but resampled per config in the sensitivity run.

## Reproduction

Three commands reproduce every number in this report from scratch:

```bash
python -m src.pipeline                    # load -> delay -> split -> train -> score -> decide -> backtest
python -m src.evaluation.sensitivity      # writes reports/sensitivity.md
python -m src.evaluation.bootstrap        # writes reports/bootstrap.md
```

Environment: Python 3.10, LightGBM 4.7.0, pandas 2.3.3, numpy 2.2.6, pyarrow 19.0.1, scikit-learn 1.7.2, PyYAML 6.0.3. All seeds fixed (`SEED=42`).