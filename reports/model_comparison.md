# Model Comparison: Primary 3-Algorithm Study

- CV strategy: 5-fold `TimeSeriesSplit`
- Training rows: 794,989
- Fraud rate: 1.0253%

## Cross-Validation Results

| Algorithm | Macro F1 (mean ± SD) | Accuracy | Precision (fraud) | Recall (fraud) | ROC-AUC |
|---|---|---|---|---|---|
| logistic_regression | 0.4773 ± 0.0186 | 0.7900 | 0.0386 | 0.8028 | 0.8792 |
| random_forest | 0.4975 ± 0.0003 | 0.9900 | 0.0000 | 0.0000 | 0.8414 |
| lightgbm | 0.5249 ± 0.0142 | 0.8935 | 0.0592 | 0.6121 | 0.8606 |

## Final Test Results

Selected algorithm: **lightgbm**

| Metric | Value |
|---|---|
| algorithm | lightgbm |
| macro_f1 | 0.5186318317119464 |
| accuracy | 0.8488325016706421 |
| precision_fraud | 0.06531218109286575 |
| recall_fraud | 0.7338429464906184 |
| f1_fraud | 0.11994888541814568 |
| roc_auc | 0.8747957291909857 |

Confusion matrix (rows=true, cols=pred): `[[171908, 30225], [766, 2112]]`
