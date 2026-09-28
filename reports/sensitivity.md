# Cost Sensitivity Analysis

## Pre-registered stop criterion

Success: the policy remains the lowest-cost action at every variation.
Null: the policy's advantage over the strongest baseline drops below 5%
relative at any variation.

Base config: `{'fraud_loss': 1.0, 'false_positive_cost': 0.1, 'review_cost': 0.02, 'residual_fraud_loss': 0.3, 'amount_scaled': True, 'fraud_loss_rate': 0.0019187869}`

| Config                       |    Policy | Strongest base |      Cost |      Adv |
|------------------------------|-----------|----------------|-----------|----------|
| baseline                     | 0.007491 | LGBM+0.5       | 0.017798 |   57.91% |
| false_positive_cost=0.05     | 0.007037 | LGBM+0.5       | 0.017752 |   60.36% |
| false_positive_cost=0.2      | 0.007625 | LGBM+0.5       | 0.017890 |   57.38% |
| review_cost=0.01             | 0.006253 | LGBM+0.5       | 0.017798 |   64.87% |
| review_cost=0.04             | 0.009298 | LGBM+0.5       | 0.017798 |   47.76% |
| residual_fraud_loss=0.15     | 0.006588 | LGBM+0.5       | 0.017798 |   62.99% |
| residual_fraud_loss=0.6      | 0.008700 | LGBM+0.5       | 0.017798 |   51.12% |

One-at-a-time variation. Amount scaling is held fixed at the train-calibrated rate. Decisions are recomputed at each setting; the model is not retrained.