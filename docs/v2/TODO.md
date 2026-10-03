# TODO — 2026-10-03

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Scope:** V2 operational-reality testing — Phase A exit → Phase B builds → Phase D publication
> **Status:** Open
> **Priority order:** Phase A exit (blocking) → Phase B (bounded by H1, H4) → Phase D (publication)
> **Governing documents:** `docs/v2/problem_framing.md`, `docs/v2/falsification_plan.md`, `docs/v2/evaluation_framework.md`, `docs/v2/stop_criteria.md`

The V2 framework is frozen. Phase A tests are executed. All six hypotheses have verdicts. All remaining work is **report assembly, two earned Phase B builds, and publication packaging** — no new hypotheses, no new models, no new splits, no new cost matrices, no re-touching V1's frozen test window.

Every task in this TODO traces to a section of a V2 document. Any task that does not is a scope violation per `stop_criteria.md` §8.

---

## Why This TODO Exists

Phase A executed on 2026-10-03. Six hypotheses were tested against pre-registered kill criteria. The verdicts are recorded in `falsification_plan.md` §12 and the intermediate JSON files under `reports/v2/intermediate/`.

The blocker is that **the assembled report does not exist**. Per `stop_criteria.md` §4.1, `evaluation_framework.md` §11, and `falsification_plan.md` §8, Phase B code cannot be written until `reports/v2_falsification.md` exists.

This TODO sequences the work that unblocks Phase B, executes the two Phase B builds that H1 and H4 earned, and packages V2 for GitHub / LinkedIn / open-source publication — without expanding scope.

---

## Verified Numbers (anchor for all V2 edits)

| Fact | Value | Source of truth |
|---|---|---|
| V1 headline advantage | 57.91%, CI [53.95%, 62.13%] | V1 `reports/bootstrap.md` |
| H1 verdict | survived — 44.25% at K=4,550 | `h1_capacity.json` |
| H2 verdict | survived — 58.08%, CI [56.35%, 59.72%] | `h2_delay_2m.json` |
| H3 verdict | confirmed (fragile) — LR both steps; gap 4.25% / 4.17% | `h3_rolling_retrain.json` |
| H4 verdict | survived — max PSI 3.94 (`velocity_4w`, 0→1); 23/28 drift | `h4_drift.json` |
| H5 verdict | killed — max block-rate disparity 2.26pp < 5pp | `h5_fairness.json` |
| H6 verdict | killed — block stratum ECE 0.0600; bias ~2.1% | `h6_stratified_calibration.json` |
| Phase A exit item remaining | `reports/v2_falsification.md` | `stop_criteria.md` §4.1 |
| Phase B scope | exactly two builds: capacity-aware policy, drift detector | `stop_criteria.md` §4.2 |
| Phase C status | skipped | `stop_criteria.md` §4.3 |
| Phase B total time-box | 9 working weeks | `stop_criteria.md` §6 |
| Phase B per-build time-box | 3 working weeks | `stop_criteria.md` §6 |

**The four numbers V2 must preserve exactly: 44.25%, 58.08% / [56.35%, 59.72%], 3.94, 2.26pp.**

---

## Phase A Exit — Blocking Everything

These three files complete Phase A. Nothing in Phase B or Phase D starts until all three exist.

### A1. Write `reports/v2_falsification.md`

**Purpose:** The assembled per-hypothesis audit trail. This is the file every downstream artifact cites.

**Format:** `evaluation_framework.md` §7 — one section per hypothesis, in execution order from `falsification_plan.md` §4: H4 → H5 → H1 → H6 → H3 → H2.

**Source of truth:** the six JSON files under `reports/v2/intermediate/`. Every number in the report traces to one of them.

**Rules:**

- One section per hypothesis, using the exact template in `evaluation_framework.md` §7 (Setup / Metrics / Result / Verdict / Interpretation / Consequence / Amends V1?).
- Non-findings (H5, H6) reported at the same length as findings (`falsification_plan.md` §6).
- Verdicts are not re-decided — they are transcribed from `falsification_plan.md` §12.
- No number appears that is not in an intermediate JSON.
- H3 uses its binary verdict format (Confirmed / Amended), not the standard four-verdict format (`evaluation_framework.md` §8).

- [ ] Write H4 section (drift) — from `h4_drift.json` + `h4_importance_crossref.json`
- [ ] Write H5 section (fairness, killed) — from `h5_fairness.json`
- [ ] Write H1 section (capacity, survived) — from `h1_capacity.json`
- [ ] Write H6 section (stratified calibration, killed) — from `h6_stratified_calibration.json`
- [ ] Write H3 section (rolling retrain, confirmed/fragile) — from `h3_rolling_retrain.json`
- [ ] Write H2 section (2-month delay, survived) — from `h2_delay_2m.json`
- [ ] Write header section: purpose, method, execution order, verdict summary table
- [ ] Confirm every number traces to an intermediate JSON
- [ ] Confirm H5 and H6 sections match findings sections in length and rigor

### A2. Write `docs/v2/documentation_map.md`

**Purpose:** V1→V2 status table. Required by `problem_framing.md` §7 and `stop_criteria.md` §9.

**Content:**

- Every V1 doc and its V2 status: inherited / extended / superseded / amended.
- For each extended or amended V1 doc, which section and which V2 result caused the change.
- Reference the V1 amendment rules in `falsification_plan.md` §7.

- [ ] Build the V1 doc inventory (from `docs/README.md` "All Documents" table)
- [ ] Assign status per doc: inherited / extended / superseded / amended
- [ ] For H1-amended V1 docs: note the capacity envelope added to Limitations
- [ ] For H2-amended V1 docs: note the delay envelope added to Limitations
- [ ] For H3-amended V1 docs: note the fragility note added to Classifier Selection
- [ ] For H4-amended V1 docs: note the drift note added to Limitations
- [ ] For H5-amended V1 docs: note the non-finding note added to Limitations
- [ ] For H6-amended V1 docs: note the non-finding note added to Limitations
- [ ] Confirm no V1 doc was silently altered

### A3. Write `docs/v2/README.md`

**Purpose:** Reading order for the `docs/v2/` folder for external visitors.

**Content:**

- Reading order for a reviewer/instructor
- Reading order for a paper team / external reader
- Reading order for a GitHub visitor
- Status key (inherited / extended / superseded / amended) matching `documentation_map.md`
- Pointer to `reports/v2_falsification.md` and `reports/v2/intermediate/`

- [ ] Define reading order for reviewers
- [ ] Define reading order for external readers (GitHub visitors)
- [ ] Define reading order for the paper team
- [ ] Add status key matching A2
- [ ] Cross-link to A1 and the intermediate JSON directory

**Phase A exits when A1, A2, A3 exist.** Per `stop_criteria.md` §4.1 and `evaluation_framework.md` §11, no Phase B code is written before this point.

---

## Phase B — Depth on Survivors (bounded by H1 and H4)

Per `stop_criteria.md` §4.2, Phase B consists of **exactly two builds**. No others enter without the mid-flight scope gate (`stop_criteria.md` §8).

### B1. Capacity-aware policy (H1 survivor)

**Order:** protocol first, then code, then config. This is `falsification_plan.md` §3 H1's own "If survives" rule.

- [ ] Write `docs/v2/protocols/decision_policy_capacity.md`
  - Capacity semantics (per-window K)
  - Ranking rule: `min(c_approve, c_block) - c_review` (as amended 2026-10-03 in `falsification_plan.md` §11)
  - Overflow routing: approve-vs-block argmin
  - Tie-break by `transaction_id` ascending (per `evaluation_framework.md` §5.1)
  - Capacity levels: `{1%, 2%, 5%, 10%, 20%} × test volume`
- [ ] Implement `src/policy/decide_capacity.py`
  - Reuse `choose_actions` from `decide.py` for the unconstrained expected costs
  - Add capacity re-ranking and overflow routing only
  - No duplicate cost logic; no retraining; no test-window re-scoring
- [ ] Add `configs/policy.yaml` with `capacity_per_window`
- [ ] Add unit tests for `_apply_capacity` boundary cases (K > band, K = 0, empty band)
- [ ] Re-run H1's diagnostic using the new module; confirm identical verdict
- [ ] Extend `docs/decision_policy.md` §8 from "specification, deferred" to "implemented" (per `problem_framing.md` §7)
- [ ] Record Phase B result in `reports/v2_falsification.md` as an addendum section

### B2. Drift detector (H4 survivor)

**Order:** protocol first, then code. This is `falsification_plan.md` §3 H4's own "If survives" rule.

- [ ] Write `docs/v2/protocols/monitoring.md`
  - PSI-based drift detection spec
  - Alert thresholds: none `< 0.1`, moderate `[0.1, 0.25)`, significant `≥ 0.25`
  - Response policy: retrain / recalibrate / alert
  - Reference `evaluation_framework.md` §5.4 for binning rules
- [ ] Implement `src/monitoring/drift_detector.py`
  - Reuse the PSI logic from `src/v2/drift.py` (do not duplicate)
  - Parameterize reference window and comparison window
  - Emit a machine-readable drift report
- [ ] Add unit tests for PSI on synthetic distributions with known drift
- [ ] Add drift summary to V1's paper Limitations section (via `docs/v2/documentation_map.md`)
- [ ] Record Phase B result in `reports/v2_falsification.md` as an addendum section

**Phase B does not include:**

- H3 work — `confirmed` is a paper note, not a build (`falsification_plan.md` §12.3)
- H5 or H6 work — killed, dropped from scope (`findings.md` §7)
- Phase C — skipped per `stop_criteria.md` §4.3

**Phase B time-box:** 9 working weeks total, 3 per build. Overrun drops the build and records it as future work (`stop_criteria.md` §6).

---

## Phase D — Publication and Communication

Per `stop_criteria.md` §4.4, Phase D exit requires the following.

### D1. V1 paper receives one V2 subsection

- [ ] Write one subsection summarising the six verdicts and the V1 headline-status table (`findings.md` §4)
- [ ] Include the two strengthening notes (H1, H2), the fragility note (H3), the drift note (H4), and the two non-findings (H5, H6)
- [ ] Amend `docs/paper/reference_sheet.md` §1 with V2 numbers, V1 numbers preserved and labeled "V1 conditions"
- [ ] Confirm the subsection does not exceed the cap in `problem_framing.md` §6.2

### D2. Write `docs/v2/cut_list.md`

- [ ] Record what V2 does not do and why
- [ ] Include the H5 pre-registration limitation (`findings.md` §5.2)
- [ ] Include the H6 pre-registration limitation (`findings.md` §5.3)
- [ ] Include infrastructure exclusions (`problem_framing.md` §4)
- [ ] Include Phase C skip rationale (`stop_criteria.md` §4.3)

### D3. Update README files

- [ ] Update root `README.md` with V2 headline result and pointer to `docs/v2/`
- [ ] Confirm `docs/v2/README.md` (from A3) is final
- [ ] Confirm `docs/README.md` links to V2 docs

### D4. Open-source packaging

- [ ] Add `LICENSE` — required for open-source publication
- [ ] Add `CITATION.cff` or a citation block in `README.md` — standard for a research artifact
- [ ] Confirm dataset license (BAF: CC BY 4.0) is named and not conflated with the code license
- [ ] Confirm `data/original/Base.csv` remains gitignored (V1 rule)
- [ ] Confirm `models/*.pkl` and `models/*.json` remain whitelisted (V1 rule)

### D5. Blog post / LinkedIn series

- [ ] Draft the post (the only optional Phase D deliverable per `stop_criteria.md` §4.4)
- [ ] Hook: V1's headline survived operational reality; two concerns were tested and dismissed
- [ ] Body: the six verdicts, the falsification discipline, the two earned Phase B builds
- [ ] Close: what was deliberately not done (points at `cut_list.md`)

### D6. Architecture diagram (if any Phase B component is built)

- [ ] Write `docs/v2/architecture.md` **after** B1 and B2 complete, not before (`problem_framing.md` §7)

---

## What Is NOT in This TODO

Explicitly excluded per V2's own documents. Adding any of these is a scope violation.

| Item | Why it is excluded | Source |
|---|---|---|
| New hypotheses (H7+) | Requires pre-registered kill criterion and mid-flight scope gate pass | `stop_criteria.md` §8 |
| New classifier search | V1's noise band is closed; H3 confirmed it | `problem_framing.md` §4 |
| New cost matrix | Frozen; change is a new experiment | `problem_framing.md` §4 |
| Cost-sensitive training | Out of scope per §5.2 | `problem_framing.md` §5.2 |
| Calibration method comparison | Gate passes at 0.0033; no measured failure | `problem_framing.md` §5.2 |
| Fairness constraint build | H5 killed | `findings.md` §7.1 |
| IPW / doubly robust estimator | Phase C skipped; bias below materiality | `stop_criteria.md` §4.3 |
| MLflow / DVC / Docker / CI-CD / FastAPI | Tooling theater | `problem_framing.md` §4 |
| A V2 paper longer than V1's | Capped at one subsection | `problem_framing.md` §6.2 |
| Re-touching V1's frozen test window with new modeling | Abandon criterion | `stop_criteria.md` §7 |
| Adding a third Phase B build | Phase B is bounded by survivors | `stop_criteria.md` §4.2 |

---

## Definition of Done — 2026-10-03 (today)

Today's achievable target is Phase A exit plus a Phase B entry plan.

- [ ] A1 — `reports/v2_falsification.md` written
- [ ] A2 — `docs/v2/documentation_map.md` written
- [ ] A3 — `docs/v2/README.md` written
- [ ] Phase A exit confirmed (all three files exist)
- [ ] Phase B entry gate satisfied (`stop_criteria.md` §4.2)
- [ ] B1 protocol drafted (`docs/v2/protocols/decision_policy_capacity.md`)
- [ ] B2 protocol drafted (`docs/v2/protocols/monitoring.md`)
- [ ] `git status` clean
- [ ] No V1 file modified beyond the amendments recorded in `documentation_map.md`
- [ ] No kill criterion modified after results were seen

---

## Suggested Commit Sequence

1. `docs(v2): assemble Phase A falsification report`
2. `docs(v2): add V1→V2 documentation map`
3. `docs(v2): add V2 reading order for external readers`
4. `docs(v2): mark Phase A exit complete`
5. `docs(v2): draft capacity-aware policy protocol`
6. `docs(v2): draft drift monitoring protocol`
7. `feat(v2): implement capacity-aware policy`
8. `feat(v2): implement drift detector`
9. `docs(v2): add Phase B addendum to falsification report`
10. `docs(v2): add V1 paper V2 subsection`
11. `docs(v2): write cut list`
12. `chore(v2): add LICENSE and citation`
13. `docs(v2): update READMEs for publication`
14. `docs(v2): publish LinkedIn / blog post`

---

## Notes and Rules

- The V2 framework is frozen at v2.0.1. Do **not** change `problem_framing.md`, `falsification_plan.md`, `evaluation_framework.md`, or `stop_criteria.md` except to record completed work in their DoD sections.
- Phase C is skipped. It is not deferred; it is skipped (`stop_criteria.md` §4.3).
- Kill criteria are not modified after results are seen. The one H1 amendment (2026-10-03) was made before H1 ran.
- V1's test window is used once. V2 hypotheses that reuse frozen scores (H1, H5, H6) are analyses, not new uses (`evaluation_framework.md` §4.1).
- A non-finding is reported at the same length as a finding.
- Any addition after Phase A exit requires a pre-registered hypothesis, a cheapest test, a pass, and a time-box amendment (`stop_criteria.md` §8).
- If a Phase B build hits its 3-week time-box without a result, drop it and record it as future work. Do not extend.
- The `reports/v2/intermediate/` JSON files are the source of truth for every number in `reports/v2_falsification.md`.

---

## Files Created or Modified Today

**Phase A exit (3):**
- `reports/v2_falsification.md` — assembled report
- `docs/v2/documentation_map.md` — V1→V2 status
- `docs/v2/README.md` — V2 reading order

**Phase B protocol drafts (2):**
- `docs/v2/protocols/decision_policy_capacity.md`
- `docs/v2/protocols/monitoring.md`

**Phase D packaging (planned, not today):**
- `docs/v2/cut_list.md`
- `LICENSE`
- `CITATION.cff`
- Root `README.md` update
- V1 paper V2 subsection