# Cost-Sensitive Fraud Decisioning Under Delayed and Censored Labels: A Temporal Backtest on the Bank Account Fraud Dataset

> **Repository:** `delayed-label-fraud-decisioning`
> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Document:** Master IMRaD draft (IEEE format)
> **Status:** assembled draft — the source DOCX and PDF are generated from this file
> **Last updated:** 2026-09-29

> **Assembly notes for the paper team:**
>
> - This file is the master draft. `paper/paper.docx` and `paper/paper.pdf`
>   are generated from it.
> - The `[Full name of each member]` and `[email addresses]` placeholders
>   must be filled before submission.
> - The `[STATISTIC NEEDED — ...]` placeholders in Section 1 must be
>   filled with real BSP or industry statistics before submission. Do not
>   invent numbers.
> - Citations use the seed numbers from `paper/references.md`. Final
>   numbering is set during assembly by the order of first in-text
>   appearance. If the paper team adds or removes a citation, renumber the
>   reference list to match.
> - Every number in this document must appear in
>   `docs/paper/reference_sheet.md` §1. If any is missing from the sheet,
>   add it to the sheet first, then cite it here.
> - Do not add bullet lists in the body. Tables and figures only. The IEEE
>   sample uses prose.

---

## Authors

[Full name of each member]  
College of Computing and Information Technologies  
National University Philippines  
Manila, Philippines  
[email addresses]

---

## Abstract

Fraud detection systems must decide whether to approve, review, or block a
transaction in real time, yet fraud labels arrive weeks to months later and
are frequently censored before the evaluation window closes. We frame this
as a cost-sensitive decision problem rather than a classification problem
and evaluate it under a temporal backtest on the Bank Account Fraud (BAF)
dataset with a simulated one-month label delay. A Logistic Regression
classifier feeding an argmin-of-expected-cost policy reduces realized cost
per transaction by 57.91% relative to the strongest baseline, LightGBM +
static 0.5 at 0.017798, with a 95% bootstrap confidence interval of
[53.95%, 62.13%]. The result is robust to a 2× variation in each cost
parameter and does not depend on test-set tuning: the cost rate is derived
from training-window amounts only. We report censored-label counts (96,843
of 1,000,000, or 9.68%) rather than treating unobserved fraud as
legitimate, and we release the full evaluation protocol alongside the
pipeline. The paper contributes a reproducible template for evaluating
fraud decision policies under delayed and partial labels, and demonstrates
that static thresholds on imbalanced data behave near-identically to
approve-all even when the underlying model is well-calibrated. Limitations
include a single delay regime, a synthetic dataset, and an amount proxy
derived from proposed credit limit.

**Index Terms** — Cost-sensitive learning, fraud detection, delayed
feedback, censored labels, decision policy, temporal backtest,
Logistic Regression, Bank Account Fraud dataset, expected-cost
minimization, false-positive cost, bootstrap confidence intervals,
sensitivity analysis, machine learning.

---

# 1. INTRODUCTION

Digital payment systems in the Philippines process millions of
transactions every day. According to the Bangko Sentral ng Pilipinas
(BSP), the share of digital payments in total retail payment volume rose
from [STATISTIC NEEDED — BSP Digital Payments Transformation Roadmap
2020–2023 reports ~42% in 2023], with the total value of digital
transactions exceeding [STATISTIC NEEDED — BSP e-payments report]. This
growth has brought fraud into closer view: the BSP received
[STATISTIC NEEDED — BSP Consumer Affairs Group complaint statistics]
fraud-related consumer complaints in [YEAR], of which unauthorized
transactions accounted for the largest share [1]. For banks, issuers,
merchants, and their customers, the operational question is not whether a
transaction is fraudulent in hindsight but whether to approve, review, or
block it *before* the label arrives.

The fraud label itself is the core difficulty. When a customer's card is
used without authorization, the loss is not confirmed at the moment of the
transaction — it is confirmed weeks to months later, when the customer
files a dispute, the merchant responds, and the chargeback is resolved.
Industry dispute windows commonly run 30 to 120 days. On real-time payment
rails such as InstaPay and PESONet, funds may become irrevocable before
fraud is confirmed. A machine-learning model trained on settled disputes
therefore learns from a label that arrives late — and worse, from a label
that may never arrive at all, because some fraud goes unreported, some
disputes are resolved in the merchant's favor, and some victims do not
notice [3].

Most published work in fraud detection treats the problem as binary
classification and reports ranking metrics such as area under the ROC
curve (AUC) or area under the precision-recall curve (PR-AUC). These
metrics are useful for comparing models on a fixed labeled dataset, but
they do not answer the operational question a bank actually faces: given
the model's score, should this transaction be approved, reviewed, or
blocked, and what is the realized cost of that decision? On a dataset
where fraud is roughly 1% of transactions, a high AUC can coexist with a
policy that barely improves on approving everything.

This paper takes a different framing. We treat fraud detection as a
one-step decision problem under delayed, partial, and asymmetric-cost
feedback. The model produces a fraud probability, but the system under
evaluation is the *policy* that maps that probability, the transaction
amount, and a fixed cost matrix into one of three actions. The policy
chooses the action that minimizes expected cost. This is not a novel
policy — expected-cost minimization is standard in cost-sensitive
learning [2] — but it is rarely evaluated end-to-end on a fraud dataset
with simulated label delay, censored labels reported rather than hidden,
and statistical rigor on the primary metric.

We evaluate this framing on the Bank Account Fraud (BAF) dataset, a
public 1-million-row synthetic benchmark designed for fraud research [4].
Because BAF provides only month-level time granularity, we simulate a
one-month label delay and hold out the final month as censored. We
compare a cost-sensitive policy against six baselines under an identical
temporal split and cost matrix, report realized cost per transaction as
the primary metric, and test the result's robustness with a 2× sensitivity
analysis on each cost parameter and a bootstrap confidence interval.

The main findings are as follows. First, the cost-sensitive policy reduces
realized cost per transaction by **57.91%** relative to the strongest
baseline (LightGBM + static 0.5), with a 95% bootstrap confidence interval
of **[53.95%, 62.13%]**. Second, the static threshold performs
*near-identically to approve-all* (5.97% reduction), a failure mode that
AUC-based evaluation would not reveal. Third, the result is robust across
a 2× range on each of three cost parameters; the minimum advantage across
all variations is 47.76%. Fourth, the cost rate used for amount scaling is
derived from training-window amounts only, so the headline result does not
depend on any test-set tuning.

This paper makes three contributions. It contributes a reproducible
evaluation protocol for fraud decision policies under delayed and
censored labels, including pre-registered stop criteria and an explicit
prohibition on random splits. It contributes a temporal backtest on BAF
with six canonical baselines, censored-label reporting, cost sensitivity,
and bootstrap confidence intervals. And it contributes a documented
negative result at the framing level: static thresholds on highly
imbalanced fraud data are not decision rules, and reporting them without a
cost anchor overstates model performance.

The remainder of this paper is organized as follows. Section 2 reviews
related work in cost-sensitive learning, delayed feedback, and fraud
detection. Section 3 describes the decision policy and cost formulation.
Section 4 describes the BAF dataset, the delay simulation, and the
temporal split. Section 5 describes the experimental setup and baselines.
Section 6 presents results, sensitivity analysis, and confidence
intervals. Section 7 discusses what the results imply for real fraud
operations. Section 8 states the limitations. Section 9 concludes and
outlines future work.

---

# 2. RELATED WORK

Fraud decisioning sits at the intersection of three research traditions:
cost-sensitive learning, learning under delayed or partial feedback, and
imbalanced fraud detection. Each contributes a piece of the framing we
adopt, and each leaves a gap we address.

## A. Cost-Sensitive Learning

Cost-sensitive learning reframes classification around the asymmetric cost
of errors rather than the symmetric error rate [2]. Elkan formalized the
Bayes-optimal decision rule under an arbitrary cost matrix, showing that
the optimal threshold on the posterior probability is a function of the
cost ratio between false positives and false negatives, not a fixed value
like 0.5 [2]. The framework was later extended to settings where only
positive labels are observed and the unlabeled population must be modeled
explicitly [6]. In fraud detection the cost asymmetry is severe: approving
a fraudulent transaction exposes the issuer to the full fraud loss, while
blocking a legitimate one incurs customer friction and churn [2], [5]. A
classifier trained to optimize accuracy or F1 treats these errors as
symmetric and therefore selects the wrong operating point. This is the
foundation of our decision-centric framing: the classifier is an input to
a policy, and the policy chooses the action that minimizes expected cost.

## B. Learning Under Delayed and Partial Feedback

Chapelle modeled delayed feedback in display advertising as a survival
problem, using survival analysis to estimate the conversion rate under an
unknown delay distribution rather than assuming the label is either
present or absent [3]. The fraud setting shares the structural property —
a decision must be made before the outcome is known — but differs in that
fraud labels are frequently censored rather than merely delayed. When the
observation window closes before a chargeback resolves, the label is
missing, not negative [4]. Treating censored labels as negatives biases
the classifier toward under-detection and inflates apparent precision. We
therefore hold out the final month of the dataset as censored, exclude it
from training and evaluation, and report the censored count alongside
every result.

## C. Fraud Detection and Calibration

Dal Pozzolo et al. showed that probability calibration degrades under
severe class imbalance and that uncalibrated scores undermine any
downstream cost-sensitive threshold [5]. Their result matters directly for
us: the decision policy we evaluate consumes a calibrated fraud
probability, and the expected cost of each action is linear in that
probability. An uncalibrated score produces wrong expected costs, and
therefore wrong decisions. We treat calibration as a gate — ECE below 0.05
on the validation window — rather than a diagnostic. A classifier that
fails the gate is rejected as a policy input regardless of its ranking
performance.

## D. Benchmark Datasets for Fraud and Imbalanced Learning

The Bank Account Fraud (BAF) dataset was introduced by Jesus et al. as a
realistic, temporal, imbalanced benchmark for machine learning evaluation
[4]. It includes a month index that supports chronological splitting, a
mixed-type feature set that reflects real account-application data, and
documented biases that make it suitable for stress-testing evaluation
protocols rather than only ranking models. We use BAF's v1 dataset because
its month-level granularity supports a defensible delay simulation, its
fraud rate of approximately 1.1% forces the cost asymmetry to matter, and
its licence (CC BY 4.0) and citable source make our results reproducible.

## E. The Gap This Paper Fills

Existing work tends to evaluate either classifiers or policies, but rarely
both, and even more rarely under a simulated delay with censored labels
explicitly reported. Studies on imbalanced fraud data often optimize
ranking metrics without connecting them to an operational cost; studies on
cost-sensitive learning often assume the label is available at decision
time; studies on delayed feedback often focus on advertising, where the
delay distribution is well understood, rather than on fraud, where labels
are both late and frequently missing. We bridge these threads by
evaluating an argmin-of-expected-cost policy end-to-end on BAF under a
simulated one-month label delay, with censored labels counted rather than
hidden, with a pre-registered evaluation protocol, and with bootstrap
confidence intervals on the primary metric. The classifier is treated as
an input to the policy; the policy is the object of study.

---

# 3. METHODOLOGY

This section describes the decision policy that is the object of study,
the cost matrix it consumes, the three classifiers that are compared as
policy inputs, the preprocessing applied to each, the hyperparameter
search procedure, and the calibration gate that a classifier must pass
before it can feed the policy.

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

The argmin rule is the source of truth [2]. Two thresholds on `p` can be
derived from the cost matrix as a diagnostic view, but they are not the
implementation. Under amount scaling, the review threshold becomes
per-row, and the fixed-threshold view no longer describes the policy's
behavior. The argmin is always well-defined, including in the degenerate
cases where the thresholds collapse or fall outside `[0, 1]`; these edge
cases are covered by unit tests.

## B. Cost Matrix and Amount Scaling

All cost inputs are frozen before any modeling begins and are never tuned
on validation or test data. The values are `fraud_loss = 1.0`,
`false_positive_cost = 0.1`, `review_cost = 0.02`, and
`residual_fraud_loss = 0.3`. The constant-loss matrix treats fraud loss as
a fixed quantity of 1.0. This is a simplification: a fraudulent
transaction of 10,000 pesos costs more than one of 10 pesos. The policy
therefore supports amount-scaled fraud loss, in which the fraud-loss term
becomes per-row: `fraud_loss(amount) = amount * fraud_loss_rate`. The rate
is calibrated from training-window amounts only:
`fraud_loss_rate = 1 / mean(amount_proxy on train) = 1 / 521.1626 =
0.0019187869`. This keeps the mean of `fraud_loss_rate * amount_proxy`
equal to 1.0 on the training window, matching the constant-loss comparison
scale, without using any test-window information. The amount column used
is `amount_proxy`, which is derived from `proposed_credit_limit` in the
Bank Account Fraud dataset; a true transaction-amount column is not
available, and this is documented as a limitation.

## C. The Three Classifiers

Three traditional classifiers are compared as policy inputs. Logistic
Regression is included as a linear, interpretable baseline with
configuration `C = 10.0`, `max_iter = 1000`. Random Forest is included as
a non-linear ensemble with configuration `n_estimators = 400`,
`n_jobs = -1`, `random_state = 42`. LightGBM is included as a
gradient-boosting method with strong tabular performance and native
categorical handling, configured with `n_estimators = 300`,
`learning_rate = 0.05`, `verbose = -1`, `random_state = 42`. No class
weighting is applied to any classifier. The decision policy assumes
`p_fraud` is a calibrated probability, and reweighting to correct for
class imbalance would distort that probability. Cost asymmetry is handled
by the policy, not by the training objective.

## D. Preprocessing

Preprocessing is fit within each training fold and applied unchanged to
the corresponding validation and test data. Logistic Regression uses
StandardScaler on numeric features and one-hot encoding on the five
categorical features with `handle_unknown="ignore"`. Random Forest uses
no scaling and ordinal encoding with `handle_unknown="use_encoded_value"`
and `unknown_value=-1`. LightGBM uses native categorical handling via
pandas `category` dtype, with the category mapping captured during
training and reapplied at inference. Eight columns are excluded from all
classifiers: `transaction_id`, `fraud_bool`, `month`, `label_month`,
`observed`, `amount_proxy`, `proposed_credit_limit`, and
`device_fraud_count`. The result is a 28-feature input: 23 numeric and 5
categorical.

## E. Hyperparameter Search

Hyperparameter selection is performed by expanding-window
cross-validation on the training window. Each fold uses contiguous months
for training and the next month for validation; no shuffling occurs and no
fold mixes time boundaries. On the current training window (months 0–2),
this yields two folds. Preprocessing is refit within each fold's training
portion. Logistic Regression tests four values of `C` in
`{0.01, 0.1, 1.0, 10.0}`. Random Forest tests three forest sizes in
`{100, 200, 400}`. LightGBM tests four combinations of `n_estimators` in
`{100, 300, 500}` and `learning_rate` in `{0.10, 0.05}`. The selected
configuration per classifier is the one with the lowest mean realized
cost after the policy across folds. The selection is subject to a
pre-registered noise-band guard: the top classifier must win every fold
and the relative gap to the runner-up must exceed 5%. If either condition
fails, the comparison is reported as a non-finding and the tie is broken
in favor of the simplest classifier under the ordering Logistic Regression
> Random Forest > LightGBM.

## F. Calibration Gate

The decision policy assumes `p` is a probability: expected costs are
linear in `p`, and a score that is not a probability produces wrong
expected costs and therefore wrong actions. A calibration gate is
therefore enforced before any classifier can be admitted as a policy
input. The gate requires an Expected Calibration Error (ECE) below 0.05
on the validation window, computed over 10 quantile bins. If a classifier
passes the gate, no calibration step is applied. If it fails, exactly one
calibration method is fit on validation and re-measured. Calibration is
never fit on the test window.

## G. Evaluation Criterion

The classifier is selected by realized cost after the policy on the
validation window, following the same cost matrix and the same delay
regime as the final test evaluation. The selected classifier is retrained
on the full training window and evaluated once on the untouched test
window (months 5–6). The test window is used exactly once. All model
selection, threshold diagnostics, and calibration checks happen before
that evaluation; nothing is tuned on the test window.

---

# 4. DATASET AND PREPROCESSING

## A. Dataset

The Bank Account Fraud (BAF) Suite, version 1, is a public 1-million-row
synthetic benchmark introduced by Jesus et al. for machine learning
evaluation under realistic fraud conditions [4]. The dataset has 32 raw
columns including the binary target `fraud_bool`, a month index ranging
from 0 to 7, and a mix of numeric, categorical, and binary features
representing an account-application transaction. The overall fraud rate
is 1.1029%. The dataset is distributed under CC BY 4.0 and is available
from the Kaggle platform.

## B. Delay Simulation

BAF exposes only month-level time granularity. Under a one-month delay
regime, a transaction in month `t` has its label available at month
`t + 1`. A transaction in month 7 has `label_time = 8`, which is beyond
the observation window; it is **censored**, not negative. Under this
regime, 96,843 rows (9.68% of the dataset) are censored and are excluded
from training and evaluation. Their count is reported in every results
table as a data-integrity figure.

## C. Chronological Split

The dataset is split chronologically into training months 0–2
(397,039 rows, fraud rate 0.9813%), validation months 3–4 (278,627 rows,
fraud rate 1.0207%), and test months 5–6 (227,491 rows, fraud rate
1.2576%). No shuffling occurs. No fold mixes time boundaries.
Preprocessing is fit on the training window only. The test window is used
exactly once.

## D. Preprocessing

Preprocessing is applied per classifier and fit within each training
fold. The categorical columns are `payment_type`, `employment_status`,
`housing_status`, `source`, and `device_os`. Numeric features are used
as-is for tree-based classifiers and standardized for Logistic Regression.
The full preprocessing pipeline is saved alongside the selected classifier
so that the deployed application applies the exact same transformations
used during training.

---

# 5. EXPERIMENTAL SETUP

## A. Evaluation Protocol

The primary metric is realized cost per transaction on the test window
under the frozen cost matrix and the one-month delay regime. The
policy is compared against the strongest canonical baseline, not the
weakest. Statistical claims use a 95% bootstrap confidence interval on
the advantage, with 1,000 resamples and seed 42. The minimum effect size
for a finding is a 5% relative reduction.

## B. Baselines

Six canonical baselines are reported: random decision, approve-all,
block-all, and each of the three classifiers under a static 0.5
threshold (Logistic Regression + 0.5, Random Forest + 0.5, LightGBM +
0.5). Every baseline uses the same split, the same cost matrix, and the
same delay regime. No baseline is tuned on the test window.

## C. Sensitivity Analysis

Each cost parameter (`false_positive_cost`, `review_cost`,
`residual_fraud_loss`) is varied one at a time over a 2× range, and the
backtest is recomputed at each setting. The model is not retrained; only
the cost matrix changes. The minimum advantage across the sweep is
reported as the robustness bound.

---

# 6. RESULTS

This section reports the data and split actually used, the
cross-validated classifier comparison, the cost-sensitive policy on the
untouched test window, the statistical and sensitivity analyses that
establish whether the result is a finding or a non-finding, and the
operational action distribution produced by the policy.

## A. Data and Split

The dataset contains 1,000,000 transactions over eight monthly periods
with an overall fraud rate of 1.1029%. Under the one-month delay regime,
the final month is censored, yielding 96,843 censored rows, or 9.68% of
the dataset. The single chronological split assigns months 0–2 to
training, months 3–4 to validation, and months 5–6 to test. The test
fraud rate (1.2576%) is modestly higher than the training rate (0.9813%),
a known temporal drift documented as a limitation. Exploratory analysis
surfaced three findings that shaped preprocessing and evaluation: the
fraud rate climbs monotonically from 1.13% in month 0 to 1.47% in month 7;
`proposed_credit_limit` is heavily right-skewed (skew 1.30, mean 515.85,
median 200) with 24.17% of values above the IQR upper bound, justifying
its exclusion from classification and its use as a cost-scaling input
instead; and the strongest point-biserial correlations with the target
are `credit_risk_score` (r = 0.0706) and `proposed_credit_limit`
(r = 0.0689), both weak but consistent with fraud detection being a
many-weak-signals problem.

## B. Classifier Comparison

Three classifiers were trained under identical folds, preprocessing
logic, and evaluation criterion. Hyperparameters were selected per
algorithm by mean realized cost after the policy across two
expanding-window folds.

**Table 1. Cross-validated realized cost per transaction after the policy.**

| Classifier | Mean ± SD (cost/txn) |
|---|---:|
| LightGBM | 0.005852 ± 0.000300 |
| Logistic Regression | 0.005915 ± 0.000338 |
| Random Forest | 0.006515 ± 0.000579 |

LightGBM achieves the lowest mean cost, with Logistic Regression second
and Random Forest clearly worse. The gap between LightGBM and Logistic
Regression is 0.000063 in absolute terms, or 1.07% relative — well inside
the 5% noise-band guard. The comparison is therefore reported as a
**non-finding**, and the selection is broken by simplicity under the
ordering Logistic Regression > Random Forest > LightGBM. Logistic
Regression is selected as the policy input and retrained on the full
training window.

**Table 2. Logistic Regression classification behavior at the 0.5 cut on
the test window (supporting evidence only).**

| Metric | Value |
|---|---:|
| Macro F1 | 0.5031 |
| Accuracy | 0.9875 |
| Precision (fraud) | 0.7826 |
| Recall (fraud) | 0.0063 |
| ROC-AUC | 0.8753 |
| Confusion matrix (TN, FP, FN, TP) | (224,625, 5, 2,843, 18) |

The low recall at 0.5 reflects the base rate: at a 1.26% fraud rate, a
threshold that minimizes misclassification produces very few positive
predictions. This is precisely the failure mode the decision-centric
framing is designed to avoid. The 0.5 cut is not the deployed operating
point.

## C. Decision Policy on the Test Window

The selected classifier's calibrated probability feeds the
argmin-of-expected-cost policy under the frozen cost matrix and the
training-calibrated amount-scaling rate. The policy's realized cost per
transaction is **0.007491**. The strongest baseline is **LightGBM +
static 0.5** at **0.017798**. The policy reduces realized cost per
transaction by **57.91%** relative to that baseline.

**Table 3. Realized cost per transaction on the test window.**

| Baseline | Cost/txn |
|---|---:|
| Random decision | 0.047484 |
| Approve-all | 0.018928 |
| Block-all | 0.098742 |
| Logistic Regression + static 0.5 | 0.018737 |
| Random Forest + static 0.5 | 0.018928 |
| LightGBM + static 0.5 (strongest) | 0.017798 |
| **Cost-sensitive policy (this work)** | **0.007491** |

Two observations matter for interpretation. First, the strongest baseline
is LightGBM + static 0.5, not Logistic Regression + static 0.5. The
advantage is reported against the stronger baseline. Second, the three
static-0.5 baselines perform nearly identically to approve-all: LightGBM
+ 0.5 reduces cost by 5.97%, Logistic Regression + 0.5 by 1.01%, and
Random Forest + 0.5 by 0%. A well-calibrated classifier with a static
threshold is effectively not a decision rule at this base rate.

The calibration gate was passed on the validation window with an ECE of
**0.0033**, well below the 0.05 threshold. The test-window Brier score
for the policy's probability input is **0.011506**.

## D. Statistical Validity

The advantage was tested with 1,000 bootstrap resamples of the test
window (seed 42) to produce a 95% confidence interval on the difference
between the baseline and the policy. The point estimate of the difference
is 0.010307 per transaction, with a 95% CI of [0.009602, 0.011058]. The
corresponding advantage is **57.91%**, with a 95% CI of **[53.95%,
62.13%]**. The interval excludes zero, so the pre-registered success
criterion is met.

## E. Sensitivity to Cost Assumptions

**Table 4. Cost-parameter sensitivity of the policy advantage.**

| Configuration | Policy cost/txn | Strongest baseline | Advantage |
|---|---:|---|---:|
| Baseline | 0.007491 | LGBM + 0.5 (0.017798) | 57.91% |
| `false_positive_cost = 0.05` | 0.007037 | LGBM + 0.5 (0.017752) | 60.36% |
| `false_positive_cost = 0.20` | 0.007625 | LGBM + 0.5 (0.017890) | 57.38% |
| `review_cost = 0.01` | 0.006253 | LGBM + 0.5 (0.017798) | 64.87% |
| `review_cost = 0.04` | 0.009298 | LGBM + 0.5 (0.017798) | **47.76%** |
| `residual_fraud_loss = 0.15` | 0.006588 | LGBM + 0.5 (0.017798) | 62.99% |
| `residual_fraud_loss = 0.60` | 0.008700 | LGBM + 0.5 (0.017798) | 51.12% |

The minimum advantage across the sweep is **47.76%**, attained at
`review_cost = 0.04`. Even at that worst case the policy retains nearly
half the baseline cost reduction.

## F. Operational Action Distribution

On the 227,491 test transactions, the policy routes 205,395 to
`approve`, 21,371 to `review`, and 725 to `block`. The operational
precision and recall of the policy are 0.0654 and 0.5051 respectively.
Ranking metrics at fixed budgets are Precision@1% = 0.2431,
Precision@5% = 0.1189, Precision@10% = 0.0775, and Recall@1% = 0.1933,
Recall@5% = 0.4729, Recall@10% = 0.6162. The ranking metrics are modest
in absolute terms, which is expected under a 1.26% base rate. The result
of interest is the cost reduction, not the ranking.

---

# 7. DISCUSSION

## A. Why the Classifier Comparison Is a Non-Finding

The classifier comparison was deliberately structured so that a
cross-validated ranking could only be reported as a finding if it was
robust to noise. LightGBM achieved the lowest mean cross-validated
realized cost against Logistic Regression by 1.07%, which is well inside
the range that a two-fold cross-validation on a 1.1% positive-rate
problem can produce by chance. The comparison is therefore reported as a
non-finding, and the selection is broken in favor of the simpler, more
interpretable classifier. A student paper that reported "LightGBM beat
Logistic Regression by 1.07%" as if it were substantive would be
overclaiming on evidence that does not support the claim.

The practical consequence is that a fraud operations team considering a
deployment on this data would not need to prefer a gradient-boosting
model over logistic regression on performance grounds alone. The
interpretability of a linear model — coefficients are readable, decisions
are traceable, drift is diagnosable — carries real operational value that
a 1.07% cost difference does not outweigh.

## B. Why the Policy Beats the Static Baselines

The 57.91% cost reduction comes from the decision rule, not from the
classifier. All three classifiers were well-calibrated on validation
(ECE well below 0.05), yet all three static-0.5 baselines performed
nearly identically to approve-all. The argmin-of-expected-cost policy
makes the tradeoff between fraud loss, review cost, and false-positive
friction explicit at every transaction. The mechanism is amount scaling:
when the fraud-loss term is per-row, the expected cost of approving a
high-amount transaction grows in proportion to that amount, and the
argmin correctly routes large transactions toward review even when the
classifier's probability is unchanged. Under constant loss the same
transactions would have been approved.

This is the paper's central methodological claim. A classifier is better
if and only if the policy it feeds produces lower realized cost. The
results support that claim: the same classifiers that fail to beat
approve-all at a 0.5 threshold produce a 57.91% cost reduction when fed
into the argmin rule. The decision rule, not the model, does the work.

## C. Error Analysis and Tradeoffs

The policy's operational recall is 0.5051 and its operational precision
is 0.0654. That is, the policy flags about half of all fraud for review
or block, and roughly one in fifteen flagged transactions is actually
fraudulent. The precision figure looks low in isolation, but it is the
correct precision for a cost-sensitive rule under the frozen cost matrix:
the policy is willing to accept a low precision because the cost of a
false positive (0.1) is much smaller than the cost of a missed fraud
(fraud_loss × amount). A rule that optimized precision would route fewer
transactions to review and would miss more fraud, raising realized cost.

The dominant error type at the classifier's 0.5 cut is false negatives —
2,843 of them against only 5 false positives on the test window. The
policy mitigates this not by retraining the classifier but by using its
probabilities differently: scores that would be classified as negative at
0.5 are routed to review if their expected cost justifies it. The
classifier's ranking ability, captured by its ROC-AUC of 0.8753, is
preserved; only the thresholding behavior changes.

## D. Connection to the Decision-Centric Framing

The results support the decision-centric framing on three levels. First,
the classifier comparison is a non-finding: the three traditional
classifiers produce statistically indistinguishable policies, so
classifier choice does not determine performance. Second, the
static-threshold baselines perform near approve-all even though the
classifiers are well-calibrated, demonstrating that calibration alone
does not produce good decisions. Third, the argmin policy, using the same
classifier probabilities, reduces cost by 57.91%, showing that the
decision rule is where the value is created.

---

# 8. LIMITATIONS

The evaluation in this paper is a controlled temporal backtest on a
single synthetic dataset under a single delay regime. It establishes the
methodological claim — that a cost-sensitive policy can substantially
reduce realized cost relative to static baselines — but it does not
establish general fraud-detection performance in production.

Four limitations bound the interpretation of the results. The dataset is
synthetic: BAF is a realistic benchmark but its fraud rate, feature
distributions, and dispute dynamics are generated rather than observed,
so the reported cost reductions are not production estimates. The delay
regime is a single one-month interval determined by BAF's month-level
granularity: longer delays, shorter delays, and mixed per-transaction
delays are not evaluated, and the censored fraction is a direct
consequence of the fixed regime. The amount column is a proxy —
`proposed_credit_limit`, not a true transaction amount — so the amount
scaling that drives much of the policy advantage is applied to a proxy
feature and its absolute magnitude should not be taken literally. And
the cost matrix is a frozen assumption rather than a measured quantity;
the sensitivity sweep bounds how much the result moves under 2× variation
in each parameter, but the values themselves are chosen, not estimated
from operational data.

Three additional limitations are structural to the framing. The policy
does not model review capacity: real fraud operations have a finite
number of investigators per time window, and the current build does not
enforce a hard cap on the review queue. The policy does not model
feedback effects: in production, the actions a system takes influence
which labels are observed later, and the current backtest assumes a
static label set. And the policy does not adapt to drift: the training
and test windows are consecutive months, and the small increase in
fraud rate from training to test is documented but not corrected. These
are named as future work rather than claimed as solved.

The reported classifier selection is itself a limitation worth stating.
The comparison across three classifiers was a non-finding — the top two
were within 1.07% of each other in mean cross-validated cost — so the
choice of Logistic Regression is justified by interpretability and
speed, not by superior performance. On a larger sample, a different
seed, or a different temporal fold structure, a different classifier
might be selected. The paper reports the choice honestly rather than
claiming a ranking the evidence does not support.

---

# 9. CONCLUSION AND FUTURE WORK

This paper evaluated a cost-sensitive fraud decision policy under a
delayed and censored label regime on the Bank Account Fraud dataset. The
classifier is an input; the policy is the object of study; the backtest
is the evidence. Under a 1-month delay, a chronological split, and a
frozen cost matrix with amount-scaled fraud loss, the argmin-of-expected-
cost policy reduced realized cost per transaction by **57.91%** relative
to the strongest baseline, with a 95% bootstrap confidence interval of
**[53.95%, 62.13%]** that excludes zero. The result is robust to a 2×
variation in each of three cost parameters, with a minimum advantage of
**47.76%**. The classifier selection across Logistic Regression, Random
Forest, and LightGBM was a non-finding under a pre-registered noise-band
guard, and the tie was broken toward the simplest model. Censored labels
(96,843 rows, 9.68%) were excluded and reported rather than treated as
negatives.

The paper's methodological contribution is a reproducible evaluation
protocol for fraud decision policies under delayed and partial labels:
temporal splitting, a calibration gate, a pre-registered noise-band
guard for classifier selection, bootstrap confidence intervals on the
primary metric, and a cost-sensitivity sweep that bounds the robustness
of the finding. Its empirical contribution is the demonstration that
static thresholds on highly imbalanced fraud data perform near-identically
to approve-all even when the underlying classifier is well-calibrated,
and that the value of a decision system lies in the decision rule rather
than in the classifier alone. Its negative contribution is an honest
reporting of a classifier comparison that produced no finding, in place
of a spurious ranking.

Several directions remain open. The most immediate is the extension to
additional delay regimes — 2-month, 3-month, and mixed per-transaction
delays — which requires a dataset with finer timestamp granularity than
BAF provides. A second direction is capacity-aware decisioning, which
would replace the unconstrained argmin with a policy that respects a
finite review budget and reports the value lost to that constraint. A
third is cost-sensitive training, in which the classifier's loss function
incorporates the same asymmetry the policy uses, evaluated against the
current decoupled design under the same stop criteria. Further directions
include rolling-window evaluation to detect drift, fairness-aware policy
constraints for regulatory contexts, and an evaluation of
amount-scaled `false_positive_cost`, which was named as a scope boundary
in this paper and would require a corresponding change to the cost
matrix. Each is gated on a measured failure of the current system, and
none is a claim of this submission.

---

# REFERENCES

[1] Bangko Sentral ng Pilipinas, *Digital Payments Transformation Roadmap
2020–2023*, Manila, Philippines, 2023.

[2] C. Elkan, "The foundations of cost-sensitive learning," in *Proc. 17th
Int. Joint Conf. Artificial Intelligence*, 2001, pp. 973–978.

[3] O. Chapelle, "Modeling delayed feedback in display advertising," in
*Proc. 20th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*,
2014, pp. 1097–1105.

[4] S. Jesus, J. Pombal, D. Alves, A. Cruz, P. Saleiro, R. Ribeiro, J.
Gama, and P. Bizarro, "Turning the tables: Biased, imbalanced, dynamic
tabular datasets for ML evaluation," in *Proc. NeurIPS Datasets and
Benchmarks Track*, 2022.

[5] A. Dal Pozzolo, O. Caelen, R. A. Johnson, and G. Bontempi,
"Calibrating probability with an unbalanced class: An application to
fraud detection," in *Proc. IEEE Symp. Computational Intelligence and
Data Mining*, 2015, pp. 1–7.

[6] C. Elkan and K. Noto, "Learning classifiers from only positive and
unlabeled data," in *Proc. 14th ACM SIGKDD Int. Conf. Knowledge
Discovery and Data Mining*, 2008, pp. 213–220.

[7] F. Pedregosa et al., "Scikit-learn: Machine learning in Python,"
*J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011.

[8] G. Ke et al., "LightGBM: A highly efficient gradient boosting
decision tree," in *Advances in Neural Information Processing Systems*,
vol. 30, 2017, pp. 3146–3154.

---

# APPENDICES

## Appendix A — Data Dictionary

The full feature-by-feature schema — names, types, units, allowed values,
and source-time availability — is provided in
`documentation/data_dictionary.md`. The 28 model features are 23 numeric
and 5 categorical. The exclusion list is `transaction_id`, `fraud_bool`,
`month`, `label_month`, `observed`, `amount_proxy`,
`proposed_credit_limit`, and `device_fraud_count`.

## Appendix B — Repository and Application

Source code, configuration, and reproducibility instructions are
available in the project repository. The deployed decision-support
application is available at:

https://delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app

The application loads the same classifier and preprocessing pipeline
reported in this paper, and displays the predicted fraud probability
along with the routed action and the cost reasoning behind it.

## Appendix C — Contribution Record

See `documentation/contribution_record.md`.

## Appendix D — Ownership and Authorship Declaration

See `documentation/ownership_declaration.md`.
