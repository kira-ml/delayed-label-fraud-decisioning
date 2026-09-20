# Data Card

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** Data Card  
> **Status:** v0.2 — aligned with Week 1 MVP  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

This document describes every dataset used in the project, its schema, how label delay is simulated, how temporal splits are constructed, and which biases and leakage risks exist.

It exists so that:

- The delay simulation assumptions are **explicit and falsifiable**
- Temporal splits are **documented before modeling**
- Leakage risks are **named, not discovered later**
- Any reviewer can reproduce the exact data setup
- Results can be interpreted with the correct caveats

**Rule:** No model result is valid unless the data used to produce it is documented here.

---

## 2. Datasets

### 2.1 Primary Dataset — Bank Account Fraud (BAF) Suite

| Field | Value |
|---|---|
| Name | Bank Account Fraud (BAF) Suite |
| Version | v1 (NeurIPS 2022) |
| Source | https://arxiv.org/abs/2211.13358 |
| License | CC BY 4.0 (verify before redistribution) |
| Format | CSV / Parquet |
| Rows | ~1M per variant |
| Features | 31 (mixed numeric + categorical) |
| Fraud rate | ~1.1% (variant-dependent) |
| Time span | Synthetic, month-based |
| Time granularity | **TBD — verify before modeling** (see Section 4.6) |
| Storage | `data/raw/baf/` |

**Why chosen:**

- Public, citable, and designed for fraud research
- Realistic feature set (tabular, mixed types)
- Suitable for temporal and delay experiments
- Manageable size for a student project
- Includes temporal ordering suitable for backtest

**Known limitations:**

- Synthetic, not real bank data
- Fraud rate may not match production distributions
- No real chargeback timestamps — delay must be simulated
- Timestamp granularity is unverified (see Section 4.6)

### 2.2 Secondary Dataset — IEEE-CIS Fraud Detection (optional)

| Field | Value |
|---|---|
| Name | IEEE-CIS Fraud Detection |
| Source | Kaggle |
| License | Competition rules — verify before redistribution |
| Format | CSV |
| Rows | ~590K train transactions |
| Features | ~400 (transaction + identity) |
| Fraud rate | ~3.5% |
| Time span | 2017-11-30 to 2017-12-31 |
| Storage | `data/raw/ieee_cis/` |

**Why optional:**

- Rich features, useful for feature engineering later
- No identity graph in Week 1
- Short time span limits rolling evaluation
- License restricts redistribution

**Week 1 rule:** Use BAF only. Add IEEE-CIS only if BAF is insufficient.

---

## 3. Schema (Post-Load)

After `src/data/load.py`, every transaction has this canonical schema.

| Column | Type | Available at decision time? | Notes |
|---|---|---|---|
| `transaction_id` | string | Yes | Unique per transaction |
| `decision_time` | timestamp | Yes | When decision must be made |
| `amount` | float | Yes | Transaction value |
| `customer_id` | string | Yes | Account identifier |
| `merchant_id` | string | Yes | Merchant identifier |
| `device_id` | string | Yes | Device fingerprint |
| `payment_method` | categorical | Yes | Card, ACH, etc. |
| `feature_*` | mixed | Yes | Model inputs |
| `y_true` | int | No | Ground truth fraud label |
| `label_time` | timestamp | No | When label becomes observable |

**Critical rules:**

- `y_true` and `label_time` are **never** features
- No column with a name like `chargeback_*`, `dispute_*`, `case_*` is used as a feature
- All features must be obtainable at or before `decision_time`
- Timestamps are stored in UTC

If BAF does not expose `customer_id`, `merchant_id`, or `device_id` directly, they must be omitted from the canonical schema and this document updated before modeling.

---

## 4. Label Delay Simulation

Public fraud datasets do not provide realistic chargeback timestamps. Delay must be simulated.

### 4.1 Simulation Rule

For each transaction:

```text
decision_time = t
label_time    = t + Δ
```

Week 1 rule: **Δ is fixed per regime**, not sampled per transaction. This keeps the Week 1 evaluation reproducible and simple.

Sampled delay distributions are explicitly **out of scope for Week 1** and may be added in Week 2+ if a measured Week 1 result justifies them.

### 4.2 Delay Regimes

Every experiment is run under three regimes.

| Regime | Δ (fraud) | Δ (non-fraud) | Purpose |
|---|---|---|---|
| Short | 7 days | 7 days | Fast chargeback |
| Medium | 30 days | 30 days | Typical dispute window |
| Long | 90 days | 90 days | Worst-case delayed feedback |

Week 1 rule:

- Fraud and non-fraud use the **same fixed Δ within a regime**
- Each regime is evaluated **separately**
- Results are **never averaged across regimes**

If the BAF timestamp granularity does not support day-level offsets, the regimes are redefined as month-based (1 / 2 / 3 months) and this section is updated. The fallback must be documented before modeling.

### 4.3 Delay Distribution

Week 1: fixed delay per regime (Section 4.2).

Week 2+ optional extension (not required):

```text
Δ_fraud     ~ LogNormal(mu, sigma)  truncated to [1, 120] days
Δ_nonfraud  = observation_window     (fixed, e.g., 90 days)
```

Any change to the delay distribution must be documented here and must not be tuned to improve results.

### 4.4 Censoring Rule

A label is **observed** only if:

```text
label_time <= evaluation_end
```

Labels whose `label_time` falls after the cutoff are treated as **censored**, not as negative.

Week 1 treatment of censored labels:

- Excluded from training
- Excluded from evaluation
- **Count reported per split and per delay regime**

Censored labels are never treated as `y = 0`.

### 4.5 Assumptions

- Fraud labels and non-fraud labels share the same fixed delay in Week 1
- Non-fraud labels are assumed fully observed after `label_time`
- Fraud labels are assumed correct once observed
- Delay is independent of features
- Delay is independent of model decisions

**These assumptions are known to be unrealistic.** They are documented so the sensitivity of results to each can be tested later. None are resolved in Week 1.

### 4.6 BAF Timestamp Granularity Verification (Blocking)

Before any delay simulation is run, verify:

- Does BAF expose a usable day-level timestamp, or only a month index?
- Is there a per-row `decision_time` field, or must it be synthesized?
- If synthesized, what is the rule, and does it preserve ordering within a month?

**Rule:** Delay regimes may not be finalized until this verification is done.  
**Fallback:** If only month-level ordering exists, redefine regimes as 1 / 2 / 3 months and update Section 4.2 before modeling.

This is a **blocking pre-modeling task** and appears in the Definition of Done (Section 12).

---

## 5. Temporal Splits

### 5.1 Chronological Split

| Split | Rule | Purpose |
|---|---|---|
| Train | `decision_time < T_train` **and** `label_time <= T_train` | Fit model |
| Validation | `T_train <= decision_time < T_val` **and** `label_time <= T_val` | Early stopping, calibration |
| Test | `decision_time >= T_val` **and** `label_time <= test_end` | Final evaluation |

### 5.2 Label Maturation Rule

The same rule applies to every split:

```text
A transaction belongs to a split only if:
  its decision_time falls inside the split window, AND
  its label_time is at or before the split's cutoff.
```

Consequences:

- Transactions whose labels have not matured by a split cutoff are **censored for that split**
- Censored transactions are excluded from training and evaluation for that split
- Censored counts are reported per split and per delay regime

### 5.3 Rules

- Splits are **chronological only**
- No shuffling
- No random train/test split
- No cross-validation across time boundaries
- No oversampling or SMOTE before splitting
- Any resampling must respect time order

### 5.4 Cutoff Values

| Split | T_train | T_val | test_end |
|---|---|---|---|
| Week 1 | TBD after EDA | TBD after EDA | TBD after EDA |

Cutoffs are set once, saved to `configs/splits.yaml`, and never changed without a documented reason.

---

## 6. Leakage Risks

Explicitly named to prevent accidental misuse.

| Risk | Description | Mitigation |
|---|---|---|
| Future features | Any feature computed using data after `decision_time` | Feature builder uses only past data |
| Post-decision fields | Columns that only exist after a decision (dispute reason, case notes) | Excluded from features |
| Target leakage | Columns highly correlated with `y_true` | Audited in EDA, removed if suspicious |
| Label leakage via delay | Using a label before `label_time` | Enforced by split rules |
| Split leakage | Train/test overlap in time | Chronological split enforced |
| Duplicate leakage | Same transaction appearing in train and test | Deduplicated by `transaction_id` |
| ID leakage | Model memorizes `customer_id` or `merchant_id` | IDs excluded or hashed |

### 6.1 Feature Audit Checklist

Before any model is trained:

- [ ] Every feature has a documented source time
- [ ] No feature uses `y_true`
- [ ] No feature uses `label_time`
- [ ] No feature uses post-decision data
- [ ] No feature is a proxy for `y_true`
- [ ] IDs are excluded or treated as categorical with care

---

## 7. Known Biases

| Bias | Description | Impact on Project |
|---|---|---|
| Censored labels | Some fraud never reported | Underestimates fraud rate |
| Unreported fraud | Customer does not dispute | Label noise |
| Investigation bias | Investigators focus on certain segments | Labels biased by past policy |
| Selection bias | Only some transactions reach review | Training distribution differs from population |
| Feedback loop | Model decisions change future labels | Observed labels depend on past policy |
| Synthetic data bias | BAF is synthetic | Patterns may not match real fraud |
| Class imbalance | Fraud is ~1% | Metrics must be imbalance-aware |
| Temporal shift | Fraud patterns change over time | Static splits may overestimate performance |

**None of these are solved in Week 1.** They are named so results can be interpreted honestly.

---

## 8. Feature Groups

| Group | Examples | Available at decision time | Week 1 use |
|---|---|---|---|
| Transaction | amount, payment method, channel | Yes | Yes |
| Customer | account age, prior fraud count | Yes (as of `t`) | Yes |
| Merchant | merchant category, prior disputes | Yes (as of `t`) | Yes |
| Device | device fingerprint, OS | Yes | Yes |
| Behavioral | velocity, time since last txn | Yes (as of `t`) | Yes |
| Identity | customer_id, device_id | Yes | Careful (ID leakage) |
| Outcome | y_true, label_time | No | Never as features |
| Post-decision | dispute reason, case notes | No | Never as features |

### 8.1 Amount Usage

`amount` is a decision-time feature **and** a cost input.

- As a feature: allowed, and used by the baseline model
- As a cost input: Week 1 uses a **constant** `fraud_loss`; amount-scaled `fraud_loss(amount) = amount * fraud_loss_rate` is a **required sensitivity analysis**, not the Week 1 default
- This split is documented so Week 1 stays simple while still testing the realism of the cost assumption

---

## 9. Preprocessing Rules

- Missing values: documented per column, never silently imputed before splitting
- Categorical encoding: fit on train only, applied to val/test
- Normalization: fit on train only, applied to val/test
- No target encoding across time boundaries
- No scaling using statistics from val/test
- All preprocessing steps saved to `artifacts/preprocessing.pkl` for reproducibility

---

## 10. Storage and Versioning

| Layer | Path | Committed? |
|---|---|---|
| Raw | `data/raw/` | No (gitignored) |
| Interim | `data/interim/` | No (gitignored) |
| Processed | `data/processed/` | No (gitignored) |
| Configs | `configs/` | Yes |
| Split definitions | `configs/splits.yaml` | Yes |
| Delay definitions | `configs/delay.yaml` | Yes |
| Cost definitions | `configs/costs.yaml` | Yes |

Raw and processed data are never committed to GitHub. Only code, configs, and documentation are tracked.

---

## 11. Reproducibility

Every data artifact must be reproducible from:

```text
raw dataset + configs + random seed
```

Requirements:

- Fixed random seed for delay simulation
- Fixed random seed for any sampling
- Fixed split cutoffs
- Documented library versions
- One command to rebuild all data artifacts

```bash
python -m src.data.build --config configs/week1.yaml
```

---

## 12. Week 1 Data Definition of Done

- [ ] BAF dataset downloaded to `data/raw/baf/`
- [ ] BAF timestamp granularity verified and documented (Section 4.6)
- [ ] Delay regimes finalized as day-based or month-based
- [ ] `src/data/load.py` produces `data/interim/transactions.parquet`
- [ ] Schema matches Section 3
- [ ] `src/data/simulate_delay.py` produces labels for all three regimes
- [ ] `src/data/split.py` produces chronological train/val/test
- [ ] Cutoffs saved to `configs/splits.yaml`
- [ ] Delay config saved to `configs/delay.yaml`
- [ ] Cost config saved to `configs/costs.yaml`
- [ ] Leakage audit checklist completed
- [ ] Censored label counts reported per split and per delay regime
- [ ] Data build reproducible with one command

---

## 13. Changelog

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | Initial data card | Project start |
| YYYY-MM-DD | Fixed delay per regime; added granularity check; added per-regime censored reporting | Align with Week 1 MVP and problem framing v0.2 |

---

## 14. References

- Bank Account Fraud (BAF) Suite — Jesus et al., NeurIPS 2022
- IEEE-CIS Fraud Detection — Kaggle
- Cost-sensitive learning — Elkan 2001
- Delayed feedback in fraud detection — industry literature
- PU learning — Elkan & Noto 2008

---

## 15. Guiding Rule

> If a delay assumption, a split cutoff, or a leakage risk is not documented here, it does not exist in this project.
