# 6. RESULTS

> **Repository:** `delayed-label-fraud-decisioning`
> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Document:** Section 6 draft — Results
> **Status:** draft — every number traces to `docs/paper/reference_sheet.md` §1
> **Last updated:** 2026-09-29

> **How to use this draft:** The prose is done. Do not add bullets — the
> IEEE sample uses prose. Tables are permitted and expected in Results.
> Every number below must appear in `docs/paper/reference_sheet.md` §1.
> If a sentence states a number, verify it against that sheet before
> submission. Subsections follow the sample's `A.` / `B.` / `C.`
> convention.

---

This section reports the results of the pipeline described in Section 3.
It proceeds in five parts: the data and split actually used, the
cross-validated classifier comparison, the cost-sensitive policy on the
untouched test window, the statistical and sensitivity analyses that
establish whether the result is a finding or a non-finding, and the
operational action distribution produced by the policy.

## A. Data and Split

The Bank Account Fraud v1 dataset contains 1,000,000 transactions over
eight monthly periods. The overall fraud rate is 1.1029%. Under the
one-month delay regime — `label_time = month + 1`, observed if
`label_time <= 7` — the final month is censored, yielding 96,843 censored
rows, or 9.68% of the dataset. These rows are excluded from training and
evaluation and reported as a data-integrity figure rather than treated as
negatives.

The single chronological split assigns months 0–2 to training
(397,039 rows, fraud rate 0.9813%), months 3–4 to validation (278,627
rows, fraud rate 1.0207%), and months 5–6 to test (227,491 rows, fraud
rate 1.2576%). The test-window fraud rate is modestly higher than the
training rate — a known temporal drift that is documented as a limitation
rather than corrected, because correcting it would require tuning on the
test window. Exploratory analysis surfaced three findings that shaped
preprocessing and evaluation: the fraud rate climbs monotonically from
1.13% in month 0 to 1.47% in month 7; the `proposed_credit_limit` feature
is heavily right-skewed (skew 1.30, mean 515.85, median 200) with 24.17%
of values above the IQR upper bound, which justifies its exclusion from
classification and its use as a cost-scaling input instead; and the
strongest point-biserial correlations with the target are `credit_risk_score`
(r = 0.0706) and `proposed_credit_limit` (r = 0.0689), both weak but
consistent with fraud detection being a many-weak-signals problem.

## B. Classifier Comparison

Three classifiers were trained under identical folds, preprocessing
logic, and evaluation criterion. Hyperparameters were selected per
algorithm by mean realized cost after the policy across two
expanding-window folds (train months 0..k, validate month k+1). The mean
and standard deviation of realized cost per transaction across folds are
reported in Table 1.

**Table 1. Cross-validated realized cost per transaction after the policy.**

| Classifier | Mean ± SD (cost/txn) |
|---|---:|
| LightGBM | 0.005852 ± 0.000300 |
| Logistic Regression | 0.005915 ± 0.000338 |
| Random Forest | 0.006515 ± 0.000579 |

LightGBM achieves the lowest mean cost, with Logistic Regression second
and Random Forest clearly worse. The gap between LightGBM and Logistic
Regression is 0.000063 in absolute terms, or 1.07% relative. The
pre-registered noise-band guard requires both a consistent winner across
folds and a relative gap exceeding 5% before a selection counts as a
finding. LightGBM wins both folds, but the gap falls well inside the
band, so the comparison is reported as a **non-finding**. The selection is
therefore broken by simplicity under the ordering Logistic Regression >
Random Forest > LightGBM. Logistic Regression is selected as the policy
input. It is retrained on the full training window and evaluated once on
the untouched test window.

Supporting classification metrics at the standard 0.5 probability cut,
which is not the deployed operating point, are reported in Table 2 for
the selected classifier.

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
predictions. This is precisely the failure mode that the decision-centric
framing is designed to avoid. The 0.5 cut is not the deployed operating
point; it is reported so that the reader can see how poorly a naive
threshold performs on this dataset.

## C. Decision Policy on the Test Window

The selected classifier's calibrated probability feeds the
argmin-of-expected-cost policy under the frozen cost matrix and the
training-calibrated amount-scaling rate. The policy's realized cost per
transaction is **0.007491**. The strongest baseline is **LightGBM +
static 0.5** at **0.017798**. The policy reduces realized cost per
transaction by **57.91%** relative to that baseline. Table 3 shows the
full comparison across all six canonical baselines and the policy.

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

Two observations from this table matter for interpretation. First, the
strongest baseline is not Logistic Regression + static 0.5, which the
project originally assumed, but LightGBM + static 0.5. The policy
advantage is reported against the stronger baseline, not the more
convenient one. Second, the three static-0.5 baselines perform nearly
identically to approve-all: LightGBM + 0.5 reduces cost by 5.97%,
Logistic Regression + 0.5 by 1.01%, and Random Forest + 0.5 by 0%. A
well-calibrated classifier with a static threshold is effectively not a
decision rule at this base rate. This is a documented negative result at
the framing level, and it is one of the paper's contributions.

The calibration gate was passed on the validation window with an ECE of
**0.0033**, well below the 0.05 threshold, so no calibration step was
applied. The test-window Brier score for the policy's probability input
is **0.011506**. The reliability table shows the classifier is
well-calibrated across the majority of the score range and mildly
overconfident only in the top decile, a region whose scores fall inside
the review band and do not drive block decisions.

## D. Statistical Validity

The advantage was tested with 1,000 bootstrap resamples of the test
window (seed 42) to produce a 95% confidence interval on the difference
between the baseline and the policy. The point estimate of the
difference is 0.010307 per transaction, with a 95% CI of [0.009602,
0.011058]. The corresponding advantage is **57.91%**, with a 95% CI of
**[53.95%, 62.13%]**. The interval excludes zero, so the pre-registered
success criterion is met: the policy advantage is a statistical finding,
not noise.

## E. Sensitivity to Cost Assumptions

Each cost parameter was varied one at a time over a 2× range, and the
backtest recomputed decisions and realized costs under each setting. The
model was not retrained; only the cost matrix changed. Table 4 reports
the policy cost, the strongest baseline, and the advantage at every
setting.

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
`review_cost = 0.04`, which is the setting that makes review most
expensive and therefore reduces the policy's leverage most. Even at that
worst case the policy retains nearly half the baseline cost reduction,
and at every setting the policy remains below every baseline. The
pre-registered stop criterion — advantage remaining above 5% across the
sweep — is comfortably met.

## F. Operational Action Distribution

On the 227,491 test transactions, the policy routes 205,395 to
`approve`, 21,371 to `review`, and 725 to `block`. Approve is the
dominant action by design: at a base rate near 1.26% and with a review
cost of 0.02, the argmin frequently finds that the cheapest decision for
a low-probability transaction is to let it through, and for a
high-probability large-amount transaction is to block outright. The
review band captures the middle of the score distribution, where the
expected cost of a wrong decision is large enough to justify the review
expense but not large enough to justify blocking.

The operational precision and recall of the policy — as opposed to the
classifier at 0.5 — are 0.0654 and 0.5051 respectively. That is, the
policy flags about half of all fraud for review or block while roughly
6.5% of its flagged transactions turn out to be fraud. Ranking metrics
at fixed budgets are Precision@1% = 0.2431, Precision@5% = 0.1189,
Precision@10% = 0.0775, and Recall@1% = 0.1933, Recall@5% = 0.4729,
Recall@10% = 0.6162. The ranking metrics are modest in absolute terms,
which is expected under a 1.26% base rate. The result of interest is the
cost reduction, not the ranking.

---

## Notes for the Paper Team

- Every number above must appear in `docs/paper/reference_sheet.md` §1
  before submission. If any is missing from the sheet, add it to the
  sheet first, then cite it here.
- The four numbers to preserve exactly: **57.91%**, **[53.95%,
  62.13%]**, **96,843**, **9.68%**.
- Do not add "high accuracy" language. Accuracy is meaningless at 1.26%
  and is a forbidden metric per `docs/paper/reference_sheet.md` §3.
- Do not present the static-0.5 result as a policy. It is a baseline for
  comparison, and its near-identical performance to approve-all is itself
  a finding.
- The classifier selection is a non-finding. Do not claim Logistic
  Regression is the best classifier on the evidence; claim it was
  selected by the noise-band guard because the cross-validated gap was
  below the pre-registered effect size.
- The confusion matrix in §B is at the 0.5 cut, not at the deployed
  operating point. If the paper team presents it, state the distinction
  explicitly.
- Ranking metrics (§F) are supporting evidence. Do not present them as
  the primary result.
