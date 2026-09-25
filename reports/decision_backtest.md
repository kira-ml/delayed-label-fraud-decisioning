# Backtest Report

_Generated: 2026-09-25 14:52:11 UTC_

## Setup

- Dataset: BAF `Base.csv`
- Delay regime: 1 month (`label_month = month + 1`)
- Split: train months {0,1,2}, val {3,4}, test {5,6}
- Model: selected classifier from the 3-algorithm comparison (models/best_model.pkl)
- Policy: `argmin` of expected cost over `{approve, review, block}`
- Cost matrix: `fraud_loss=1.0`, `false_positive_cost=0.1`, `review_cost=0.02`, `residual_fraud_loss=0.3`
- Amount scaling: **enabled**, `fraud_loss(amount) = amount * 0.0019187869`

## Data Integrity

- Total transactions: 1,000,000
- Censored (`label_month > 7`): 96,843 (9.68%)
- Evaluated test rows (observed labels, months 5-6): 227,491

## Results

| Baseline | Cost/txn | Total cost | Fraud $ saved vs approve-all |
|---|---:|---:|---:|
| Random | 0.047484 | 10802.09 | -6496.21 |
| Approve-all | 0.018928 | 4305.87 | 0.00 |
| Block-all | 0.098742 | 22463.00 | -18157.13 |
| Selected classifier + static 0.5 | 0.018737 | 4262.45 | 43.42 |
| Cost-sensitive policy | 0.007491 | 1704.17 | 2601.71 |

## Ranking metrics (on the policy's scores)

| Budget | Precision | Recall |
|---|---:|---:|
| @1%  | 0.2431 | 0.1933 |
| @5%  | 0.1189 | 0.4729 |
| @10% | 0.0775 | 0.6162 |

## Calibration

- Brier score: **0.011506**
- ROC-AUC (informational only): 0.8753

## Action distribution

- `approve`: 205,395
- `review`: 21,371
- `block`: 725

## Interpretation

The cost-sensitive policy achieves **0.007491** cost per transaction. The strongest non-policy baseline is **Selected classifier + static 0.5** at **0.018737**.
**Result:** the policy does beat the strongest baseline on realized cost per transaction under the same split, delay regime, and cost matrix.

## Limitations

- Single delay regime (1 month).
- Amount-scaled `fraud_loss` uses `amount_proxy = proposed_credit_limit`.
- BAF is synthetic data; results are not production estimates.
- Censored labels are excluded, not modelled.
- No hyperparameter tuning, no calibration step, no capacity constraint.
