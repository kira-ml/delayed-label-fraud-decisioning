# Changelog

## [2.1.0] — 2026-11-02

### Added
- Fair baselines: cost-optimal single-threshold and two-threshold policies
  tuned on the validation window (`src/evaluation/baselines.py`).
- Baseline audit and ablation report (`reports/ablation.md`,
  `reports/ablation.json`) with a waterfall figure.
- Unit tests for the threshold baselines (`tests/test_baselines.py`).
- V2.1 communication kit (`docs/communication/one_pager_v2_1.html`,
  `carousel_v2_1.html`, `caption_v2_1.md`).

### Changed
- The headline now reports both comparisons: **57.91%** vs a 0.5 cut-off
  and **22.29%** vs the best cost-optimal threshold.
- README now leads with the fair comparison and includes the V2 falsification
  summary.
- The Streamlit results tab reads the fair baseline from
  `reports/ablation.json` and labels the 0.5 baseline as naive.
- `reports/decision_backtest.md` is deterministic (the dynamic timestamp was
  removed) and labels the six canonical baselines as such.

### Unchanged
- The model, cost matrix, chronological split, and policy.
- The six V2 verdicts: 3 survived, 1 fragile, 2 killed.
- The limitations: synthetic data, one regime, amount proxy.
