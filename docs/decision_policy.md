# Decision Policy

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** Decision Policy  
> **Status:** v0.3 — applied to MVP build (2026-09-21)  
> **Last updated:** 2026-09-21

---

## 1. Purpose

This document defines **how a fraud score becomes an action**.

It exists because a fraud model does not make decisions. A **policy** does. The policy maps a predicted probability `p` and a cost structure into one of three actions:

```text
approve
review
block
```

The model is evaluated by the **policy it feeds**, not by its AUC.

**Rule:** Write the policy before the model. If the model changes the policy retroactively, the policy was wrong or the model is being overfit to the metric.

---

## 2. Why a Policy Is Needed

A fraud score alone is not actionable.

Given `p = 0.03`, should the system approve, review, or block?

- The answer depends on transaction amount.
- It depends on the cost of a false positive.
- It depends on the cost of a review.
- It depends on investigator capacity.
- It depends on fraud loss if approved.

Without an explicit policy, thresholds are chosen arbitrarily or tuned to make the model look good. Both are failure modes.

The policy makes the tradeoff **explicit, auditable, and cost-based**.

---

## 3. Actions

| Action | Meaning | Customer impact | Operational cost |
|---|---|---|---|
| `approve` | Let the transaction proceed | None | None if legit, fraud loss if fraud |
| `review` | Hold for manual/async review | Delay, friction | Review cost + residual fraud loss |
| `block` | Decline the transaction | High friction, potential churn | False-positive cost if legit |

Three actions are used because:

- `approve` and `block` alone ignore review as an option
- Review is where most real fraud operations live
- Three actions expose the capacity problem directly

---

## 4. Inputs

The policy consumes the following per transaction:

| Input | Symbol | Source | Available at decision time |
|---|---|---|---|
| Predicted fraud probability | `p` | Model | Yes |
| Transaction amount | `amount` | Transaction | Yes |
| Fraud loss | `fraud_loss` | Cost config | Yes |
| False-positive cost | `false_positive_cost` | Cost config | Yes |
| Review cost | `review_cost` | Cost config | Yes |
| Residual fraud loss after review | `residual_fraud_loss` | Cost config | Yes |
| Review capacity | `capacity` | Ops config | Deferred — not used in MVP |

All cost inputs come from `configs/costs.yaml`. They are fixed for a given experiment and never tuned on the test set.

Capacity is defined here for completeness but **not exercised in the MVP**. There is no `configs/policy.yaml`; capacity is deferred to post-MVP work.

---

## 5. Expected Cost Formulation

For each transaction, the policy computes the expected cost of each action and selects the minimum.

### 5.1 Approve

```text
E[cost(approve)] = p * fraud_loss
```

- If the transaction is fraud (`y=1`), the system loses `fraud_loss`.
- If the transaction is legit (`y=0`), the system loses nothing at decision time.

### 5.2 Review

```text
E[cost(review)] = review_cost + p * residual_fraud_loss
```

- `review_cost` is always paid.
- If the transaction is fraud, a fraction of the fraud loss is still incurred because review is imperfect.

### 5.3 Block

```text
E[cost(block)] = (1 - p) * false_positive_cost
```

- If the transaction is legit (`y=0`), the system pays the friction cost.
- If the transaction is fraud (`y=1`), blocking is correct and costs nothing extra at decision time.

### 5.4 Decision Rule

```text
action = argmin over {approve, review, block} of E[cost(action)]
```

This is the entire policy. It is intentionally simple.

**Implementation note:** in `src/policy/decide.py`, this rule is exposed as a pure function `choose_actions(p, costs, amounts=None)` so it can be tested without file I/O. The pipeline calls this function; the tests call the same function. There is one implementation of the argmin rule, not two.

---

## 6. Derived Thresholds

The argmin rule implies two thresholds on `p`, given fixed costs and amount.

### 6.1 Review vs Approve

Review becomes cheaper than approve when:

```text
review_cost + p * residual_fraud_loss  <  p * fraud_loss
```

Solving for `p`:

```text
p > review_cost / (fraud_loss - residual_fraud_loss)
```

Call this `p_review`.

### 6.2 Block vs Review

Block becomes cheaper than review when:

```text
(1 - p) * false_positive_cost  <  review_cost + p * residual_fraud_loss
```

Solving for `p`:

```text
p > (false_positive_cost - review_cost) / (false_positive_cost + residual_fraud_loss)
```

Call this `p_block`.

### 6.3 Resulting Policy

```text
if p < p_review:                 approve
elif p < p_block:                review
else:                            block
```

These thresholds are **derived**, not tuned. If costs change, thresholds change automatically.

### 6.4 Example Values

Using the constant-loss cost matrix:

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
```

Then:

```text
p_review = 0.02 / (1.0 - 0.3)           = 0.0286
p_block  = (0.1 - 0.02) / (0.1 + 0.3)   = 0.20
```

Policy:

```text
p < 0.0286              -> approve
0.0286 <= p < 0.20      -> review
p >= 0.20               -> block
```

These are the constant-loss defaults. They hold when `amount_scaled: false`. When amount scaling is enabled, the thresholds become amount-dependent (see Section 7) and this fixed-threshold view is a diagnostic only.

**Observed in the MVP:** under constant loss, the policy produced `p_review=0.0286` and `p_block=0.2000` on the test set, matching the derivation exactly. The action distribution was 210,734 approve / 15,124 review / 1,633 block.

### 6.5 Threshold Edge Cases

The threshold presentation in Section 6.3 is a convenience, not the definition. The **argmin rule in Section 5.4 is always well-defined**, even when the thresholds degenerate. Three cases must be handled explicitly in code and reported in the Week 1 report.

**Case A — `fraud_loss <= residual_fraud_loss`.**  
Denominator of `p_review` is zero or negative. Review is never cheaper than approve for any `p >= 0`. The review band is empty. The policy reduces to an approve-vs-block decision:

```text
approve if  p * fraud_loss < (1 - p) * false_positive_cost
block otherwise
```

This is a sign that the cost matrix is inconsistent (review is as bad as or worse than doing nothing). The config should be rejected before modeling, not silently accepted.

**Case B — `p_review >= p_block`.**  
The review band is empty: for `p` in `[p_block, p_review)` the threshold rule would say `approve`, but block is cheaper. The argmin rule handles this correctly; the threshold rule does not. Implement the argmin rule, not the threshold rule.

**Case C — thresholds outside `[0, 1]`.**  
If `p_review < 0` or `p_block > 1`, the corresponding band vanishes. The argmin rule still applies. Do not clip thresholds. Report any regime where this occurs.

**Rule:** implement Section 5.4 as the source of truth. Use Section 6.3 only as a diagnostic view for the Week 1 report.

**Coverage:** all three cases are covered by unit tests in `tests/test_policy.py` (`test_edge_case_a_*`, `test_edge_case_b_*`, `test_edge_case_c_*`). All pass. The tests assert that the argmin produces the minimum of the three expected costs at every `p`, not that the threshold rule produces a particular answer. This is the correct behavior when the thresholds degenerate.

---

## 7. Amount Sensitivity

The constant-loss policy treats `fraud_loss` as fixed. This is a simplification.

In reality, `fraud_loss` scales with `amount`:

```text
fraud_loss(amount) = amount * fraud_loss_rate
```

If amount-scaled costs are used, the review-vs-approve threshold becomes amount-dependent:

```text
p_review(amount) = review_cost / (amount * fraud_loss_rate - residual_fraud_loss)
```

and the block-vs-review threshold becomes:

```text
p_block(amount) = (false_positive_cost - review_cost) / (false_positive_cost + residual_fraud_loss)
```

The same edge cases from Section 6.5 apply, plus the additional case where `amount * fraud_loss_rate <= residual_fraud_loss`, in which review is never cheaper than approve.

### 7.1 MVP Result — Amount Scaling Adopted

The amount-scaled sensitivity analysis required by `architecture.md` §9.2 was run on 2026-09-21.

**Setup:**
- `amount_scaled: true`
- `fraud_loss_rate = 0.002067377733397323` (chosen so that `mean(fraud_loss_rate * amount_proxy) = 1.0` on the test set, keeping the comparison apples-to-apples with constant loss)
- Same model, same split, same test set. Only the cost assumption changed.

**Stop criterion (`architecture.md` §9.2):**
- Flips >= 2% of decisions, OR
- Cost per transaction changes by >= 1% relative.

**Measured result:**

| Config | Policy cost/txn | Strongest baseline | Policy advantage |
|---|---:|---:|---:|
| Constant `fraud_loss` | 0.008901 | 0.012088 | 26.4% |
| Amount-scaled | **0.007777** | 0.018892 | **58.8%** |

- Decision flips: 5,542 / 227,491 = **2.44%** (all approve -> review on large transactions)
- Cost/txn change: **-12.6%** relative

**Verdict: success stop.** Amount scaling is adopted as the new default. Both thresholds were exceeded, and the policy's advantage over the strongest baseline nearly doubled.

**Mechanism:** with per-row `fraud_loss`, the approve expected cost `p * amount * rate` grows for large transactions, so the argmin routes them to review. Under constant loss those same transactions were approved. The policy is exploiting signal the constant-loss version was leaving on the table.

### 7.2 Out-of-Scope Cost Realism

`false_positive_cost` is also plausibly proportional to `amount` (lost revenue, customer value). The MVP does not model this. It is named here so it is not a hidden assumption, and it is a candidate for post-MVP work.

---

## 8. Capacity Override

Real systems have finite review capacity. If the review queue is full, the policy must adapt.

### 8.1 Rule

If the number of transactions in the review band exceeds `capacity` per time window:

```text
keep the top-K by expected savings (p * fraud_loss - review_cost)
route the rest by the block-vs-approve decision only
```

### 8.2 Purpose

- Prevent review queue overflow
- Make the capacity tradeoff explicit
- Expose how much value is lost when capacity is constrained

### 8.3 MVP Rule

Capacity simulation is **out of scope for the MVP**. There is no `configs/policy.yaml` and no `capacity_enabled` flag in the current code. The section is preserved as a specification for post-MVP work.

Budget-constrained **ranking** metrics (top 1% / 5% / 10%) are reported in the backtest per `evaluation_protocol.md` §10. Those are ranking metrics, not capacity-aware decisioning. They do not modify the policy's actions; they report on the top slice of the scored test set as it stands.

---

## 9. Calibration Requirement

The policy assumes `p` is a real probability.

If `p` is uncalibrated:

- Expected costs are wrong
- Thresholds derived from costs are wrong
- Cost-based decisions are wrong

### 9.1 MVP Result

Calibration was measured on the validation set on 2026-09-21 using the diagnostic in `src/evaluation/calibration.py`.

| Metric | Value |
|---|---:|
| ECE (10 quantile bins) | **0.0040** |
| Brier (model) | 0.010050 |
| Brier (trivial, predict val mean) | 0.010103 |
| Brier gain over trivial | 0.52% |

**Stop criterion (`architecture.md` §9.2):** ECE < 0.05 -> null stop.

**Verdict: null stop.** ECE of 0.0040 is well below the 0.05 threshold. No calibration step (Platt, isotonic, or otherwise) was applied. Raw LightGBM output is used by the policy directly.

**Reliability note:** the reliability table shows the model is very well calibrated across bins 0-8 (where 90% of transactions live). It is mildly overconfident in the top decile (bin 9: mean predicted 9.5%, actual 7.0%), but those scores fall inside the review band and do not affect block decisions. This is documented, not corrected — correcting it would be a change without a measured failure justifying it.

### 9.2 Cadence

Recalibrate whenever the model is retrained or when calibration drifts beyond a threshold defined in the evaluation protocol. The ECE diagnostic is not part of the pipeline; run it manually after retraining.

---

## 10. Action Logging

Every decision must be logged for audit and backtest.

### 10.1 Schema — MVP vs. Full

The full action log schema in Section 10.1.1 (below) is the specification. The MVP implements a **strict subset**, shown in Section 10.1.2, because three of the columns require capabilities the MVP deliberately does not include (`cost_config_hash`, per-row `amount`, `decision_time`).

#### 10.1.1 Full schema (post-MVP specification)

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | string | Join key |
| `decision_time` | timestamp | When decision was made |
| `amount` | float | Transaction value |
| `p_fraud` | float | Model output |
| `action` | enum | approve / review / block |
| `expected_cost_approve` | float | For audit |
| `expected_cost_review` | float | For audit |
| `expected_cost_block` | float | For audit |
| `chosen_expected_cost` | float | Min of the three |
| `reason` | string | e.g., "p > p_block" |
| `cost_config_hash` | string | Hash of `configs/costs.yaml` used for the decision |

#### 10.1.2 MVP schema (as implemented)

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | int | Join key |
| `month` | int | For grouping |
| `p_fraud` | float | Model output |
| `action` | string | approve / review / block |
| `expected_cost_approve` | float | For audit |
| `expected_cost_review` | float | For audit |
| `expected_cost_block` | float | For audit |
| `chosen_expected_cost` | float | Min of the three |
| `reason` | string | Fixed string `"argmin_expected_cost"` in the MVP |

**MVP omissions and why:**

- `decision_time` — BAF has only month-level granularity; a per-row timestamp would be fabricated.
- `amount` — `amount_proxy` lives in `scored_test.parquet` and is joined in the backtest, not duplicated into the log.
- `cost_config_hash` — the MVP runs one cost matrix; there is nothing to disambiguate. Add it post-MVP when multiple cost configs are in play.

### 10.2 Why Log All Three Costs

- Debugging: shows why the action was chosen
- Sensitivity: allows re-scoring under different cost matrices without re-running the model
- Fairness: allows auditing whether one action dominates for a subgroup

In the MVP, the three expected costs are what makes the amount-scaled sensitivity possible without re-running the model. This is exactly the use case anticipated here.

### 10.3 Labels Are Not in the Action Log

`y_true` and `label_time` are **not** columns of the action log. They are joined in the backtest, only for transactions whose labels have matured by `test_end`. This preserves the audit trail as a pure decision record.

### 10.4 Storage

- MVP: `data/processed/action_log.parquet`
- No database.

---

## 11. Failure Modes

The policy is simple, but it can still fail. Name them now.

| Failure mode | Cause | Symptom | MVP status |
|---|---|---|---|
| Uncalibrated `p` | Model outputs uncalibrated scores | Costs and thresholds wrong | Measured; ECE = 0.0040, no failure |
| Wrong cost matrix | Costs do not reflect reality | Policy picks wrong action | Only amount scaling tested; full sensitivity deferred |
| Constant fraud loss | Amount ignored | Large transactions under-protected | Addressed — amount scaling adopted |
| Degenerate thresholds | `fraud_loss <= residual_fraud_loss` or `p_review >= p_block` | Review band empty or misleading | Covered by tests; not triggered by MVP cost config |
| Capacity ignored | Review queue overflows | Latency and backlog | Out of MVP scope |
| Threshold tuning on test | Retro-fitting to results | Leakage, invalid comparison | Not done — thresholds derived, never tuned |
| Feedback loop | Policy changes labels | Observed labels biased | Out of MVP scope; BAF is a static dataset |
| Segment disparity | Costs differ by segment | Policy unfair or ineffective | Out of MVP scope |
| Adversarial adaptation | Fraudsters learn thresholds | Drift | Out of MVP scope |

Each unresolved item is a candidate for post-MVP work. None is claimed as solved.

---

## 12. What This Policy Is Not

- It is not a learned policy (no bandits, no RL)
- It is not a ranking policy (top-N by score is a separate ranking problem)
- It is not a capacity-aware scheduler
- It is not a causal policy (no counterfactual treatment effect)
- It is not a fairness-aware policy (no group constraints)

Those are extensions, not MVP requirements.

---

## 13. Relationship to Evaluation Protocol

The evaluation protocol measures **realized cost** of the policy.

The policy defines:

- What actions exist
- How actions are chosen
- What expected costs are

The evaluation protocol defines:

- How realized cost is computed
- Which baselines are compared
- Which budgets are reported

The two documents must agree on:

- Cost matrix values
- Action set
- Decision rule
- Canonical config key names

**Canonical key:** the residual loss after review is `residual_fraud_loss` in `configs/costs.yaml`.

**MVP verification:** both documents describe the same action set (approve / review / block), the same decision rule (argmin of expected cost), and the same cost matrix keys. Amount scaling was added to both `configs/costs.yaml` and the policy code; the evaluation protocol's sensitivity requirement was satisfied by the same change. No disagreement remains.

If the two documents disagree in future, the evaluation protocol wins and this document is updated.

---

## 14. Configuration

### 14.1 `configs/costs.yaml` — as implemented

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: true
fraud_loss_rate: 0.002067377733397323
```

The first four keys are the constant-loss cost matrix. `amount_scaled` and `fraud_loss_rate` were added after the constant-loss MVP was validated and the amount-scaled sensitivity returned a success stop. See Section 7.1.

### 14.2 `configs/policy.yaml` — not implemented

The full architecture envisions a `configs/policy.yaml` for threshold overrides and capacity settings. The MVP does not implement it. There is no `use_derived_thresholds`, `p_review`, `p_block`, `capacity_enabled`, or `review_capacity_per_day` in the code.

Thresholds are always derived from the cost matrix — there is no override mechanism. Capacity is deferred.

This section is preserved as a specification for post-MVP work. Do not create `configs/policy.yaml` until there is a measured failure that requires it.

---

## 15. MVP Definition of Done

- [x] Actions defined: approve / review / block
- [x] Expected cost formulas implemented in `src/policy/decide.py`
- [x] Argmin rule implemented as the source of truth (as `choose_actions`)
- [x] Derived thresholds computed from costs and reported as a diagnostic view only
- [x] Threshold edge cases (Section 6.5) handled and covered by unit tests
- [x] Cost matrix in `configs/costs.yaml` with canonical key `residual_fraud_loss`
- [ ] Policy config in `configs/policy.yaml` — **out of MVP scope**, deferred
- [x] Action log written to `data/processed/action_log.parquet`
- [ ] Action log schema matches full Section 10.1.1, including `cost_config_hash` — **MVP schema is a documented subset**, see Section 10.1.2
- [x] Calibration measured and reported: Brier (0.010050) and ECE (0.0040), null stop
- [ ] Policy evaluated under all three delay regimes — **only 1-month run in MVP**, deferred
- [x] Policy compared against the canonical baseline set: random, approve-all, block-all, LightGBM + static 0.5
- [ ] Rule-based threshold baseline — **not in MVP per `mvp_architecture.md` §8**, deferred
- [x] Amount-scaled fraud loss sensitivity analysis run and reported — success stop, adopted
- [x] Failure modes documented in the Week 1 report and in Section 11 above

**Result:** every applicable box checked. Deferred items are documented as deferred, not omitted.

---

## 16. Changelog

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | Initial decision policy | Project start |
| YYYY-MM-DD | Added threshold edge cases; made amount-scaled loss a required Week 1 sensitivity; added `cost_config_hash` to log schema; declared canonical `residual_fraud_loss` key; aligned baselines | Align with problem framing v0.2, data card v0.2, and evaluation protocol v0.2 |
| 2026-09-21 | Updated status to v0.3; recorded amount-scaled sensitivity as adopted (Section 7.1); recorded ECE diagnostic as null stop (Section 9.1); documented MVP action log as a subset of the full schema (Section 10.1.2); marked capacity and multi-regime as deferred (Sections 8.3, 15); noted `configs/policy.yaml` was not implemented | Reconcile document with the built MVP |

---

## 17. Guiding Rule

> A model is only useful if the policy it feeds produces **lower realized cost** than the baselines, under the **same temporal split, delay regime, cost matrix, and budget**.

The policy is the product. The model is an input to it.
