# Decision Policy

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Decision Policy  
> **Status:** v1.0 — first-principles revision; the policy is the object of study  
> **Last updated:** 2026-09-24

---

## 0. Derivation From Problem Framing

This document defines the decision policy that is the **object of study** of
the project. It is derived from `docs/problem_framing.md` §3 (decomposition),
§5 (objective function), and §7 (system). It is evaluated by
`docs/evaluation_protocol.md` v1.0.

**Rule:** If a component of this policy cannot be traced to a sentence in
`problem_framing.md`, it is either wrong or the framing is incomplete.

**Rule:** The evaluation protocol defines how this policy is measured. If
the two documents disagree about actions, decision rule, or cost matrix
keys, the evaluation protocol wins and this document is updated.

This revision replaces v0.4, which framed the policy as a "supplementary
analysis" layered on top of a "primary classification deliverable." That
framing was inherited from course deliverables, not from the problem. It is
reversed here. The policy is the product. The classifier is an input.

---

## 1. Purpose

A fraud model does not make decisions. A **policy** does.

This document defines how a calibrated probability `p = P(fraud | X_t)` and
a frozen cost matrix become one of three actions:

```text
approve
review
block
```

The classifier is evaluated by the **policy it feeds**, not by its own
classification metrics. A classifier with a higher macro F1 but a worse
policy cost is a worse classifier **for this project**.

**Rule:** Write the policy before the model. If the model changes the policy
retroactively, the policy was wrong, or the model is being overfit to a
metric that is not the objective.

**Rule:** The policy is not tuned. Thresholds are derived from the cost
matrix. Tuning thresholds on validation or test data is forbidden by the
evaluation protocol.

---

## 2. Why a Policy Is Needed

A fraud score alone is not actionable.

Given `p = 0.03`, should the system approve, review, or block?

- The answer depends on transaction amount.
- It depends on the cost of a false positive.
- It depends on the cost of a review.
- It depends on fraud loss if approved.
- It depends on residual fraud loss if reviewed.

Without an explicit policy, thresholds are chosen arbitrarily or tuned to
make a metric look good. Both are failure modes. The policy makes the
tradeoff **explicit, auditable, and cost-based**.

This is the structural consequence of `problem_framing.md` §2: a decision
must be made before the label arrives, and both error types have real costs.
A classifier that ignores this produces a ranked list, not a decision.

---

## 3. Actions

| Action | Meaning | Customer impact | Operational cost |
|---|---|---|---|
| `approve` | Let the transaction proceed | None | `0` if legit, `fraud_loss` if fraud |
| `review` | Hold for manual or async review | Delay, friction | `review_cost + residual_fraud_loss` if fraud, `review_cost` if legit |
| `block` | Decline the transaction | High friction, churn risk | `0` if fraud, `false_positive_cost` if legit |

Three actions are used because:

- `approve` and `block` alone ignore review, which is where most real fraud
  operations live.
- Review is not free and not unlimited; the three-action formulation exposes
  the capacity tradeoff directly.
- A three-action policy can express a decision that a binary classifier
  cannot: "this is uncertain enough to warrant investigation."

---

## 4. Inputs

The policy consumes the following per transaction:

| Input | Symbol | Source | Available at decision time |
|---|---|---|---|
| Predicted fraud probability | `p` | Calibrated classifier | Yes |
| Transaction amount | `amount` | Transaction (`amount_proxy` = `proposed_credit_limit`) | Yes |
| Fraud loss | `fraud_loss` | `configs/costs.yaml` | Yes |
| False-positive cost | `false_positive_cost` | `configs/costs.yaml` | Yes |
| Review cost | `review_cost` | `configs/costs.yaml` | Yes |
| Residual fraud loss after review | `residual_fraud_loss` | `configs/costs.yaml` | Yes |
| Review capacity | `capacity` | Ops config | **Deferred — not used** |

All cost inputs come from `configs/costs.yaml`. They are **frozen** for the
duration of the experiment and are never tuned on validation or test data.
Changing the cost matrix is a new experiment with its own reported result.

**Calibration requirement:** `p` must be a real probability. The evaluation
protocol (§7) defines the gate: ECE < 0.05 on the validation window, or a
documented calibration step must bring it below. An uncalibrated `p`
produces wrong expected costs, and therefore wrong decisions.

Capacity is defined here for completeness but is **not exercised in the
current build**. There is no `configs/policy.yaml`; capacity is deferred to
future work (see §8).

---

## 5. Expected Cost Formulation

For each transaction, the policy computes the expected cost of each action
and selects the minimum.

### 5.1 Approve

```text
E[cost(approve)] = p * fraud_loss(amount)
```

- If the transaction is fraud (`y=1`), the system loses `fraud_loss(amount)`.
- If the transaction is legit (`y=0`), the system loses nothing at decision
  time.

### 5.2 Review

```text
E[cost(review)] = review_cost + p * residual_fraud_loss
```

- `review_cost` is always paid.
- If the transaction is fraud, a fraction of the fraud loss is still
  incurred, because review is imperfect.

### 5.3 Block

```text
E[cost(block)] = (1 - p) * false_positive_cost
```

- If the transaction is legit (`y=0`), the system pays the friction cost.
- If the transaction is fraud (`y=1`), blocking is correct and costs nothing
  extra at decision time.

### 5.4 Decision Rule

```text
action* = argmin over {approve, review, block} of E[cost(action)]
```

This is the entire policy. It is intentionally simple.

**Implementation note:** in `src/policy/decide.py`, this rule is exposed as
a pure function `choose_actions(p, costs, amounts=None)` so that it can be
tested without file I/O. The pipeline calls this function; the tests call
the same function. There is exactly one implementation of the argmin rule.

**Source of truth:** the argmin rule is the source of truth. The derived
thresholds in §6 are a **diagnostic view** used for reporting. When the
thresholds degenerate (§6.5), the argmin rule still produces the correct
answer; the threshold rule does not.

---

## 6. Derived Thresholds (Diagnostic View)

The argmin rule implies two thresholds on `p`, given fixed costs and amount.

### 6.1 Review vs. Approve

Review becomes cheaper than approve when:

```text
review_cost + p * residual_fraud_loss  <  p * fraud_loss
```

Solving for `p`:

```text
p > review_cost / (fraud_loss - residual_fraud_loss)
```

Call this `p_review`.

### 6.2 Block vs. Review

Block becomes cheaper than review when:

```text
(1 - p) * false_positive_cost  <  review_cost + p * residual_fraud_loss
```

Solving for `p`:

```text
p > (false_positive_cost - review_cost) / (false_positive_cost + residual_fraud_loss)
```

Call this `p_block`.

### 6.3 Threshold View (Diagnostic Only)

```text
if p < p_review:                 approve
elif p < p_block:                review
else:                            block
```

These thresholds are **derived**, not tuned. If costs change, thresholds
change automatically. If the thresholds degenerate, §6.5 applies.

### 6.4 Example Values (Constant-Loss Matrix)

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

Threshold view:

```text
p < 0.0286              -> approve
0.0286 <= p < 0.20      -> review
p >= 0.20               -> block
```

These are the constant-loss defaults. They hold when `amount_scaled: false`.
When amount scaling is enabled, the review threshold becomes
amount-dependent (§7) and this fixed-threshold view is a diagnostic only.

**Observed in the current build:** under constant loss, the policy produced
`p_review = 0.0286` and `p_block = 0.2000` on the test window, matching the
derivation exactly.

### 6.5 Threshold Edge Cases

The threshold view in §6.3 is a convenience, not the definition. The
**argmin rule in §5.4 is always well-defined**, even when the thresholds
degenerate.

**Case A — `fraud_loss <= residual_fraud_loss`.**  
The denominator of `p_review` is zero or negative. Review is never cheaper
than approve for any `p >= 0`. The review band is empty, and the policy
reduces to an approve-vs-block decision:

```text
approve if  p * fraud_loss < (1 - p) * false_positive_cost
block otherwise
```

This signals a cost matrix where review is as bad as or worse than doing
nothing. The config should be rejected before modeling, not silently
accepted.

**Case B — `p_review >= p_block`.**  
The review band is empty. For `p` in `[p_block, p_review)` the threshold
rule would say `approve`, but block is actually cheaper. The argmin rule
handles this correctly; the threshold rule does not. Implement the argmin
rule.

**Case C — thresholds outside `[0, 1]`.**  
If `p_review < 0` or `p_block > 1`, the corresponding band vanishes. The
argmin rule still applies. Do not clip thresholds. Report any regime where
this occurs.

**Rule:** implement §5.4 as the source of truth. Use §6.3 only as a
diagnostic view for the report.

**Coverage:** all three cases are covered by unit tests in
`tests/test_policy.py` (`test_edge_case_a_*`, `test_edge_case_b_*`,
`test_edge_case_c_*`). The tests assert that the argmin produces the minimum
of the three expected costs at every `p`, not that the threshold rule
produces a particular answer. This is the correct behavior when the
thresholds degenerate.

---

## 7. Amount-Scaled Fraud Loss

The constant-loss policy treats `fraud_loss` as fixed. This is a
simplification: a $10,000 fraudulent transfer costs more than a $10 one.

The policy therefore supports amount-scaled fraud loss:

```text
fraud_loss(amount) = amount * fraud_loss_rate
```

When amount scaling is enabled, the review-vs-approve threshold becomes
amount-dependent:

```text
p_review(amount) = review_cost / (amount * fraud_loss_rate - residual_fraud_loss)
```

The block-vs-review threshold is unchanged because it does not depend on
`fraud_loss`.

The edge cases in §6.5 apply, plus one additional case: if
`amount * fraud_loss_rate <= residual_fraud_loss`, review is never cheaper
than approve for that transaction.

### 7.1 Rate Calibration

`fraud_loss_rate` is derived from **training-window** amounts only:

```text
fraud_loss_rate = 1 / mean(amount_proxy on train)
                = 1 / 521.1626
                = 0.0019187869
```

This choice keeps `mean(fraud_loss_rate * amount_proxy) = 1.0` on the
training window, matching the constant-loss comparison scale without using
any test-window information. No test-window leakage is possible.

### 7.2 Observed Effect (Evidence)

Amount scaling was evaluated under the stop criterion defined in the
evaluation protocol. Setup:

- `amount_scaled: true`
- `fraud_loss_rate = 0.0019187869`
- Same classifier, same split, same test window
- Only the cost assumption changed

| Config | Policy cost/txn | Strongest baseline | Advantage |
|---|---:|---:|---:|
| Constant `fraud_loss = 1.0` | 0.008901 | 0.012088 | 26.4% |
| Amount-scaled (train-calibrated) | **0.007566** | 0.017543 | **56.9%** |

- Decision flips: 5,542 / 227,491 = **2.44%**
- Relative cost/txn change: **−15.0%**

**Verdict: success stop.** Amount scaling is adopted as the default. Both
stop thresholds were exceeded.

**Mechanism:** with per-row `fraud_loss`, the approve expected cost
`p * amount * rate` grows for large transactions, so the argmin routes them
to review. Under constant loss those same transactions were approved. The
policy is exploiting signal the constant-loss version was leaving on the
table.

### 7.3 Out-of-Scope Cost Realism

`false_positive_cost` is also plausibly proportional to `amount` (lost
revenue, customer value). The current build does not model this. It is named
here so it is not a hidden assumption, and it is a candidate for future
work.

---

## 8. Capacity Override (Deferred)

Real systems have finite review capacity. If the review queue is full, the
policy must adapt.

### 8.1 Specification (Not Implemented)

If the number of transactions in the review band exceeds `capacity` per time
window:

```text
keep the top-K by expected savings (p * fraud_loss(amount) - review_cost)
route the rest by the approve-vs-block decision only
```

### 8.2 Why It Matters

- Prevents review queue overflow
- Makes the capacity tradeoff explicit
- Exposes how much value is lost when capacity is constrained

### 8.3 Status

Capacity simulation is **out of scope** for the current build. There is no
`configs/policy.yaml` and no `capacity_enabled` flag in the current code.
This section is preserved as a specification for future work.

Budget-constrained **ranking** metrics (top 1% / 5% / 10%) are reported in
the backtest per `docs/evaluation_protocol.md` §11.2. Those are ranking
metrics, not capacity-aware decisioning. They do not modify the policy's
actions; they report on the top slice of the scored test window as it
stands.

---

## 9. Calibration Requirement

The policy assumes `p` is a real probability.

If `p` is uncalibrated:

- Expected costs are wrong.
- Thresholds derived from costs are wrong.
- Cost-based decisions are wrong.

### 9.1 Gate

The evaluation protocol (`docs/evaluation_protocol.md` §7) defines the gate:
**ECE < 0.05 on the validation window**, or a documented calibration step
must bring it below. A classifier that fails the gate is not admissible as a
policy input.

### 9.2 Observed Result

Calibration was measured on the validation window using the diagnostic in
`src/evaluation/calibration.py`.

| Metric | Value |
|---|---:|
| ECE (10 quantile bins) | **0.0040** |
| Brier (model) | 0.010050 |
| Brier (trivial, predict val mean) | 0.010103 |

**Verdict: gate passed.** ECE of 0.0040 is well below 0.05. No calibration
step (Platt, isotonic, or otherwise) was applied. Raw LightGBM output is
used by the policy directly.

**Reliability note:** the reliability table shows the model is well
calibrated across bins 0–8 (where ~90% of transactions live). It is mildly
overconfident in the top decile (bin 9: mean predicted 9.5%, actual 7.0%),
but those scores fall inside the review band and do not affect block
decisions. This is documented, not corrected — correcting it would be a
change without a measured failure justifying it.

### 9.3 Cadence

Recalibrate whenever the classifier is retrained, or when ECE drifts beyond
the gate. The ECE diagnostic is not part of the automated pipeline; it is
run manually after retraining and its result is recorded in the report.

---

## 10. Action Logging

Every decision must be logged for audit and backtest.

### 10.1 Full Schema (Specification)

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | string | Join key |
| `decision_time` | timestamp | When decision was made |
| `amount` | float | Transaction value |
| `p_fraud` | float | Classifier output |
| `action` | enum | approve / review / block |
| `expected_cost_approve` | float | For audit |
| `expected_cost_review` | float | For audit |
| `expected_cost_block` | float | For audit |
| `chosen_expected_cost` | float | Min of the three |
| `reason` | string | e.g. `"argmin_expected_cost"` |
| `cost_config_hash` | string | Hash of the cost matrix used |

### 10.2 Current Schema (As Implemented)

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | int | Join key |
| `month` | int | For grouping |
| `p_fraud` | float | Classifier output |
| `action` | string | approve / review / block |
| `expected_cost_approve` | float | For audit |
| `expected_cost_review` | float | For audit |
| `expected_cost_block` | float | For audit |
| `chosen_expected_cost` | float | Min of the three |
| `reason` | string | Fixed string `"argmin_expected_cost"` |

**Current omissions and why:**

- `decision_time` — BAF has only month-level granularity; a per-row
  timestamp would be fabricated.
- `amount` — `amount_proxy` lives in `scored_test.parquet` and is joined in
  the backtest, not duplicated into the log.
- `cost_config_hash` — the current build runs one frozen cost matrix; there
  is nothing to disambiguate. Add it when a second cost matrix is
  introduced.

### 10.3 Why Log All Three Expected Costs

- **Debugging:** shows why the action was chosen.
- **Sensitivity:** allows re-scoring under different cost matrices without
  re-running the classifier.
- **Audit:** allows checking whether one action dominates for a subgroup.

In the current build, the three expected costs are what makes the
amount-scaled sensitivity possible without re-running the classifier. This
is exactly the use case anticipated here.

### 10.4 Labels Are Not in the Action Log

`y_true` and `label_time` are **not** columns of the action log. They are
joined in the backtest, only for transactions whose labels have matured by
the evaluation end. This preserves the audit trail as a pure decision
record.

### 10.5 Storage

- Current: `data/processed/action_log.parquet`
- No database.

---

## 11. Failure Modes

The policy is simple, but it can still fail. Named here before results are
claimed.

| Failure mode | Cause | Symptom | Status |
|---|---|---|---|
| Uncalibrated `p` | Classifier outputs uncalibrated scores | Costs and thresholds wrong | Measured; ECE = 0.0040, gate passed |
| Wrong cost matrix | Costs do not reflect reality | Policy picks wrong action | All four parameters tested; sensitivity sweep complete |
| Constant fraud loss | Amount ignored | Large transactions under-protected | Addressed — amount scaling adopted |
| Degenerate thresholds | `fraud_loss <= residual_fraud_loss`, or `p_review >= p_block`, or thresholds outside [0,1] | Review band empty or misleading | Covered by unit tests; not triggered by current cost matrix |
| Capacity ignored | Review queue overflows | Latency and backlog | Out of current scope; documented as future work |
| Threshold tuning on test | Retro-fitting to results | Leakage, invalid comparison | Forbidden by the evaluation protocol; not done |
| Feedback loop | Policy changes labels | Observed labels biased | Out of current scope; BAF is a static dataset |
| Segment disparity | Costs differ by segment | Policy unfair or ineffective | Out of current scope |
| Adversarial adaptation | Fraudsters learn thresholds | Distribution drift | Out of current scope |

Each unresolved item is a candidate for future work. None is claimed as
solved.

---

## 12. What This Policy Is Not

- It is not a learned policy (no bandits, no RL).
- It is not a ranking policy (top-N by score is a separate ranking problem).
- It is not a capacity-aware scheduler (§8 is deferred).
- It is not a causal policy (no counterfactual treatment effect).
- It is not a fairness-aware policy (no group constraints).
- It is not a threshold-tuning exercise (thresholds are derived from costs).

Those are extensions, not requirements.

---

## 13. Relationship to the Evaluation Protocol

The decision policy defines:

- Which actions exist
- How an action is chosen
- What expected costs are
- Which cost keys are canonical

The evaluation protocol defines:

- How realized cost is computed
- Which baselines are compared
- Which metrics are reported
- How statistical claims are made

The two documents must agree on:

- Action set: `approve` / `review` / `block`
- Decision rule: argmin of expected cost
- Canonical config keys: `fraud_loss`, `false_positive_cost`, `review_cost`,
  `residual_fraud_loss`, `amount_scaled`, `fraud_loss_rate`

**Canonical key:** the residual loss after review is `residual_fraud_loss`
in `configs/costs.yaml`.

**Verification:** both documents describe the same action set, the same
decision rule, and the same cost matrix keys. Amount scaling was added to
both `configs/costs.yaml` and the policy code; the evaluation protocol's
sensitivity requirement is satisfied by the same change. No disagreement
remains.

If the two documents disagree in future, the evaluation protocol wins and
this document is updated.

---

## 14. Configuration

### 14.1 `configs/costs.yaml` — As Implemented

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
amount_scaled: true
fraud_loss_rate: 0.0019187869
```

The first four keys are the constant-loss cost matrix. `amount_scaled` and
`fraud_loss_rate` were added after the constant-loss build was validated and
the amount-scaled sensitivity returned a success stop. See §7.

### 14.2 `configs/policy.yaml` — Not Implemented

The full architecture envisions a `configs/policy.yaml` for threshold
overrides and capacity settings. The current build does not implement it.
There is no `use_derived_thresholds`, `p_review`, `p_block`,
`capacity_enabled`, or `review_capacity_per_day` in the code.

Thresholds are **always derived** from the cost matrix — there is no
override mechanism. Capacity is deferred. This section is preserved as a
specification for future work. Do not create `configs/policy.yaml` until
there is a measured failure that requires it.

---

## 15. Definition of Done

### 15.1 Policy (Implemented)

- [x] Actions defined: approve / review / block
- [x] Expected cost formulas implemented in `src/policy/decide.py`
- [x] Argmin rule implemented as the source of truth (`choose_actions`)
- [x] Derived thresholds computed from costs and reported as a diagnostic
      view only
- [x] Threshold edge cases (§6.5) handled and covered by unit tests
- [x] Cost matrix in `configs/costs.yaml` with canonical keys
- [x] Action log written to `data/processed/action_log.parquet`
- [x] Calibration gate passed: ECE = 0.0040 on validation
- [x] Policy compared against the canonical baseline set (random,
      approve-all, block-all, LR/RF/LGBM + static 0.5)
- [x] Amount-scaled fraud loss evaluated and adopted (success stop, §7.2)
- [x] Full 2× sensitivity sweep across all four cost parameters run
- [x] Bootstrap confidence intervals computed on the test window
- [x] Failure modes documented (§11) and cross-referenced in the report

### 15.2 Deferred (Documented, Not Omitted)

- [ ] Policy config in `configs/policy.yaml` — deferred until a measured
      failure requires it
- [ ] Full action log schema including `cost_config_hash` — deferred until
      multiple cost matrices exist
- [ ] Policy evaluated under additional delay regimes (2-month, 3-month) —
      out of scope for this submission
- [ ] Capacity-aware decisioning — deferred
- [ ] Amount-scaled `false_positive_cost` — named in §7.3, deferred

**Result:** every applicable box checked. Deferred items are documented as
deferred, not omitted.

---

## 16. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | v0.4 — reframed as supplementary analysis | Align with course submission structure |
| 2026-09-24 | v1.0 — first-principles revision; policy promoted to object of study; "supplementary" label removed; two-layer references removed; calibration gate aligned with `evaluation_protocol.md` v1.0; amount scaling presented as evidence not supplementary result; DoD consolidated into Policy (Implemented) and Deferred; guiding rule rewritten | Derive from `problem_framing.md` v1.0, per the professor's confirmed autonomy |

---

## 17. Guiding Rule

> The policy is the product. The classifier is an input. The cost matrix is
> the assumption. The backtest is the evidence.

> A classifier is better if and only if the policy it feeds produces lower
> realized cost per transaction under the same split, the same cost matrix,
> and the same delay regime. Classification metrics are supporting evidence,
> not the criterion.

> Thresholds are derived, never tuned. The argmin rule is the source of
> truth; the threshold view is a diagnostic.