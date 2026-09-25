# Documentation Index

This folder contains every project document. Start with the reading order
that matches who you are, then dip into the reference docs as needed.

---

## Reading Order — Reviewer / Instructor

The four docs that define what the project claims and how it is measured.
Read in this order.

1. [`problem_framing.md`](problem_framing.md) — what problem this solves and why it exists
2. [`evaluation_protocol.md`](evaluation_protocol.md) §1–4 — what claims are allowed
3. [`../reports/decision_backtest.md`](../reports/decision_backtest.md) — the result
4. [`decision_policy.md`](decision_policy.md) §5–6 — how a score becomes an action

Everything else is depth. Stop after those four if you only have 30 minutes.

---

## Reading Order — Paper Team

Four files in [`paper/`](paper/). Open them in this order.

1. [`paper/paper_blueprint.md`](paper/paper_blueprint.md) — IEEE section map
2. [`paper/reference_sheet.md`](paper/reference_sheet.md) — every number and claim, one page
3. [`paper/introduction_draft.md`](paper/introduction_draft.md) — Section 1 skeleton
4. [`paper/abstract_and_index_terms.md`](paper/abstract_and_index_terms.md) — copy-paste ready

**Rule:** if a sentence in the paper states a number, it must appear in
`reference_sheet.md` §1. If it states a claim, it must appear in §2 or §3.

---

## Reading Order — New Contributor

Understand the built system before the plan.

1. [`mvp_architecture.md`](mvp_architecture.md) — the as-built pipeline (source of truth)
2. [`data_card.md`](data_card.md) §2–5 — dataset, delay simulation, splits
3. [`decision_policy.md`](decision_policy.md) — the policy in full
4. [`evaluation_protocol.md`](evaluation_protocol.md) §7–9 — the backtest
5. [`evaluation_protocol.md`](evaluation_protocol.md) §17 — stop criteria
   and verdicts

---

## All Documents

### Foundation (source of truth)

| Document | Purpose |
|---|---|
| [`problem_framing.md`](problem_framing.md) | First-principles problem decomposition, scope, success criteria |
| [`first_principles_decomposition.md`](first_principles_decomposition.md) | Derivation behind the decision-centric framing; assumptions audit; traceability matrix |
| [`data_card.md`](data_card.md) | Dataset, schema, delay simulation, splits, leakage and bias registers |
| [`decision_policy.md`](decision_policy.md) | Actions, expected cost, threshold derivation, action log schema |
| [`evaluation_protocol.md`](evaluation_protocol.md) | Cost matrix, temporal backtest, baselines, forbidden metrics, stop criteria |

### Build and implementation

| Document | Purpose |
|---|---|
| [`mvp_architecture.md`](mvp_architecture.md) | The as-built single decision pipeline — **read this for what exists** |

### Superseded (kept for context)

| Document | Reason |
|---|---|
| [`architecture.md`](architecture.md) | Week 1 MVP specification; superseded by `mvp_architecture.md` and the v1.0 foundation documents |
| [`mvp_2_weeks.md`](mvp_2_weeks.md) | Original 2-week plan; superseded by `mvp_architecture.md` |

### Process and plan

| Document | Purpose |
|---|---|
| [`roadmap.md`](roadmap.md) | Gated execution plan for the unified decision pipeline |
| [`daily_log/`](daily_log/) | Session-by-session build record |

### Paper materials

| Document | Purpose |
|---|---|
| [`paper/paper_blueprint.md`](paper/paper_blueprint.md) | IEEE section map and length budget |
| [`paper/abstract_and_index_terms.md`](paper/abstract_and_index_terms.md) | Abstract (~200 words) and index terms |
| [`paper/introduction_draft.md`](paper/introduction_draft.md) | Section 1 prose with placeholder markers |
| [`paper/reference_sheet.md`](paper/reference_sheet.md) | Every number, claim, and forbidden claim |

---

## Reports (in `/reports`)

| Report | Contents |
|---|---|
| [`decision_backtest.md`](../reports/decision_backtest.md) | Primary deliverable: policy vs. baseline comparison, data integrity, failure analysis, stop verdict |
| [`model_comparison.md`](../reports/model_comparison.md) | Supporting: classifier comparison as policy inputs, selection justification, final test results |
| [`sensitivity.md`](../reports/sensitivity.md) | Full cost sensitivity table across the 2× sweep |
| [`bootstrap.md`](../reports/bootstrap.md) | 95% confidence intervals on cost per transaction |

---

## Document Status Key

- **Source of truth** — describes what currently exists; if it disagrees with code, the code is wrong.
- **Specification** — describes what should exist post-MVP; not yet built.
- **Superseded** — kept for context; a newer document replaces it.
- **Historical** — session log; preserves the state at a moment in time.

If two documents disagree and neither is marked superseded, the evaluation
protocol wins and the other document is updated. See
[`decision_policy.md`](decision_policy.md) §13.

---

## Repository Root

- [`../README.md`](../README.md) — project overview and reproduce commands
- [`../TODO.md`](../TODO.md) — open work items for the current phase
- [`../reports/`](../reports/) — evaluation outputs
- [`../src/`](../src/) — pipeline source
- [`../tests/`](../tests/) — unit tests for the policy and cost matrix
