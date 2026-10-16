# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary (confirmed): a non-technical panel watching a live, thesis-defense-style
demo of the system (course: Introduction to Machine Learning, National University
Philippines, presentation on 2026-10-17). They need to understand, within a few
minutes, what the system takes in, what it decides, and why.

Secondary (the product's stated operator in the paper): a fraud-operations
analyst who must act on each transaction before its fraud label arrives.

## Product Purpose

A decision-support app for bank-account fraud. For each application/transaction it
estimates a fraud probability and routes it to one of three actions: approve,
review, or block, by choosing the action with the lowest expected cost. Success
in the demo: a viewer can say what the system did with a transaction and why,
without knowing machine-learning terms.

## Positioning

The decision rule, not the classifier, does the work. A cost-minimizing
approve/review/block policy reduced cost per transaction by 57.91% versus the
strongest static-threshold baseline, with a 95% bootstrap CI of [53.95%, 62.13%].
Bigger amounts carry bigger potential loss, so they get more caution at the same
fraud probability.

## Operating Context

- Shown live on a projector during a group presentation, then also deployed on
  Streamlit Community Cloud.
- Two flows: single-transaction manual entry and CSV batch upload
  (`sample_input.csv`, `sample_500.csv` in the repo root).
- Presenter drives; audience reads from a distance.

## Capabilities and Constraints

- Streamlit (Python) app at `app/streamlit_app.py`; loads `models/best_model.pkl`
  and `models/preprocessing.pkl`, the same artifacts reported in the paper.
- Cost matrix in `configs/costs.yaml`; the argmin of expected cost is the source
  of truth, and thresholds are derived diagnostics only.
- Dataset is the synthetic Bank Account Fraud (BAF) suite; amount is proxied by
  `proposed_credit_limit`.
- All numbers shown must match `docs/main.tex` and `reports/`.

## Brand Commitments

None beyond the project title and group/institution names.

## Evidence on Hand

- Results: `reports/decision_backtest.md`, `reports/sensitivity.md`,
  `reports/bootstrap.md`, `reports/model_comparison.md`.
- Paper: `docs/main.tex`.
- Must not claim: high accuracy, production-readiness, real bank data, multiple
  delay regimes, or measured latency.

## Product Principles

1. Plain language first; technical detail is available but never in the way.
2. Every decision shows its reason (risk level + amount + cost comparison).
3. Never overstate: numbers come from the paper, unchanged.
4. Readable from the back of a room.

## Accessibility & Inclusion

Projector viewing: high contrast, large type, and action meaning never carried by
color alone (always paired with a word).
