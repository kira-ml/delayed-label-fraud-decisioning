# MVP Backtest Report

_Generated: 2026-09-22 10:58:08 UTC_

## Setup

- Dataset: BAF `Base.csv`
- Delay regime: 1 month (`label_month = month + 1`)
- Split: train months {0,1,2}, val {3,4}, test {5,6}
- Model: LightGBM binary classifier, library defaults, early stopping on val
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
| LightGBM + static 0.5 | 0.017749 | 4037.76 | 268.12 |
| Cost-sensitive policy | 0.007621 | 1733.77 | 2572.10 |

## Ranking metrics (on the policy's scores)

| Budget | Precision | Recall |
|---|---:|---:|
| @1%  | 0.2316 | 0.1842 |
| @5%  | 0.1182 | 0.4701 |
| @10% | 0.0795 | 0.6323 |

## Calibration

- Brier score: **0.011832**
- ROC-AUC (informational only): 0.8821

## Action distribution

- `approve`: 206,276
- `review`: 19,473
- `block`: 1,742

## Interpretation

The cost-sensitive policy achieves **0.007621** cost per transaction. The strongest non-policy baseline is **LightGBM + static 0.5** at **0.017749**.
**Result:** the policy does beat the strongest baseline on realized cost per transaction under the same split, delay regime, and cost matrix.

## Limitations

- Single delay regime (1 month).
- Amount-scaled `fraud_loss` uses `amount_proxy = proposed_credit_limit`.
- BAF is synthetic data; results are not production estimates.
- Censored labels are excluded, not modelled.
- No hyperparameter tuning, no calibration step, no capacity constraint.
