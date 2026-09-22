# Cost Sensitivity Analysis

## Pre-registered stop criterion

Success: the policy remains the lowest-cost action at every variation.
Null: the policy's advantage over the strongest baseline drops below 5%
relative at any variation.

Base config: `{'fraud_loss': 1.0, 'false_positive_cost': 0.1, 'review_cost': 0.02, 'residual_fraud_loss': 0.3, 'amount_scaled': True, 'fraud_loss_rate': 0.0019187869}`

| Config                       |    Policy | Strongest base |      Cost |      Adv |
|------------------------------|-----------|----------------|-----------|----------|
| baseline                     | 0.007621 | LightGBM+0.5   | 0.017749 |   57.06% |
| false_positive_cost=0.05     | 0.007087 | LightGBM+0.5   | 0.017686 |   59.93% |
| false_positive_cost=0.2      | 0.007858 | LightGBM+0.5   | 0.017875 |   56.04% |
| review_cost=0.01             | 0.006294 | LightGBM+0.5   | 0.017749 |   64.54% |
| review_cost=0.04             | 0.009396 | LightGBM+0.5   | 0.017749 |   47.06% |
| residual_fraud_loss=0.15     | 0.006677 | LightGBM+0.5   | 0.017749 |   62.38% |
| residual_fraud_loss=0.6      | 0.008850 | LightGBM+0.5   | 0.017749 |   50.14% |

One-at-a-time variation. Amount scaling is held fixed at the train-calibrated rate. Decisions are recomputed at each setting; the model is not retrained.