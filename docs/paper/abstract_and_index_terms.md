# Abstract and Index Terms

## Abstract

Fraud detection systems must decide whether to approve, review, or block a
transaction in real time, yet fraud labels arrive weeks to months later and
are frequently censored before the evaluation window closes. We frame this
as a cost-sensitive decision problem rather than a classification problem
and evaluate it under a temporal backtest on the Bank Account Fraud (BAF)
dataset with a simulated one-month label delay. A LightGBM classifier
feeding an argmin-of-expected-cost policy reduces realized cost per
transaction by 56.9% relative to the strongest baseline, a static 0.5
threshold on the same model's scores, with a 95% bootstrap confidence
interval of [52.8%, 60.9%]. The result is robust to a 2× variation in each
cost parameter and does not depend on test-set tuning: the cost rate is
derived from training-window amounts only. We report censored-label counts
(96,843 of 1,000,000, or 9.68%) rather than treating unobserved fraud as
legitimate, and we release the full evaluation protocol alongside the
pipeline. The paper contributes a reproducible template for evaluating
fraud decision policies under delayed and partial labels, and demonstrates
that static thresholds on imbalanced data behave near-identically to
approve-all even when the underlying model is well-calibrated. Limitations
include a single delay regime, a synthetic dataset, and an amount proxy
derived from proposed credit limit.

## Index Terms

Cost-sensitive learning, fraud detection, delayed feedback, censored
labels, decision policy, temporal backtest, LightGBM, Bank Account Fraud
dataset, expected-cost minimization, false-positive cost, bootstrap
confidence intervals, sensitivity analysis, machine learning.

## Notes for the Team

- The abstract is one paragraph, ~200 words, no bullets. Matches the
  sample's structure.
- The four numbers to preserve exactly: **56.9%**, **[52.8%, 60.9%]**,
  **96,843**, **9.68%**.
- Do NOT add "excellent accuracy" or similar. The result is a cost
  reduction, not an accuracy claim. This is a deliberate contrast with
  typical student papers and reviewers will notice.
- Index terms should match the sample's style: a comma-separated list of
  ~10-14 terms, title-cased, no period at the end.