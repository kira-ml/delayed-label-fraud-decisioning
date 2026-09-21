# Documentation Index

This folder contains every project document. Start with the reading order
that matches who you are, then dip into the reference docs as needed.

---

## Reading Order — Reviewer / Instructor

The four docs that define what the project claims and how it is measured.
Read in this order.

1. [`problem_framing.md`](problem_framing.md) — what problem this solves and why it exists
2. [`evaluation_protocol.md`](evaluation_protocol.md) §1–4 — what claims are allowed
3. [`../reports/mvp_backtest.md`](../reports/mvp_backtest.md) — the result
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
5. [`architecture.md`](architecture.md) §9 — data-driven stop criteria

---

## All Documents

### Foundation (source of truth)

| Document | Purpose |
|---|---|
| [`problem_framing.md`](problem_framing.md) | First-principles problem decomposition, scope, success criteria |
| [`data_card.md`](data_card.md) | Dataset, schema, delay simulation, splits, leakage and bias registers |
| [`decision_policy.md`](decision_policy.md) | Actions, expected cost, threshold derivation, action log schema |
| [`evaluation_protocol.md`](evaluation_protocol.md) | Cost matrix, temporal backtest, baselines, forbidden metrics |

### Build and implementation

| Document | Purpose |
|---|---|
| [`mvp_architecture.md`](mvp_architecture.md) | The as-built 2-week pipeline — **read this for what exists** |
| [`architecture.md`](architecture.md) | Full post-MVP architecture spec, with data-driven stop criteria (§9) |
| [`mvp_2_weeks.md`](mvp_2_weeks.md) | Original 2-week plan (superseded by `mvp_architecture.md`) |

### Process and plan

| Document | Purpose |
|---|---|
| [`roadmap.md`](roadmap.md) | Gated weekly plan; Week 2+ requires a measured failure |
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
| [`mvp_backtest.md`](../reports/mvp_backtest.md) | Primary deliverable: baseline comparison, sensitivity, bootstrap, stopping decisions |
| [`sensitivity.md`](../reports/sensitivity.md) | Full cost sensitivity table |
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
- [`../reports/`](../reports/) — evaluation outputs
- [`../src/`](../src/) — pipeline source
- [`../tests/`](../tests/) — unit tests for the policy and cost matrix
