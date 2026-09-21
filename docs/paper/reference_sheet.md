# Paper Reference Sheet

One-page lookup for the paper team. Every number and claim used in the
paper must be traceable to this sheet.

---

## 1. Key Numbers (exact — do not round without noting)

| Number | Value | Source |
|---|---:|---|
| Dataset size | 1,000,000 rows | reports/mvp_backtest.md §Data Integrity |
| Fraud rate (overall) | 1.1029% | data_card.md §4.1 |
| Fraud rate (test) | 1.2576% | reports/mvp_backtest.md §Data Integrity |
| Censored labels | 96,843 (9.68%) | reports/mvp_backtest.md §Data Integrity |
| Train rows | 397,039 (months 0–2) | evaluation_protocol.md §7.1 |
| Val rows | 278,627 (months 3–4) | evaluation_protocol.md §7.1 |
| Test rows | 227,491 (months 5–6) | evaluation_protocol.md §7.1 |
| Features used | 29 | reports/mvp_backtest.md |
| Val AUC | 0.9029 | daily log Task 7 |
| ECE (val) | 0.0040 | decision_policy.md §9.1 |
| Brier (test) | 0.011881 | reports/mvp_backtest.md §Calibration |
| Policy cost/txn | 0.007566 | reports/mvp_backtest.md §Results |
| Static-0.5 cost/txn | 0.017543 | reports/mvp_backtest.md §Results |
| Approve-all cost/txn | 0.018928 | reports/mvp_backtest.md §Results |
| **Policy advantage** | **56.87%** | reports/mvp_backtest.md §Interpretation |
| Advantage 95% CI | [52.77%, 60.91%] | reports/bootstrap.md |
| Min advantage across cost variations | 46.46% | reports/sensitivity.md |
| Approve / Review / Block counts | 206,724 / 19,155 / 1,612 | reports/mvp_backtest.md §Action distribution |
| Test suite | 13 tests, ~1.4 s | daily log (post-log update) |

**The four numbers to preserve exactly: 56.87%, [52.77%, 60.91%], 96,843, 9.68%.**

---

## 2. Claims You Can Make (with evidence)

| Claim | Evidence |
|---|---|
| Cost-sensitive policy outperforms strongest baseline | 0.007566 vs 0.017543, 56.87% reduction |
| Result is not statistical noise | Bootstrap CI [52.77%, 60.91%], excludes zero |
| Result is robust to cost assumptions | Min advantage 46.46% across 2× range on 3 parameters |
| Result does not depend on test-set tuning | fraud_loss_rate derived from train window |
| Calibration is adequate without post-hoc fix | ECE = 0.0040, below 0.05 threshold |
| Censored labels excluded, not treated as negative | 96,843 month-7 rows marked and excluded |
| Splits are temporal, not random | Chronological split; split.py asserts sum |
| Pipeline reproduces from one command | `python -m src.pipeline` byte-for-byte |
| Static threshold is near-null at this base rate | Static-0.5 reduces cost 7.3% vs approve-all |

---

## 3. Claims You CANNOT Make (avoid these)

| Do NOT say | Why |
|---|---|
| "High accuracy" | Accuracy is meaningless at 1.26% base rate and is a forbidden metric (evaluation_protocol.md §8.6) |
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

At decision time, a LightGBM classifier produces a fraud probability for
each transaction. A cost-sensitive policy then selects the action —
approve, review, or block — that minimizes expected cost under a fixed
cost matrix, with transaction amount scaling the fraud loss term.

---

## 5. What Was NOT Done (state in Limitations)

- Single delay regime (1 month); no 2-month or 3-month
- No hyperparameter tuning; LightGBM defaults
- No calibration adjustment (ECE already below threshold)
- No capacity constraint on review queue
- Amount proxy = proposed_credit_limit; BAF has no clean amount column
- No bootstrap CIs on the sensitivity runs (only on the main comparison)
- No rule-based baseline (deferred; 5 baselines implemented, not 6)
- Synthetic data; results are not production estimates

---

## 6. Section → Source Doc Map

| Paper section | Read this |
|---|---|
| Introduction | problem_framing.md §1–4 |
| Related Work | (paper team must write; cite Elkan 2001, Chapelle 2014, Jesus 2022) |
| Methodology | decision_policy.md §5–6 |
| Dataset | data_card.md §2–5 |
| Experimental Setup | evaluation_protocol.md §7–9 |
| Results | reports/mvp_backtest.md + reports/bootstrap.md + reports/sensitivity.md |
| Discussion | reports/mvp_backtest.md §Interpretation |
| Limitations | reports/mvp_backtest.md §Limitations |
| Conclusion | roadmap.md §5–7 |
| References | (paper team must build) |