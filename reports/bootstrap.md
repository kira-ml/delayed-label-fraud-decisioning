# Bootstrap Confidence Intervals

## Pre-registered stop criterion

Success: the 95% CI on the difference (baseline − policy) excludes zero.
Null: the CI includes zero.

Resampling: 1000 iterations, seed=42, n=227,491

| Quantity | Point estimate | 95% CI |
|---|---:|---|
| Policy cost/txn | 0.007621 | [0.007331, 0.007918] |
| LightGBM + 0.5 cost/txn | 0.017749 | [0.016918, 0.018619] |
| Difference (baseline − policy) | 0.010128 | [0.009436, 0.010869] |
| Advantage (%) | 57.06% | [53.16%, 61.24%] |

**Difference CI excludes zero:** True
