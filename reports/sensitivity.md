# Cost Sensitivity Analysis

## Pre-registered stop criterion

Success: the policy remains the lowest-cost action at every variation.
Null: the policy's advantage over the strongest baseline drops below 5%
relative at any variation.

Base config: `{'fraud_loss': 1.0, 'false_positive_cost': 0.1, 'review_cost': 0.02, 'residual_fraud_loss': 0.3, 'amount_scaled': True, 'fraud_loss_rate': 0.0019187869}`

| Config                       |    Policy | Strongest base |      Cost |      Adv |
|------------------------------|-----------|----------------|-----------|----------|
| baseline                     | 0.007491 | Classifier+0.5 | 0.018737 |   60.02% |
| false_positive_cost=0.05     | 0.007037 | Classifier+0.5 | 0.018736 |   62.44% |
| false_positive_cost=0.2      | 0.007625 | Classifier+0.5 | 0.018739 |   59.31% |
| review_cost=0.01             | 0.006253 | Classifier+0.5 | 0.018737 |   66.63% |
| review_cost=0.04             | 0.009298 | Classifier+0.5 | 0.018737 |   50.38% |
| residual_fraud_loss=0.15     | 0.006588 | Classifier+0.5 | 0.018737 |   64.84% |
| residual_fraud_loss=0.6      | 0.008700 | Classifier+0.5 | 0.018737 |   53.57% |

One-at-a-time variation. Amount scaling is held fixed at the train-calibrated rate. Decisions are recomputed at each setting; the model is not retrained.