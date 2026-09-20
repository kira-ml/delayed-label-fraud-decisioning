# MVP Backtest Report

_Generated: 2026-09-20 16:59:05 UTC_

## Setup

- Dataset: BAF `Base.csv`
- Delay regime: 1 month (`label_month = month + 1`)
- Split: train months {0,1,2}, val {3,4}, test {5,6}
- Model: LightGBM binary classifier, library defaults, early stopping on val
- Policy: `argmin` of expected cost over `{approve, review, block}`
- Cost matrix: `fraud_loss=1.0`, `false_positive_cost=0.1`, `review_cost=0.02`, `residual_fraud_loss=0.3`

## Data Integrity

- Total transactions: 1,000,000
- Censored (`label_month > 7`): 96,843 (9.68%)
- Evaluated test rows (observed labels, months 5-6): 227,491

## Results

| Baseline | Cost/txn | Total cost | Fraud $ saved vs approve-all |
|---|---:|---:|---:|
| Random | 0.044916 | 10218.04 | -7357.04 |
| Approve-all | 0.012576 | 2861.00 | 0.00 |
| Block-all | 0.098742 | 22463.00 | -19602.00 |
| LightGBM + static 0.5 | 0.012088 | 2749.90 | 111.10 |
| Cost-sensitive policy | 0.008901 | 2024.98 | 836.02 |

## Ranking metrics (on the policy's scores)

| Budget | Precision | Recall |
|---|---:|---:|
| @1%  | 0.2347 | 0.1866 |
| @5%  | 0.1201 | 0.4775 |
| @10% | 0.0798 | 0.6344 |

## Calibration

- Brier score: **0.011881**
- ROC-AUC (informational only): 0.8834

## Action distribution

- `approve`: 210,734
- `review`: 15,124
- `block`: 1,633

## Interpretation

The cost-sensitive policy achieves **0.008901** cost per transaction. The strongest non-policy baseline is **LightGBM + static 0.5** at **0.012088**.
**Result:** the policy does beat the strongest baseline on realized cost per transaction under the same split, delay regime, and cost matrix.

## Limitations

- Single delay regime (1 month).
- Constant `fraud_loss`; no amount-scaled cost in this MVP.
- BAF is synthetic data; results are not production estimates.
- Censored labels are excluded, not modelled.
- No hyperparameter tuning, no calibration step, no capacity constraint.
