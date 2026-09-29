# 3. METHODOLOGY

> **Repository:** `delayed-label-fraud-decisioning`
> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Document:** Section 3 draft — Methodology
> **Status:** draft — consistent with `decision_policy.md` v1.0, `evaluation_protocol.md` v1.0, and `src/**`
> **Last updated:** 2026-09-29

> **How to use this draft:** The prose is done. Do not add bullets — the
> IEEE sample uses prose. Subsections follow the sample's `A.` / `B.` /
> `C.` convention. Every formula below matches `docs/decision_policy.md`
> §5 and §7 and the as-built implementation in `src/policy/decide.py`.

---

This section describes the decision policy that is the object of study,
the cost matrix it consumes, the three classifiers that are compared as
policy inputs, the preprocessing applied to each, the hyperparameter
search procedure, and the calibration gate that a classifier must pass
before it can feed the policy. The framing is decision-centric: the
classifier is an input to the policy, and the policy is the product.

## A. Decision Formulation

At decision time, the system must choose one of three actions for each
transaction: `approve`, `review`, or `block`. Three actions are used
because approve and block alone ignore manual review, which is where most
operational fraud decisioning lives, and because a three-action
formulation exposes the review-cost tradeoff directly. For a transaction
with predicted fraud probability `p = P(fraud | X_t)`, the policy computes
the expected cost of each action and selects the minimum:

```text
E[cost(approve)] = p * fraud_loss(amount)
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action* = argmin over {approve, review, block} of E[cost(action)]
```

The argmin rule is the source of truth. Two thresholds on `p` can be
derived from the cost matrix as a diagnostic view, but they are not the
implementation. Under amount scaling, the review threshold becomes
per-row, and the fixed-threshold view no longer describes the policy's
behavior. The argmin is always well-defined, including in the degenerate
cases where the thresholds collapse or fall outside `[0, 1]`; these edge
cases are covered by unit tests in `tests/test_policy.py`.

## B. Cost Matrix and Amount Scaling

All cost inputs are frozen in `configs/costs.yaml` before any modeling
begins and are never tuned on validation or test data. The values are:

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: true
fraud_loss_rate: 0.0019187869
```

The constant-loss matrix treats fraud loss as a fixed quantity of 1.0. This
is a simplification: a fraudulent transaction of 10,000 pesos costs more
than one of 10 pesos. The policy therefore supports amount-scaled fraud
loss, in which the fraud-loss term becomes per-row:

```text
fraud_loss(amount) = amount * fraud_loss_rate
```

The rate is calibrated from training-window amounts only:

```text
fraud_loss_rate = 1 / mean(amount_proxy on train)
                = 1 / 521.1626
                = 0.0019187869
```

This keeps the mean of `fraud_loss_rate * amount_proxy` equal to 1.0 on
the training window, matching the constant-loss comparison scale, without
using any test-window information. The amount column used is
`amount_proxy`, which is derived from `proposed_credit_limit` in the Bank
Account Fraud dataset; a true transaction-amount column is not available,
and this is documented as a limitation. Amount scaling changes the
decision for a small fraction of rows — under the current build, about
2.4% of the test window — but that minority carries disproportionate cost,
and the policy's expected-cost minimization correctly routes it.

The `false_positive_cost` is treated as constant in the current build.
It is plausibly proportional to transaction amount in reality, but this
extension is out of scope and is named as future work in the limitations.

## C. The Three Classifiers

Three traditional classifiers are compared as policy inputs. The choice of
these three — and not others — reflects the course requirement to compare
exactly three traditional algorithms and the domain-appropriate assumption
that tabular fraud data is best served by linear baselines and tree
ensembles rather than deep architectures.

**Logistic Regression** is included as a linear, interpretable baseline.
Its coefficients are directly readable, it trains quickly, and it
calibrates well by construction when the log-odds model is roughly
correct. Configuration: `C = 10.0`, `max_iter = 1000`.

**Random Forest** is included as a non-linear ensemble. It handles mixed
feature types and interactions without explicit feature engineering and is
robust to outliers. Configuration: `n_estimators = 400`, `n_jobs = -1`,
`random_state = 42`.

**LightGBM** is included as a gradient-boosting method with strong
performance on tabular data and native support for categorical features.
Configuration: `n_estimators = 300`, `learning_rate = 0.05`,
`verbose = -1`, `random_state = 42`.

No class weighting is applied to any classifier. The decision policy
assumes `p_fraud` is a calibrated probability, and reweighting to correct
for class imbalance would distort that probability. Cost asymmetry is
handled by the policy, not by the training objective. No resampling is
applied for the same reason.

## D. Preprocessing

Preprocessing is fit within each training fold and applied unchanged to
the corresponding validation and test data. The transformation differs by
classifier:

**Logistic Regression** uses StandardScaler on numeric features and
one-hot encoding on the five categorical features (`payment_type`,
`employment_status`, `housing_status`, `source`, `device_os`). The one-hot
encoder is configured with `handle_unknown="ignore"` so that unseen
categories at inference time do not raise.

**Random Forest** uses no scaling and ordinal encoding on categorical
features with `handle_unknown="use_encoded_value"` and
`unknown_value=-1`. This preserves tree-split semantics without inflating
the feature dimension.

**LightGBM** uses native categorical handling via pandas `category`
dtype. The category mapping is captured during training and reapplied at
inference, so validation and test data cannot introduce categories the
model has not seen.

Eight columns are excluded from all classifiers: `transaction_id`,
`fraud_bool`, `month`, `label_month`, `observed`, `amount_proxy`,
`proposed_credit_limit`, and `device_fraud_count`. The exclusion list is
enforced in code (`FEATURE_EXCLUDE` in `src/common.py`) and verified by
tests. The rationale for each exclusion is documented in
`docs/data_card.md` §4.2 and `documentation/data_dictionary.md` §5. The
result is a 28-feature input: 23 numeric and 5 categorical.

## E. Hyperparameter Search

Hyperparameter selection is performed by expanding-window cross-validation
on the training window. Each fold uses contiguous months for training and
the next month for validation; no shuffling occurs and no fold mixes time
boundaries. On the current training window (months 0–2), this yields two
folds. Preprocessing is refit within each fold's training portion.

For each classifier, a small grid of configurations is evaluated on the
same folds. Logistic Regression tests four values of the regularization
strength `C` in `{0.01, 0.1, 1.0, 10.0}` with `max_iter = 1000` fixed.
Random Forest tests three forest sizes `n_estimators` in
`{100, 200, 400}`. LightGBM tests four combinations of `n_estimators`
in `{100, 300, 500}` and `learning_rate` in `{0.10, 0.05}`. The selected
configuration per classifier is the one with the lowest mean realized
cost after the policy across folds.

The selection criterion is **realized cost after the policy**, not a
classification metric. A classifier that ranks better but produces worse
policy cost is not selected. Classification metrics — macro F1, accuracy,
per-class precision, recall, F1, ROC-AUC — are recorded for all three
classifiers side by side as supporting evidence, but they do not decide
the selection.

The selection is subject to a pre-registered noise-band guard. The top
classifier must win every fold **and** the relative gap to the runner-up
must exceed 5%. If either condition fails, the comparison is reported as
a non-finding, and the tie is broken in favor of the simplest classifier
under the ordering Logistic Regression > Random Forest > LightGBM. This
guard prevents the paper from claiming a ranking that is indistinguishable
from noise.

## F. Calibration Gate

The decision policy assumes `p` is a probability: expected costs are
linear in `p`, and a score that is not a probability produces wrong
expected costs and therefore wrong actions. A calibration gate is
therefore enforced before any classifier can be admitted as a policy
input. The gate requires an Expected Calibration Error (ECE) below 0.05
on the validation window, computed over 10 quantile bins.

If a classifier passes the gate, no calibration step is applied and its
raw output is used by the policy. If a classifier fails, exactly one
calibration method (Platt scaling or isotonic regression) is fit on
validation and re-measured. If the calibrated ECE drops below the gate,
the classifier remains admissible; otherwise it is rejected. Only one
calibration attempt is permitted per classifier. Calibration is never fit
on the test window.

In the current build, all three classifiers pass the gate without a
calibration step, so the policy consumes raw classifier output directly.
The reliability table for the selected classifier is well-calibrated
across the majority of the score range, mildly overconfident only in the
top decile — a region whose scores fall inside the review band and do not
affect block decisions.

## G. Evaluation Criterion

The classifier is selected by realized cost after the policy on the
validation window, following the same cost matrix and the same delay
regime as the final test evaluation. The selected classifier is retrained
on the full training window and evaluated once on the untouched test
window (months 5–6). The test window is used exactly once. All model
selection, threshold diagnostics, and calibration checks happen before
that evaluation; nothing is tuned on the test window.

This methodology section describes the framing and the procedure. The
results it produces — the classifier comparison, the selected classifier,
the policy cost on the test window, the bootstrap confidence interval,
and the sensitivity sweep minimum — are reported in Section 6.

---

## Notes for the Paper Team

- Every formula above matches `docs/decision_policy.md` §5 and §7 and
  `src/policy/decide.py`.
- Every hyperparameter value matches `src/models/train_compare.py`
  `PARAM_GRIDS` and `reports/model_comparison.md`.
- Every preprocessing rule matches `src/models/preprocess.py` and
  `docs/data_card.md` §10.
- The calibration gate is `evaluation_protocol.md` §7; the noise-band
  guard is `evaluation_protocol.md` §8 and §17.1.
- Do not add "no hyperparameter tuning" — this is false and was already
  corrected in `reports/decision_backtest.md`.
- Do not present the derived thresholds in §A as the decision rule; the
  argmin is the rule and the thresholds are diagnostic.
- Do not count hyperparameter variants as distinct algorithms; the three
  algorithms are LR, RF, and LGBM.
- This section has no citations to add; all content is project-internal.
  If the paper team wants a citation for the argmin rule or the cost
  framework, use [2] from `paper/references.md` (Elkan 2001) in §A.
