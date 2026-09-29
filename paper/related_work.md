# 2. RELATED WORK

> **Repository:** `delayed-label-fraud-decisioning`
> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Document:** Section 2 draft — Related Work
> **Status:** draft — citations use seed numbers from `paper/references.md`
> **Last updated:** 2026-09-29

> **How to use this draft:** The prose is done. Citations use the seed
> numbers in `paper/references.md`; final numbering is set during assembly
> of `paper_imrad.md`. Do not add bullets — the IEEE sample uses prose.
> Subsections follow the sample's `A.` / `B.` / `C.` convention.

---

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
every result. This is a small discipline, but it separates a paper that
reports an honest number from one that quietly optimizes on the labels it
happens to have.

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
ranking metrics without connecting them to an operational cost; studies
on cost-sensitive learning often assume the label is available at decision
time; studies on delayed feedback often focus on advertising, where the
delay distribution is well understood, rather than on fraud, where labels
are both late and frequently missing. We bridge these threads by
evaluating an argmin-of-expected-cost policy end-to-end on BAF under a
simulated one-month label delay, with censored labels counted rather than
hidden, with a pre-registered evaluation protocol, and with bootstrap
confidence intervals on the primary metric. The classifier is treated as
an input to the policy; the policy is the object of study. This is not a
novel policy — expected-cost minimization is standard in cost-sensitive
learning — but the combination of a delay-aware split, an explicitly
reported censored fraction, a cost-sensitive decision rule, and a
statistical evaluation of the primary metric has not, to our knowledge,
been assembled on this dataset.

---

## Notes for the Paper Team

- Citations use seed numbers from `paper/references.md`. During final
  assembly of `paper/paper_imrad.md`, renumber to the order of first
  in-text appearance.
- Every citation above corresponds to a seed entry in
  `paper/references.md`. Do not cite a work that is not in the reference
  list; do not add a reference that is not cited here or elsewhere in the
  paper.
- Do not add bullets. The IEEE sample uses prose in the body.
- Do not introduce a claim that is not supported by the cited work or by
  the project's own reports (`reports/decision_backtest.md`,
  `reports/model_comparison.md`, `reports/sensitivity.md`,
  `reports/bootstrap.md`).
- If a reviewer asks "what is new here," the answer is in §E. Do not
  overclaim a novel policy; the contribution is the end-to-end evaluation
  under delayed and censored labels, not the argmin rule itself.
