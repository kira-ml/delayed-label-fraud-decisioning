# V2 Problem Framing: Operational Reality Testing

> **Repository:** `delayed-label-fraud-decisioning`  
> **Branch:** `v2`  
> **Purpose:** Portfolio / resume — operational extension of the V1 final-project system  
> **Document:** V2 Problem Framing / charter  
> **Status:** v2.0-draft — decision-centric framing, V1 inheritance, falsification-first  
> **Last updated:** 2026-10-02

---

## 0. How to Read This Document

This document is the **root of V2**. It inherits V1's framing without
re-deriving it. Every other V2 document — falsification plan, documentation
map, conditional specs, reports, paper section — must trace a sentence to
this file.

**Rule:** If a V2 document cannot be traced to a sentence in this document,
either the document is unjustified or this document is incomplete.

**Rule:** V1's `docs/problem_framing.md` remains the charter for the
decision-centric framing. V2 does **not** re-derive that framing. V2 tests
whether V1's conclusion survives conditions V1 did not exercise.

**Rule:** No V2 code is written before the falsification plan produces a
survivor. A hypothesis that fails its kill criterion is reported as a
non-finding and dropped from scope.

---

## 1. One-Sentence V2 Project

Test whether V1's cost-sensitive fraud decision policy — which reduced
realized cost by 57.91% vs. the strongest baseline under static,
single-delay, unconstrained conditions — **survives operational reality**:
finite review capacity, longer label delay, rolling retraining, input drift,
confounding, and group disparity.

---

## 2. The V1 Conclusion Under Test

V1 produced a single headline finding, restated here exactly:

> Under a 1-month delayed-label regime, on a fixed chronological split
> (train months 0–2, validation 3–4, test 5–6, censored 7), with a frozen
> cost matrix and no review capacity constraint, a cost-sensitive policy
> fed by a Logistic Regression classifier produced a realized cost per
> transaction of **0.007491** on the test window, against a strongest
> baseline of **0.017798** (LGBM + static 0.5). The advantage is **57.91%**
> with a 95% bootstrap CI of **[53.95%, 62.13%]**.

V1 also produced two supporting findings:

- **Calibration:** ECE = 0.0033 on validation. Gate passed. No calibration
  step applied.
- **Classifier selection:** LGBM vs. LR gap on validation realized cost was
  1.07%, below the 5% noise band. Non-finding. LR selected by simplicity.

Three properties of V1's setup are load-bearing for the headline:

1. **Static split.** One train/val/test partition. No retraining.
2. **Single delay regime.** `label_time = month + 1`. No other regime tested.
3. **Unconstrained review.** Every transaction routed to `review` is
   reviewed. There is no queue, no capacity, no prioritization within band.

If any of those three properties is what produced the advantage — rather
than the decision-centric framing itself — V1's conclusion is narrower than
it appears.

---

## 3. The V2 Fundamental Question

> **Does the V1 decision-centric advantage survive when the three
> load-bearing properties above are relaxed, and when the evaluation
> accounts for confounding and group disparity?**

Stated as a falsifiable claim:

> **H0:** The V1 advantage (>5% relative cost reduction, 95% CI excluding
> zero) is robust to finite review capacity, longer label delay, rolling
> retraining, measurable input drift, confounding, and group disparity.

V2's job is to test H0 and report where it holds, where it degrades, and
where it breaks.

This is a **robustness and validity question**, not a new-model question.
V2 does not search for a better classifier, a better cost matrix, or a
better policy. V2 asks whether the existing result means what V1 claims it
means.

---

## 4. What V2 Is Not

Explicit, so scope discipline is enforceable.

- **Not a rewrite.** V1's pipeline, cost matrix, split, and evaluation
  protocol remain the standards. V2 extends; it does not replace.
- **Not a tooling exercise.** MLflow, DVC, Docker, CI/CD, and a FastAPI
  layer are not in V2 scope. They do not change the answer to §3's
  question. Their omission is documented in `docs/v2/cut_list.md` when
  written.
- **Not a new model search.** No neural networks, transformers, LLMs,
  AutoML, or algorithm leaderboards. The classifier comparison in V1
  established the noise band; V2 does not re-open it unless a robustness
  test invalidates it.
- **Not a new cost matrix.** V1's `configs/costs.yaml` is frozen. Changing
  it would be a new experiment with its own reported result, not a V2
  upgrade.
- **Not a production deployment.** V1's Streamlit app remains the demo.
  V2 adds robustness findings, not a service layer.
- **Not a paper rewrite.** V1's IMRaD paper stands. V2 adds a results
  subsection on operational robustness. If V2 grows beyond one subsection,
  that is a signal the scope has drifted.

---

## 5. Scope

### 5.1 In Scope

The following are in scope because §3 requires them. Each is a hypothesis
with a cheapest test and a kill criterion, detailed in
`docs/v2/falsification_plan.md`.

| ID | Hypothesis | What it tests |
|---|---|---|
| H1 | Policy advantage stays >5% at plausible review capacity | Load-bearing property 3 |
| H2 | Policy advantage stays >5% at 2-month delay | Load-bearing property 2 |
| H3 | LR still wins under rolling monthly retraining | Load-bearing property 1; V1's classifier conclusion |
| H4 | Feature drift is measurable month-over-month | Validity of the static split |
| H5 | Block rate differs >5pp across protected groups | Group disparity |
| H6 | Direct cost estimate matches causal estimate | Confounding of the V1 advantage |

### 5.2 Out of Scope

Explicitly deferred, with reasons:

- **Cost-sensitive training.** V1 established that decision-time cost
  handling is what matters. Moving cost into the training loss tests a
  different question than §3's.
- **Calibration method comparison.** V1 passes the gate at ECE = 0.0033.
  Platt vs. isotonic vs. beta is a solution to a problem that does not yet
  exist. If H2 or H4 causes ECE to exceed 0.05, this becomes in-scope as a
  response.
- **Fairness constraint implementation.** H5 is diagnostic only. A
  constraint is built only if the diagnostic shows measurable disparity
  worth constraining.
- **Full causal policy optimization.** H6 tests whether the V1 estimate is
  confounded. It does not attempt to optimize a policy under
  counterfactuals. That is a separate project.
- **Infrastructure.** As stated in §4.
- **Multi-currency, multi-market, or multi-product extensions.** Not
  required by §3.

### 5.3 The Base Rate Assumption

Per V1's own evidence — LGBM vs. LR was a non-finding inside the noise
band — the prior is that **most V2 hypotheses will not survive their kill
criteria.** This is expected and is not a V2 failure. V2 succeeds if it
produces at least one finding that either:

- confirms the V1 advantage under a harder condition (a *robustness
  confirmation*), or
- falsifies it in a documented regime (a *fragility finding*).

Either outcome is publishable as a portfolio result. A V2 that reports
"all six hypotheses tested, one survived, five are non-findings, here is
what each non-finding means" is a stronger artifact than a V2 that ships
five half-verified capabilities.

---

## 6. Success Criteria

### 6.1 Primary

V2 succeeds if:

1. Every hypothesis in §5.1 is tested with its documented cheapest test.
2. Every hypothesis has a recorded verdict: **survived**, **killed**, or
   **inconclusive — needs more data**.
3. Every verdict is written to `reports/v2_falsification.md` with the
   evidence that produced it.
4. At least one hypothesis either confirms the V1 advantage under a harder
   condition or falsifies it in a documented regime.
5. V1's headline numbers are either unchanged (if H0 holds) or explicitly
   amended (if H0 is falsified in a stated regime).
6. No hypothesis is silently dropped. Dropped hypotheses are recorded as
   dropped, with the reason.

### 6.2 Secondary

- V2 adds at most one subsection to V1's IMRaD paper.
- V1's `docs/paper/reference_sheet.md §1` is updated with V2 numbers, with
  V1 numbers preserved and labeled "V1 conditions."
- A blog post or LinkedIn series communicates the V2 finding.
- `docs/v2/documentation_map.md` records V1→V2 status for every V1 doc.
- The V2 folder contains no empty subfolders and no speculative specs.

### 6.3 What Does Not Count as V2 Success

- A larger repository with more tooling.
- A higher headline advantage produced by a new model.
- A V2 paper longer than V1's.
- Any claim that is not backed by a documented test and a verdict.
- A non-finding reported as a finding.
- A finding reported without a kill criterion that was written before the
  test.

---

## 7. Relationship to V1 Documents

The full mapping is in `docs/v2/documentation_map.md`. The governing rules:

- **V1's `problem_framing.md` and `first_principles_decomposition.md` are
  inherited unchanged.** V2 does not re-derive the decision-centric
  framing.
- **V1's `evaluation_protocol.md` is extended, not replaced.** V2 metrics
  (capacity utilization, multi-regime censoring, IPW estimates, group
  disparity) are added as sections.
- **V1's `decision_policy.md` is extended.** §8 (Capacity Override) moves
  from "specification, deferred" to "implemented" **only if H1 survives**.
- **V1's `data_card.md` is extended** with multi-regime delay rules **only
  if H2 survives**.
- **V1's `mvp_architecture.md` remains the as-built description of V1.**
  V2's as-built architecture is written as `docs/v2/architecture.md`
  **after** components are built, not before.
- **V1's `roadmap.md` and `TODO.md` are superseded** for V2 work. V1's
  roadmap moves to `docs/archive/` when V2 work begins. V2's roadmap is
  written after Phase A, informed by which hypotheses survived.

**Rule:** No V1 document is silently altered. If V2 contradicts a V1 claim,
the V1 claim is amended with a dated note, and the change is recorded in
`docs/v2/documentation_map.md`.

---

## 8. The Falsification Discipline

V2's organizing principle is the scientific falsification loop:

1. **State the assumption.** H1–H6 in §5.1.
2. **State the cheapest test.** Detailed in `docs/v2/falsification_plan.md`.
3. **State the kill criterion before running the test.** Numeric. No
   post-hoc thresholds.
4. **Run the test on existing artifacts.** No new code beyond what the test
   requires.
5. **Record the verdict.** Survived / killed / inconclusive.
6. **Update V1's claims if H0 is falsified.** The V1 headline is amended,
   not defended.
7. **Kill what died.** A killed hypothesis is dropped from scope. It is not
   "kept for future work" unless the future work has its own falsifiable
   hypothesis and kill criterion.

The full falsification plan is the next document written, before any V2
code.

---

## 9. Risks Named in Advance

| Risk | Mitigation |
|---|---|
| Kitchen-sink V2 | §4 and §5.2 explicit; cut list published |
| Tooling theater | §4 excludes MLflow / Docker / CI/CD / API by name |
| Rewriting V1 | §7 governs V1→V2 relationship; V1 docs inherited |
| Evaluating on test again | Any V2 test that re-touches the V2 test window is treated as a new experiment with its own protocol |
| Killing the interesting question | H6 (causal) is the highest-ceiling item; it is scoped as a test, not a build |
| Non-finding reported as finding | §6.1 requires a verdict per hypothesis, including "killed" |
| V2 paper drifts | §6.2 caps V2 paper addition at one subsection |
| Scope creep through "while I'm here" | §5.2 and §4 name the boundary; the cut list is the enforcement |

**One V2-specific risk worth naming separately:** V1's classifier selection
(LR over LGBM) is itself a load-bearing claim. If H1 or H3 invalidates it,
V1's paper must be amended, not quietly left standing. The V2 falsification
plan must anticipate this outcome.

---

## 10. Definition of Done for This Document

- [x] V1's conclusion under test is restated exactly (§2)
- [x] V2's fundamental question is stated as a falsifiable claim (§3)
- [x] What V2 is not is explicit (§4)
- [x] Hypotheses H1–H6 are named with the load-bearing property each tests (§5.1)
- [x] Out-of-scope items are named with reasons (§5.2)
- [x] Success criteria are numeric and per-hypothesis (§6)
- [x] V1→V2 document relationship rules are stated (§7)
- [x] Falsification discipline is the organizing principle (§8)
- [x] Risks are named before work begins (§9)

**Not yet done (downstream, not blockers for this doc):**

- [ ] `docs/v2/falsification_plan.md` — the six cheapest tests and their kill criteria
- [ ] `docs/v2/documentation_map.md` — V1→V2 status table
- [ ] `docs/v2/README.md` — reading order for the folder
- [ ] `docs/v2/cut_list.md` — what V2 does not do and why

---

## 11. Guiding Rules

> V1 asked whether a decision-centric framing beats a classification
> framing. V2 asks whether the decision-centric framing survives
> operational reality. These are different questions with different
> methods.

> Every V2 hypothesis has a cheapest test and a numeric kill criterion
> written before the test is run. No exceptions.

> A hypothesis that fails its kill criterion is reported as a non-finding
> and dropped from scope. Dropping a hypothesis is a legitimate outcome.

> Complexity is added only against a measured failure of the V1 system.
> The V1 system has no measured failure under V1 conditions. Every V2
> addition must be justified by its own measured failure under harder
> conditions.

> If V2 contradicts V1, V1 is amended. The V1 headline is not defended.

> The test window is used once per experiment. V2 experiments that
> re-touch V1's test window are new experiments with their own
> pre-registered protocol, not reuses of V1's.

---

## 12. References

- `docs/problem_framing.md` — V1 charter
- `docs/first_principles_decomposition.md` — V1 derivation
- `docs/evaluation_protocol.md` — V1 evaluation standard
- `docs/decision_policy.md` — V1 policy definition
- `docs/data_card.md` — V1 dataset and split definition
- `docs/v2/falsification_plan.md` — the six tests (to be written)
- `docs/v2/documentation_map.md` — V1→V2 doc status (to be written)
- Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular
  Datasets for ML Evaluation," NeurIPS 2022
- Elkan, "The Foundations of Cost-Sensitive Learning," IJCAI 2001

---

## 13. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | v2.0-draft — initial V2 charter; V1 conclusion restated; hypotheses H1–H6 scoped; falsification discipline adopted; cut list referenced; base-rate assumption stated | First-principles scoping of V2 as an operational-reality test of V1's conclusion, not a feature extension |
