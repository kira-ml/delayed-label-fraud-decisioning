# Model Comparison: Primary 3-Algorithm Study

- CV strategy: 2-fold expanding-window by month (train months 0..k, validate month k+1)
- Training rows: 397,039
- Fraud rate: 0.9813%

## Hyperparameters

| Algorithm | Configuration |
|---|---|
| logistic_regression | `{'C': 10.0, 'max_iter': 1000}` |
| random_forest | `{'n_estimators': 400, 'n_jobs': -1, 'random_state': 42}` |
| lightgbm | `{'n_estimators': 300, 'learning_rate': 0.05, 'verbose': -1, 'random_state': 42}` |

Each algorithm's configuration was selected by mean realized cost across the expanding-window folds. All configurations within an algorithm were evaluated on the same folds with the same preprocessing, so the selection is fair and reproducible (see `docs/evaluation_protocol.md` §4.4 and §8).

## Selection Criterion: Realized Cost After the Policy

| Algorithm | Realized cost/txn (mean ± SD) |
|---|---|
| logistic_regression | 0.005915 ± 0.000338 |
| random_forest | 0.006515 ± 0.000579 |
| lightgbm | 0.005852 ± 0.000300 |

Lowest mean realized cost wins. Classification metrics below are supporting evidence, not the criterion (see `docs/evaluation_protocol.md` §8 and §11).

## Cross-Validation Results

| Algorithm | Macro F1 (mean ± SD) | Accuracy | Precision (fraud) | Recall (fraud) | F1 (fraud) | Precision (legit) | Recall (legit) | F1 (legit) | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|
| logistic_regression | 0.5043 ± 0.0025 | 0.9909 | 0.4700 | 0.0067 | 0.0131 | 0.9910 | 0.9999 | 0.9954 | 0.8669 |
| random_forest | 0.4977 ± 0.0001 | 0.9909 | 0.0000 | 0.0000 | 0.0000 | 0.9909 | 1.0000 | 0.9954 | 0.8307 |
| lightgbm | 0.5215 ± 0.0017 | 0.9906 | 0.3074 | 0.0259 | 0.0477 | 0.9912 | 0.9995 | 0.9953 | 0.8746 |

## Final Test Results

Selected algorithm: **logistic_regression**

### Primary: Realized cost of the policy

| Metric | Value |
|---|---|
| realized_cost_per_txn | 0.0074911340788031185 |
| total_realized_cost | 1704.1655827210002 |
| action_approve | 205395 |
| action_review | 21371 |
| action_block | 725 |
| policy_recall | 0.5050681579867179 |
| policy_precision | 0.06539645184648805 |
| precision_at_1pct | 0.24307692307692308 |
| recall_at_1pct | 0.19328905976931143 |
| precision_at_5pct | 0.11894505494505495 |
| recall_at_5pct | 0.4729115693813352 |
| precision_at_10pct | 0.0774945054945055 |
| recall_at_10pct | 0.6162181055574973 |

### Supporting: Classification behavior at the 0.5 cut

| Metric | Value |
|---|---|
| algorithm | logistic_regression |
| macro_f1 | 0.503091571918646 |
| accuracy | 0.9874808234171901 |
| precision_fraud | 0.782608695652174 |
| recall_fraud | 0.006291506466270535 |
| f1_fraud | 0.012482662968099861 |
| precision_legit | 0.9875015386779679 |
| recall_legit | 0.9999777411743757 |
| f1_legit | 0.993700480869192 |
| roc_auc | 0.8752966122720927 |

Confusion matrix (rows=true, cols=pred): `[[224625, 5], [2843, 18]]`

## Selection Justification

**logistic_regression** is the selection after the noise-band guard in `docs/evaluation_protocol.md` v1.0 §17.1. The top two classifiers were within the pre-registered 5% effect-size threshold, so the CV comparison is reported as a **non-finding** and the tie is broken by simplicity (LR > RF > LGBM), per §8. The test-window result for the selected classifier is reported once, below, as required by the evaluation protocol.

## Failure Analysis

Test-window counts at the classifier's 0.5 cut: TN=224625, FP=5, FN=2843, TP=18. The 0.5 cut is not the operating point of the deployed system. The primary system is the decision policy, which routes each transaction to approve / review / block by expected cost and is evaluated in the Primary table above. See `docs/decision_policy.md` §5 for the policy and `docs/evaluation_protocol.md` §10 for the metric definition.
