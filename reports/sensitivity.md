# Cost Sensitivity Analysis

## Pre-registered stop criterion

Success: the policy remains the lowest-cost action at every variation.
Null: the policy's advantage over the strongest baseline drops below 5%
relative at any variation.

Base config: `{'fraud_loss': 1.0, 'false_positive_cost': 0.1, 'review_cost': 0.02, 'residual_fraud_loss': 0.3, 'amount_scaled': True, 'fraud_loss_rate': 0.0019187869}`

| Config                       |    Policy | Strongest base |      Cost |      Adv |
|------------------------------|-----------|----------------|-----------|----------|
| baseline                     | 0.007566 | LightGBM+0.5   | 0.017543 |   56.87% |
| false_positive_cost=0.05     | 0.007055 | LightGBM+0.5   | 0.017480 |   59.64% |
| false_positive_cost=0.2      | 0.007845 | LightGBM+0.5   | 0.017670 |   55.60% |
| review_cost=0.01             | 0.006217 | LightGBM+0.5   | 0.017543 |   64.56% |
| review_cost=0.04             | 0.009393 | LightGBM+0.5   | 0.017543 |   46.46% |
| residual_fraud_loss=0.15     | 0.006644 | LightGBM+0.5   | 0.017543 |   62.13% |
| residual_fraud_loss=0.6      | 0.008783 | LightGBM+0.5   | 0.017543 |   49.94% |

One-at-a-time variation. Amount scaling is held fixed at the train-calibrated rate. Decisions are recomputed at each setting; the model is not retrained.