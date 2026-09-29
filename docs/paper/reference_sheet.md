# Paper Reference Sheet

One-page lookup for the paper team. Every number and claim used in the
paper must be traceable to this sheet.

---

## 1. Key Numbers (exact — do not round without noting)

| Number | Value | Source |
|---|---:|---|
| Dataset size | 1,000,000 rows | reports/decision_backtest.md §Data Integrity |
| Fraud rate (overall) | 1.1029% | data_card.md §4.5 |
| Fraud rate (test) | 1.2576% | reports/decision_backtest.md §Data Integrity |
| Censored labels | 96,843 (9.68%) | reports/decision_backtest.md §Data Integrity |
| Train rows | 397,039 (months 0–2) | evaluation_protocol.md §4 |
| Val rows | 278,627 (months 3–4) | evaluation_protocol.md §4 |
| Test rows | 227,491 (months 5–6) | evaluation_protocol.md §4 |
| Features used | 28 | docs/data_card.md §10.4 |
| ECE (val) | 0.0033 | decision_policy.md §9.2 |
| Brier (test) | 0.011506 | reports/decision_backtest.md §Calibration |
| Policy cost/txn | 0.007491 | reports/decision_backtest.md §Results |
| Strongest static-0.5 (LGBM+0.5) cost/txn | 0.017798 | reports/decision_backtest.md §Results |
| Approve-all cost/txn | 0.018928 | reports/decision_backtest.md §Results |
| **Policy advantage** | **57.91%** | reports/decision_backtest.md §Interpretation |
| Advantage 95% CI | [53.95%, 62.13%] | reports/bootstrap.md |
| Min advantage across cost variations | 47.76% | reports/sensitivity.md |
| Approve / Review / Block counts | 205,395 / 21,371 / 725 | reports/decision_backtest.md §Action distribution |
| Test suite | 58 tests | pytest -q |

**The four numbers to preserve exactly: 57.91%, [53.95%, 62.13%], 96,843, 9.68%.**

---

## 2. Claims You Can Make (with evidence)

| Claim | Evidence |
|---|---|
| Cost-sensitive policy outperforms strongest baseline | 0.007491 vs 0.017798, 57.91% reduction |
| Result is not statistical noise | Bootstrap CI [53.95%, 62.13%], excludes zero |
| Result is robust to cost assumptions | Min advantage 47.76% across 2× range on 3 parameters |
| Result does not depend on test-set tuning | fraud_loss_rate derived from train window |
| Calibration is adequate without post-hoc fix | ECE = 0.0033, below 0.05 threshold |
| Censored labels excluded, not treated as negative | 96,843 month-7 rows marked and excluded |
| Splits are temporal, not random | Chronological split; split.py asserts sum |
| Pipeline reproduces from one command | `python -m src.pipeline` byte-for-byte |
| Static threshold is near-null at this base rate | LGBM+0.5 reduces cost 5.97% vs approve-all (0.018928 → 0.017798) |

---

## 3. Claims You CANNOT Make (avoid these)

| Do NOT say | Why |
|---|---|
| "High accuracy" | Accuracy is meaningless at 1.26% base rate and is a forbidden metric (evaluation_protocol.md §15) |
| "The model detects fraud with X% accuracy" | Same reason; use cost reduction, not accuracy |
| "Production-ready" | Synthetic dataset, single delay regime, proxy amount column |
| "Real-time performance verified" | No latency measurement was done |
| "Handles all delay regimes" | Only 1-month regime was tested |
| "Outperforms on all metrics" | Ranking metrics (precision/recall) are modest; the win is on cost |
| "Tested on real bank data" | BAF is synthetic |
| "Generalizes to other fraud domains" | Not tested |
| "Capacity-aware" | No capacity constraint was modeled |
| "Statistically significant across all variations" | CIs computed only on the main test-set comparison |

---

## 4. Methodology Summary (2 sentences the paper can reuse)

At decision time, a LogisticRegression classifier produces a fraud
probability for each transaction. A cost-sensitive policy then selects the
action —
approve, review, or block — that minimizes expected cost under a fixed
cost matrix, with transaction amount scaling the fraud loss term.

---

## 5. What Was NOT Done (state in Limitations)

- Single delay regime (1 month); no 2-month or 3-month
- Hyperparameter grid per algorithm evaluated on the same folds; selection by mean realized cost
- No calibration adjustment (ECE already below threshold)
- No capacity constraint on review queue
- Amount proxy = proposed_credit_limit; BAF has no clean amount column
- No bootstrap CIs on the sensitivity runs (only on the main comparison)
- No rule-based threshold baseline (deferred; 6 canonical baselines implemented: Random, Approve-all, Block-all, LR+0.5, RF+0.5, LGBM+0.5)
- Synthetic data; results are not production estimates

---

## 6. Section → Source Doc Map

| Paper section | Read this |
|---|---|
| Introduction | problem_framing.md §1–4 |
| Related Work | (paper team must write; cite Elkan 2001, Chapelle 2014, Jesus 2022, Dal Pozzolo 2015) |
| Methodology | decision_policy.md §5–6 |
| Dataset | data_card.md §2–5 |
| Experimental Setup | evaluation_protocol.md §7–9 |
| Results | reports/decision_backtest.md + reports/bootstrap.md + reports/sensitivity.md |
| Discussion | reports/decision_backtest.md §Interpretation |
| Limitations | reports/decision_backtest.md §Limitations |
| Conclusion | roadmap.md §5–7 |
| References | (paper team must build) |
