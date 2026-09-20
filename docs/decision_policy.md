# Decision Policy

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** Decision Policy  
> **Status:** v0.2 — LOCKED before modeling  
> **Last updated:** YYYY-MM-DD

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
| Review capacity | `capacity` | Ops config | Yes (optional in Week 1) |

All cost inputs come from `configs/costs.yaml`. They are fixed for a given experiment and never tuned on the test set.

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

Using Week 1 defaults:

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
p < 0.0286              → approve
0.0286 <= p < 0.20      → review
p >= 0.20               → block
```

These are the Week 1 defaults. They are documented so any change is visible.

### 6.5 Threshold Edge Cases

The threshold presentation in Section 6.3 is a convenience, not the definition. The **argmin rule in Section 5.4 is always well-defined**, even when the thresholds degenerate. Three cases must be handled explicitly in code and reported in the Week 1 report.

**Case A — `fraud_loss <= residual_fraud_loss`.**  
Denominator of `p_review` is zero or negative. Review is never cheaper than approve for any `p ≥ 0`. The review band is empty. The policy reduces to an approve-vs-block decision:

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

---

## 7. Amount Sensitivity

The Week 1 policy treats `fraud_loss` as a constant. This is a simplification.

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

### 7.1 Week 1 Rule

- **Default:** constant `fraud_loss` in `configs/costs.yaml`, with `amount_scaled: false`.
- **Required:** an amount-scaled sensitivity analysis in the Week 1 report (`amount_scaled: true`, `fraud_loss_rate > 0`).
- The sensitivity analysis must report whether the ranking of baselines changes when amount-scaled costs are used.
- If the ranking changes, this must be documented as a limitation of the constant-loss default.

This aligns with `evaluation_protocol.md` v0.2 Section 12.

### 7.2 Out-of-Scope Cost Realism

`false_positive_cost` is also plausibly proportional to `amount` (lost revenue, customer value). Week 1 does not model this. It is named here so it is not a hidden assumption, and it is a candidate for the Week 2 sensitivity analysis.

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

### 8.3 Week 1 Rule

Capacity simulation is **optional** in Week 1.  
If included, it must be reported as a **separate experiment**, not mixed into the Week 1 baseline.  
`capacity_enabled: false` is the default in `configs/policy.yaml`.

Budget-constrained **ranking** metrics (top 1% / 5% / 10%) are reported in Week 1 per `evaluation_protocol.md` v0.2 Section 10. Those are not the same as capacity-aware decisioning.

---

## 9. Calibration Requirement

The policy assumes `p` is a real probability.

If `p` is uncalibrated:

- Expected costs are wrong
- Thresholds derived from costs are wrong
- Cost-based decisions are wrong

### 9.1 Week 1 Rule

- Measure calibration with Brier score and ECE
- If ECE is high, apply Platt scaling or isotonic regression on validation data
- Never apply calibration fit on test data
- Report calibration before and after

### 9.2 Cadence

Recalibrate whenever the model is retrained or when calibration drifts beyond a threshold defined in the evaluation protocol.

---

## 10. Action Logging

Every decision must be logged for audit and backtest.

### 10.1 Schema

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

### 10.2 Why Log All Three Costs

- Debugging: shows why the action was chosen
- Sensitivity: allows re-scoring under different cost matrices without re-running the model
- Fairness: allows auditing whether one action dominates for a subgroup
- The `cost_config_hash` makes it unambiguous which cost matrix produced each decision

### 10.3 Labels Are Not in the Action Log

`y_true` and `label_time` are **not** columns of the action log. They are joined in the backtest, only for transactions whose labels have matured by `test_end`. This preserves the audit trail as a pure decision record.

### 10.4 Storage

- Week 1: `data/processed/action_log.parquet`
- No database in Week 1

---

## 11. Failure Modes

The policy is simple, but it can still fail. Name them now.

| Failure mode | Cause | Symptom |
|---|---|---|
| Uncalibrated `p` | Model outputs uncalibrated scores | Costs and thresholds wrong |
| Wrong cost matrix | Costs do not reflect reality | Policy picks wrong action |
| Constant fraud loss | Amount ignored | Large transactions under-protected |
| Degenerate thresholds | `fraud_loss <= residual_fraud_loss` or `p_review >= p_block` | Review band empty or misleading |
| Capacity ignored | Review queue overflows | Latency and backlog |
| Threshold tuning on test | Retro-fitting to results | Leakage, invalid comparison |
| Feedback loop | Policy changes labels | Observed labels biased |
| Segment disparity | Costs differ by segment | Policy unfair or ineffective |
| Adversarial adaptation | Fraudsters learn thresholds | Drift |

Each of these is a candidate for Week 2–4 work. None is solved by Week 1.

---

## 12. What This Policy Is Not

- It is not a learned policy (no bandits, no RL)
- It is not a ranking policy (top-N by score is a separate ranking problem)
- It is not a capacity-aware scheduler
- It is not a causal policy (no counterfactual treatment effect)
- It is not a fairness-aware policy (no group constraints)

Those are extensions, not Week 1 requirements.

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

**Canonical key:** the residual loss after review is `residual_fraud_loss` in `configs/costs.yaml`. Any earlier use of `residual_fraud_loss_after_review` in `evaluation_protocol.md` should be treated as the same quantity and aligned.

If the two documents disagree, the evaluation protocol wins and this document is updated.

---

## 14. Configuration

### 14.1 `configs/costs.yaml`

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: false
fraud_loss_rate: 0.0
```

### 14.2 `configs/policy.yaml`

```yaml
use_derived_thresholds: true
p_review: null       # null → derive from costs
p_block: null        # null → derive from costs
capacity_enabled: false
review_capacity_per_day: 1000
```

If `p_review` and `p_block` are provided explicitly, they override derived thresholds. This is allowed only for sensitivity analysis and must be reported as such.

---

## 15. Week 1 Definition of Done

- [ ] Actions defined: approve / review / block
- [ ] Expected cost formulas implemented in `src/policy/decide.py`
- [ ] Argmin rule implemented as the source of truth
- [ ] Derived thresholds computed from costs and reported as a diagnostic view only
- [ ] Threshold edge cases (Section 6.5) handled and covered by a unit test
- [ ] Cost matrix in `configs/costs.yaml` with canonical key `residual_fraud_loss`
- [ ] Policy config in `configs/policy.yaml`
- [ ] Action log written to `data/processed/action_log.parquet`
- [ ] Action log schema matches Section 10, including `cost_config_hash`
- [ ] Calibration measured and reported: Brier and ECE
- [ ] Policy evaluated under all three delay regimes
- [ ] Policy compared against the canonical baseline set: random, approve-all, block-all, rule-based, LightGBM + static threshold
- [ ] Amount-scaled fraud loss sensitivity analysis run and reported
- [ ] Failure modes documented in the Week 1 report

---

## 16. Changelog

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | Initial decision policy | Project start |
| YYYY-MM-DD | Added threshold edge cases; made amount-scaled loss a required Week 1 sensitivity; added `cost_config_hash` to log schema; declared canonical `residual_fraud_loss` key; aligned baselines | Align with problem framing v0.2, data card v0.2, and evaluation protocol v0.2 |

---

## 17. Guiding Rule

> A model is only useful if the policy it feeds produces **lower realized cost** than the baselines, under the **same temporal split, delay regime, cost matrix, and budget**.

The policy is the product. The model is an input to it.
