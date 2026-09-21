# Bootstrap Confidence Intervals

## Pre-registered stop criterion

Success: the 95% CI on the difference (baseline − policy) excludes zero.
Null: the CI includes zero.

Resampling: 1000 iterations, seed=42, n=227,491

| Quantity | Point estimate | 95% CI |
|---|---:|---|
| Policy cost/txn | 0.007566 | [0.007277, 0.007874] |
| LightGBM + 0.5 cost/txn | 0.017543 | [0.016732, 0.018336] |
| Difference (baseline − policy) | 0.009977 | [0.009257, 0.010686] |
| Advantage (%) | 56.87% | [52.77%, 60.91%] |

**Difference CI excludes zero:** True
