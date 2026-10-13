# Protocol — Capacity-Aware Decision Policy

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Document:** Phase B protocol — capacity-aware policy
> **Status:** v1.0 — draft, gates `src/policy/decide_capacity.py`
> **Last updated:** 2026-10-03
> **Earned by:** H1 survived (`reports/v2/intermediate/h1_capacity.json`)
> **Governing documents:** `docs/decision_policy.md` §8,
> `docs/v2/evaluation_framework.md` §5.1, §6.1,
> `docs/v2/falsification_plan.md` §3 H1, §11

---

## 0. Why This Protocol Exists

Per `falsification_plan.md` §3 H1's "If survives" clause, H1's survival
authorizes exactly one Phase B build: a capacity-aware decision policy.
This document specifies the protocol **before** implementation. No code
is written until this file is reviewed.

**Rule:** The argmin rule from `docs/decision_policy.md` §5.4 remains
the source of truth. Capacity is an override on review routing, not a
replacement for the argmin rule.

**Rule:** No classifier is retrained. No test-window score is
recomputed. This protocol operates on frozen
`data/processed/scored_test.parquet`.

---

## 1. Inputs

- `data/processed/scored_test.parquet` — frozen `p_fraud`, `amount_proxy`
- `configs/costs.yaml` — frozen cost matrix
- `configs/policy.yaml` — new; defines `capacity_per_window`
- `src/policy/decide.py` — `choose_actions()` reused unchanged

---

## 2. Semantics

A capacity `K` is the maximum number of transactions that may be routed
to `review` in one window. The window is the evaluation window (the
test window for the H1 diagnostic; a configured time window in
production).

Capacity does **not** modify the expected costs. It modifies only which
review-band transactions are actually reviewed.

---

## 3. Algorithm

Given `p`, `costs`, `amounts`, and `K`:

1. Compute the three per-row expected costs
   (`c_approve`, `c_review`, `c_block`) using
   `src/policy/decide.py` `choose_actions()`. Do not re-implement.
2. Identify the review band: rows where the unconstrained argmin is
   `review`.
3. If `|review_band| <= K`, route every review-band row to `review`.
   Done.
4. Otherwise, rank review-band rows by **savings of review vs the
   next-best non-review action**:
   ```
   savings = min(c_approve, c_block) - c_review
   ```
   Descending. Ties broken by `transaction_id` ascending. Keep top-K
   in review.
5. Overflow rows are routed by the two-action argmin:
   ```
   action = approve if c_approve <= c_block else block
   ```
6. Rows not in the review band keep their unconstrained argmin action.

**Note on the ranking formula.** The pre-registered formula was
`p_fraud * fraud_loss(amount) - review_cost`
(`falsification_plan.md` §11). It was amended on 2026-10-03, before H1
executed, to `min(c_approve, c_block) - c_review`. The amendment is
recorded in `falsification_plan.md` §11. This protocol uses the amended
formula.

---

## 4. Config Schema — `configs/policy.yaml`

```yaml
capacity_per_window: 227491   # integer; number of reviews allowed per window
                              # 227491 = 100% of V1 test window (unconstrained)
                              # 4550  = 2% (kill-zone minimum for H1)
                              # null  = unconstrained (V1 behavior)
```

**Rule:** `capacity_per_window` is a config value. It is not tuned on
the test window. If it is changed, the change is a new experiment with
its own reported result.

---

## 5. Verification Plan

- [ ] Unit tests for `_apply_capacity` boundary cases:
  - `K >= |review_band|` (unconstrained behavior preserved)
  - `K == 0` (no reviews; all review-band rows overflow to two-action argmin)
  - empty review band (no changes)
  - ties in `savings` broken deterministically
- [ ] Re-run H1's diagnostic using `src/policy/decide_capacity.py`; the
  verdict must match `h1_capacity.json`
- [ ] Confirm 100% capacity reproduces V1's unconstrained policy cost
  (0.007491) exactly
- [ ] Confirm no classifier is retrained and no test score is
  recomputed

---

## 6. Integration

- `docs/decision_policy.md` §8 moves from "specification, deferred" to
  "implemented" once this protocol is implemented.
- `configs/policy.yaml` is added. It is the first new config file since
  V1. Its existence is documented in `docs/v2/documentation_map.md`.
- `reports/v2_falsification.md` receives an addendum section after
  Phase B.

---

## 7. What This Protocol Does Not Do

- It does not re-tune the cost matrix.
- It does not retrain the classifier.
- It does not modify the argmin rule.
- It does not add a fairness constraint.
- It does not model a review-time budget in wall-clock time (window is
  a row count in the current implementation; a wall-clock window is a
  future extension).
- It does not alter the frozen test window.

---

## 8. Definition of Done

- [ ] `src/policy/decide_capacity.py` implemented
- [ ] `configs/policy.yaml` added with documented schema
- [ ] Unit tests cover the boundary cases in §5
- [ ] H1 re-run reproduces the JSON verdict
- [ ] `docs/decision_policy.md` §8 updated
- [ ] `reports/v2_falsification.md` Phase B addendum written
- [ ] `git status` clean