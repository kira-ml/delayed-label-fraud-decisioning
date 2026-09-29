# 7. DISCUSSION

> **Repository:** `delayed-label-fraud-decisioning`
> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Document:** Section 7 draft — Discussion
> **Status:** draft — every number traces to `docs/paper/reference_sheet.md` §1
> **Last updated:** 2026-09-29

> **How to use this draft:** The prose is done. Do not add bullets — the
> IEEE sample uses prose. Subsections follow the sample's `A.` / `B.` /
> `C.` convention. This is the section where overclaiming is most
> tempting and most damaging; the discipline is to interpret only what
> the results actually support.

---

The results in Section 6 show a 57.91% reduction in realized cost per
transaction relative to the strongest baseline, with a 95% bootstrap
confidence interval of [53.95%, 62.13%] and a minimum advantage of 47.76%
across the cost-sensitivity sweep. This section interprets that result,
explains what it does and does not imply, and connects it back to the
decision-centric framing the project is built on.

## A. Why the Classifier Comparison Is a Non-Finding, and Why That Matters

The classifier comparison was deliberately structured so that a
cross-validated ranking could only be reported as a finding if it was
robust to noise. The pre-registered noise-band guard requires the top
classifier to win every fold and the relative gap to the runner-up to
exceed 5%. LightGBM achieved the lowest mean cross-validated realized
cost (0.005852 ± 0.000300) against Logistic Regression's 0.005915 ±
0.000338, a relative gap of 1.07%. That gap is real but small; it is
well inside the range that a two-fold cross-validation on a 1.1%
positive-rate problem can produce by chance. The comparison is therefore
reported as a non-finding, and the selection is broken in favor of the
simpler, more interpretable classifier.

This is not a weakness of the result — it is a feature of the
evaluation. A student paper that reported "LightGBM beat Logistic
Regression by 1.07%" as if it were a substantive finding would be
overclaiming on evidence that does not support the claim. The honest
statement is that on this dataset, with this delay regime, and this
sample size, the three traditional classifiers produce statistically
indistinguishable policies. The choice of Logistic Regression is
justified by interpretability and speed rather than by superior
performance, and the paper reports it that way.

The practical consequence is that a fraud operations team considering a
deployment on this data would not need to prefer a gradient-boosting
model over logistic regression on performance grounds alone. The
interpretability of a linear model — coefficients are readable, decisions
are traceable, drift is diagnosable — carries real operational value that
a 1.07% cost difference does not outweigh. This is the kind of reasoning
the noise-band guard was designed to surface.

## B. Why the Policy Beats the Static Baselines

The 57.91% cost reduction comes from the decision rule, not from the
classifier. This is worth stating explicitly because the intuition that
"a better classifier produces a better decision" is exactly the intuition
the paper is arguing against. All three classifiers were well-calibrated
on validation (ECE well below 0.05), yet all three static-0.5 baselines
performed nearly identically to approve-all: LightGBM + 0.5 reduced cost
by 5.97%, Logistic Regression + 0.5 by 1.01%, and Random Forest + 0.5 by
0%. A well-calibrated probability with an arbitrary threshold is
effectively not a decision rule at this base rate.

The argmin-of-expected-cost policy, by contrast, makes the tradeoff
between fraud loss, review cost, and false-positive friction explicit at
every transaction. The mechanism is amount scaling. When the fraud-loss
term is per-row, the expected cost of approving a high-amount transaction
grows in proportion to that amount, and the argmin correctly routes large
transactions toward review even when the classifier's probability is
unchanged. Under constant loss the same transactions would have been
approved. The policy is exploiting signal — the amount itself — that a
static threshold on `p` has no mechanism to use.

This is the paper's central methodological claim. A classifier is better
if and only if the policy it feeds produces lower realized cost. The
results support that claim: the same classifiers that fail to beat
approve-all at a 0.5 threshold produce a 57.91% cost reduction when fed
into the argmin rule. The decision rule, not the model, does the work.

## C. Error Analysis and Tradeoffs

The policy's operational recall on the test window is 0.5051, and its
operational precision is 0.0654. That is, the policy flags about half of
all fraud for review or block, and roughly one in fifteen flagged
transactions is actually fraudulent. The precision figure looks low in
isolation, but it is the correct precision for a cost-sensitive rule
under the frozen cost matrix: the policy is willing to accept a low
precision because the cost of a false positive (0.1) is much smaller than
the cost of a missed fraud (fraud_loss * amount). A rule that optimized
precision would route fewer transactions to review and would miss more
fraud, raising realized cost. The policy's operating point is chosen by
the cost matrix, not by a classification metric.

The dominant error type at the classifier's 0.5 cut is false negatives —
2,843 of them against only 5 false positives on the test window. This is
the same imbalance that makes static thresholds degenerate. The policy
mitigates this not by retraining the classifier but by using its
probabilities differently: scores that would be classified as negative at
0.5 are routed to review if their expected cost justifies it, catching a
substantial fraction of fraud the classifier would otherwise miss. The
classifier's ranking ability, which is captured by its ROC-AUC of 0.8753,
is preserved; only the thresholding behavior changes.

The cost sensitivity sweep shows that the policy's advantage is robust
to a 2× variation in every cost parameter. The worst case is
`review_cost = 0.04`, where the advantage falls to 47.76% — still nearly
half the baseline cost. This is important because the cost matrix is an
assumption, not a measurement. If the true review cost were twice the
frozen value, the policy would still dominate every baseline. If the
false-positive cost were half the frozen value, the advantage would grow
to 60.36%. The direction of the finding does not reverse anywhere in the
tested range.

## D. Connection to the Decision-Centric Framing

The framing argued that fraud detection is a decision problem under
uncertainty, not a classification problem, and that classification
metrics are a proxy for the decision rather than the decision itself. The
results support this claim on three levels. First, the classifier
comparison is a non-finding: the three traditional classifiers produce
statistically indistinguishable policies, so classifier choice does not
determine performance. Second, the static-threshold baselines perform
near approve-all even though the classifiers are well-calibrated,
demonstrating that calibration alone does not produce good decisions.
Third, the argmin policy, using the same classifier probabilities,
reduces cost by 57.91%, showing that the decision rule is where the value
is created.

The corollary is that evaluation must be of the policy. If this paper had
reported classifier accuracy or macro F1 as its primary metric, the
results would have looked ordinary — macro F1 of 0.5031 is not
impressive, and neither is ROC-AUC of 0.8753 on a temporal backtest.
Under the decision-centric framing, those numbers become supporting
evidence and the primary result becomes a measured operational cost
reduction. The framing changes what counts as a good result.

## E. What This Work Does Not Show

The results do not demonstrate that the deployed classifier is the best
possible classifier; the comparison was a non-finding, and a different
algorithm might win on a larger sample or a different seed. They do not
demonstrate that the policy generalizes to other fraud domains,
transaction amounts, or cost structures; the cost matrix is frozen and
the dataset is synthetic. They do not demonstrate production readiness:
no latency measurement was performed, no capacity constraint on the
review queue was modeled, and the amount column is a proxy derived from
`proposed_credit_limit` rather than a true transaction value. They do not
demonstrate that the delay simulation captures real chargeback dynamics;
the 1-month regime is a defensible simplification given BAF's
month-level granularity, but it is a simplification. And they do not
demonstrate that the policy will remain optimal under adversarial drift;
fraud patterns evolve, and the temporal split used here tests only a
single ordering of the eight available months.

Each of these limitations is a candidate for future work, and each is
documented in Section 8. None is hidden, and none is claimed as solved.

---

## Notes for the Paper Team

- Every number above must appear in `docs/paper/reference_sheet.md` §1
  before submission.
- The four numbers to preserve exactly: **57.91%**, **[53.95%,
  62.13%]**, **96,843**, **9.68%**.
- Do not claim Logistic Regression is the best classifier. It was
  selected by the noise-band guard, not by superior performance. This
  distinction is the paper's methodological strength and must not be
  softened.
- Do not present the 0.5-cut confusion matrix as the deployed operating
  point; the deployed system is the argmin policy, and the classification
  metrics are supporting evidence.
- The low precision of the policy (0.0654) is a feature of the cost
  matrix, not a defect. Explain it via the cost asymmetry, not as a
  weakness.
- Do not add recommendations that go beyond the evaluated system. The
  paper evaluated a policy; it did not evaluate a production deployment.
- The three claims that must not appear in this section, per
  `docs/paper/reference_sheet.md` §3: "production-ready", "generalizes to
  other fraud domains", and "statistically significant across all
  variations." If a sentence drifts toward any of these, rewrite it.
