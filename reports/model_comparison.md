# Model Comparison: Primary 3-Algorithm Study

- CV strategy: 5-fold `TimeSeriesSplit`
- Training rows: 794,989
- Fraud rate: 1.0253%

## Cross-Validation Results

| Algorithm | Macro F1 (mean ± SD) | Accuracy | Precision (fraud) | Recall (fraud) | ROC-AUC |
|---|---|---|---|---|---|
| logistic_regression | 0.4773 ± 0.0186 | 0.7900 | 0.0386 | 0.8028 | 0.8792 |
| random_forest | 0.4975 ± 0.0003 | 0.9900 | 0.0000 | 0.0000 | 0.8414 |
| lightgbm | 0.5344 ± 0.0139 | 0.9890 | 0.2426 | 0.0450 | 0.8802 |

## Final Test Results

Selected algorithm: **lightgbm**

| Metric | Value |
|---|---|
| algorithm | lightgbm |
| macro_f1 | 0.5335638754934683 |
| accuracy | 0.9852300608260045 |
| precision_fraud | 0.3096446700507614 |
| recall_fraud | 0.0423905489923558 |
| f1_fraud | 0.0745721271393643 |
| roc_auc | 0.8765865003180965 |

Confusion matrix (rows=true, cols=pred): `[[201861, 272], [2756, 122]]`
