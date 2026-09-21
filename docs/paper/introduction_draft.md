# 1. INTRODUCTION

> **How to use this draft:** The paragraphs below have bracketed
> placeholders like [CITE: BSP 2024 report] or [STATISTIC NEEDED]. Fill
> those in before submission. The structure and prose are done. Do not add
> bullets — the sample uses prose in the intro.

---

Digital payment systems in the Philippines process millions of
transactions every day. According to the Bangko Sentral ng Pilipinas
(BSP), the share of digital payments in total retail payment volume rose
from [STATISTIC NEEDED — BSP Digital Payments Transformation Roadmap
2020–2023 reports ~42% in 2023], with the total value of digital
transactions exceeding [STATISTIC NEEDED — BSP e-payments report]. This
growth has brought fraud into closer view: the BSP received
[STATISTIC NEEDED — BSP Consumer Affairs Group complaint statistics]
fraud-related consumer complaints in [YEAR], of which unauthorized
transactions accounted for the largest share. For banks, issuers,
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
notice.

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
learning — but it is rarely evaluated end-to-end on a fraud dataset with
simulated label delay, censored labels reported rather than hidden, and
statistical rigor on the primary metric.

We evaluate this framing on the Bank Account Fraud (BAF) dataset, a
public 1-million-row synthetic benchmark designed for fraud research.
Because BAF provides only month-level time granularity, we simulate a
one-month label delay and hold out the final month as censored. We
compare a cost-sensitive policy against five baselines under an identical
temporal split and cost matrix, report realized cost per transaction as
the primary metric, and test the result's robustness with a 2× sensitivity
analysis on each cost parameter and a bootstrap confidence interval.

The main findings are as follows. First, the cost-sensitive policy reduces
realized cost per transaction by **56.9%** relative to the strongest
baseline — a static 0.5 threshold on the same model's scores — with a 95%
bootstrap confidence interval of **[52.8%, 60.9%]**. Second, the static
threshold performs *near-identically to approve-all* (7.3% reduction), a
failure mode that AUC-based evaluation would not reveal. Third, the
result is robust across a 2× range on each of three cost parameters; the
minimum advantage across all variations is 46.5%. Fourth, the cost rate
used for amount scaling is derived from training-window amounts only, so
the headline result does not depend on any test-set tuning.

This paper makes three contributions. It contributes a reproducible
evaluation protocol for fraud decision policies under delayed and
censored labels, including pre-registered stop criteria and an explicit
prohibition on random splits. It contributes a temporal backtest on BAF
with five canonical baselines, censored-label reporting, cost sensitivity,
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

## Statistics to Find (Fill In Before Submission)

The sample intro cites MRT-3 ridership from DOTr and LRTA reports. Yours
should cite BSP, credit-card-industry, and academic sources the same way.

| Statistic | Where to Find It |
|---|---|
| Philippine digital payment share (retail volume) | BSP Digital Payments Transformation Roadmap 2020–2023 |
| Total value of digital transactions | BSP Selected Philippine Economic Indicators, Payments section |
| Number of fraud complaints to BSP | BSP Consumer Affairs Group annual report |
| Credit card fraud losses in PH | BSP Financial Inclusion reports, credit card industry association |
| Typical chargeback/dispute window | Visa/Mastercard dispute resolution rules (public) |
| Global card fraud losses | Nilson Report (annual), or Visa/Mastercard investor reports |
| Digital payment volume growth | BSP Payments System Oversight reports |

Aim for 4–6 real statistics, all from 2022 or later, all cited with author
or institution and year. The sample cites exactly this way ("According to
Paulley (2021)..."). Do not invent numbers. If you cannot find a specific
Philippine statistic, cite the closest regional (ASEAN) or global one and
label it as such.

## References This Intro Needs

Add these to `docs/paper/references.md` in IEEE numbered format:

1. Bangko Sentral ng Pilipinas, *Digital Payments Transformation Roadmap
   2020–2023*, Manila, Philippines, 2023.
2. C. Elkan, "The foundations of cost-sensitive learning," in *Proc. 17th
   Int. Joint Conf. Artificial Intelligence*, 2001, pp. 973–978.
3. O. Chapelle, "Modeling delayed feedback in display advertising," in
   *Proc. 20th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*,
   2014, pp. 1097–1105.
4. S. Jesus, J. Pombal, D. Alves, A. Cruz, P. Saleiro, R. Ribeiro, J.
   Gama, and P. Bizarro, "Turning the table: A comprehensive survey of
   the Bank Account Fraud dataset suite," in *Proc. NeurIPS Datasets and
   Benchmarks Track*, 2022.
5. A. Dal Pozzolo, O. Caelen, R. A. Johnson, and G. Bontempi, "Calibrating
   probability with an unbalanced class: An application to fraud
   detection," in *Proc. IEEE Symp. Computational Intelligence and Data
   Mining*, 2015, pp. 1–7.