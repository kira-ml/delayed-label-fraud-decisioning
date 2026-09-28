# Bootstrap Confidence Intervals

## Pre-registered stop criterion

Success: the 95% CI on the difference (baseline − policy) excludes zero.
Null: the CI includes zero.

Resampling: 1000 iterations, seed=42, n=227,491

| Quantity | Point estimate | 95% CI |
|---|---:|---|
| Policy cost/txn | 0.007491 | [0.007196, 0.007797] |
| LGBM+0.5 cost/txn | 0.017798 | [0.016967, 0.018670] |
| Difference (baseline − policy) | 0.010307 | [0.009602, 0.011058] |
| Advantage (%) | 57.91% | [53.95%, 62.13%] |

**Difference CI excludes zero:** True
