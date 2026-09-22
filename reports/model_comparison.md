# Model Comparison: Primary 3-Algorithm Study

- CV strategy: 5-fold expanding-window by month (train months 0..k, validate month k+1)
- Training rows: 794,989
- Fraud rate: 1.0253%

## Hyperparameters

| Algorithm | Configuration |
|---|---|
| logistic_regression | `{'C': 1.0, 'class_weight': 'balanced', 'max_iter': 1000}` |
| random_forest | `{'n_estimators': 200, 'class_weight': 'balanced_subsample', 'n_jobs': -1, 'random_state': 42}` |
| lightgbm | `{'n_estimators': 300, 'verbose': -1, 'random_state': 42}` |

No hyperparameter tuning was performed. One fixed configuration per algorithm, identical across all folds, was used so the comparison is fair and reproducible (see `docs/evaluation_protocol.md` §4.4).

## Cross-Validation Results

| Algorithm | Macro F1 (mean ± SD) | Accuracy | Precision (fraud) | Recall (fraud) | F1 (fraud) | Precision (legit) | Recall (legit) | F1 (legit) | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|
| logistic_regression | 0.4783 ± 0.0201 | 0.7916 | 0.0392 | 0.7993 | 0.0744 | 0.9974 | 0.7916 | 0.8822 | 0.8792 |
| random_forest | 0.4977 ± 0.0004 | 0.9899 | 0.1400 | 0.0003 | 0.0006 | 0.9899 | 1.0000 | 0.9949 | 0.8386 |
| lightgbm | 0.5337 ± 0.0100 | 0.9891 | 0.2666 | 0.0430 | 0.0729 | 0.9903 | 0.9988 | 0.9945 | 0.8804 |

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
| precision_legit | 0.9865309334024055 |
| recall_legit | 0.9986543513429277 |
| f1_legit | 0.9925556238475722 |
| roc_auc | 0.8765865003180965 |

Confusion matrix (rows=true, cols=pred): `[[201861, 272], [2756, 122]]`

## Selection Justification

**lightgbm** achieved the highest mean CV Macro F1 among the three algorithms. Macro F1 was chosen as the primary metric because the dataset is heavily imbalanced (~1.1% fraud) and both false positives and false negatives carry real operational cost (see `docs/evaluation_protocol.md` §4.5). Interpretability, training speed, and practical suitability were considered as tiebreakers; no tiebreak was needed.

## Failure Analysis

Test-set counts: TN=201861, FP=272, FN=2756, TP=122. The dominant error type is false negatives (2756 vs 272). At the default 0.5 threshold the model is conservative: it rarely flags fraud, so recall on the fraud class is low. This is expected for an imbalanced problem and is addressed operationally by the cost-sensitive policy in the Streamlit app, which uses derived thresholds far below 0.5 rather than a fixed 0.5 cut (see `docs/decision_policy.md`).
