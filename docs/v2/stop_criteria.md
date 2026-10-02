# V2 Stop Criteria

> **Repository:** `delayed-label-fraud-decisioning`  
> **Branch:** `v2`  
> **Purpose:** Portfolio / resume — operational extension of the V1 final-project system  
> **Document:** V2 Stop Criteria  
> **Status:** v2.0-draft — meta-level gates; does not duplicate per-hypothesis kill criteria  
> **Last updated:** 2026-10-02

---

## 0. Derivation and Non-Duplication Rule

This document is derived from `docs/v2/falsification_plan.md` §5–§6 and
`docs/v2/evaluation_framework.md` §8.

**Rule:** This document does **not** restate the per-hypothesis kill
criteria. Those live in `falsification_plan.md` §3 and are the source of
truth. This document only consolidates them by reference.

**Rule:** This document adds the **meta-level** stop criteria that do not
exist elsewhere: phase gates, project-level stop, time-boxes, abandon
criteria, and mid-flight scope gates. If a rule is already stated in
`falsification_plan.md` or `evaluation_framework.md`, it is cited, not
duplicated.

**Rule:** This document is the operational companion to the falsification
plan. The falsification plan defines *what* is tested. This document
defines *when V2 stops*.

---

## 1. Purpose

V2 has three separate stopping questions that the existing docs answer
only partially:

1. **Per hypothesis:** does this specific test produce a verdict?
   → answered in `falsification_plan.md` §3 and §5.
2. **Per phase:** when does Phase A end, and when does Phase B begin?
   → **not answered.**
3. **Per project:** when is V2 done, and under what conditions is V2
   abandoned entirely?
   → **not answered.**

This document answers (2) and (3). It exists to prevent three failure
modes:

- **Endless phase A.** A hypothesis that never produces a clean verdict
  blocks everything downstream. Without a time-box, V2 stays in
  Phase A indefinitely.
- **Silent scope expansion.** A hypothesis survives, and the scope quietly
  grows to include follow-up questions that were never pre-registered.
  Without a scope gate, Phase B expands without bound.
- **Missing project stop.** V2 has no defined completion criterion. The
  branch lingers, the paper section is never written, and the portfolio
  artifact never ships. Without a project-level stop, V2 has no definition
  of done.

---

## 2. Relationship to Other V2 Documents

| Document | Defines | This doc's relationship |
|---|---|---|
| `problem_framing.md` §6 | What V2 success means | Inherited |
| `problem_framing.md` §8 | Falsification discipline | Inherited |
| `falsification_plan.md` §3 | Per-hypothesis kill criteria | Referenced (§3) |
| `falsification_plan.md` §4 | Execution order | Inherited |
| `falsification_plan.md` §5 | Verdict format | Inherited |
| `falsification_plan.md` §6 | Non-findings discipline | Inherited |
| `falsification_plan.md` §7 | V1 amendment rules | Inherited |
| `evaluation_framework.md` §8 | Verdicts and stop criteria per hypothesis | Referenced |
| `evaluation_framework.md` §9 | Forbidden practices | Inherited |
| **This document** | **Phase gates, time-boxes, project stop, abandon rules, scope gate** | **New** |

**Rule:** if a stop rule appears in two documents, the more specific
document wins. `falsification_plan.md` §3 wins for per-hypothesis kill
criteria. This document wins for phase and project stop.

---

## 3. Per-Hypothesis Kill Criteria — Reference Only

This table consolidates the kill criteria for convenience. The source of
truth is `falsification_plan.md` §3.

| ID | Kill criterion (from `falsification_plan.md` §3) |
|---|---|
| H1 | Advantage < 5% at any capacity `K ≥ 4,550` |
| H2 | Advantage < 5% at 2-month delay |
| H3 | Model choice flips in either rolling step |
| H4 | Max PSI < 0.1 across all features and adjacent month pairs |
| H5 | Max block-rate disparity < 5 percentage points |
| H6 | Any action stratum has ECE ≥ 0.05 |

**No rule in this document modifies these criteria.** Changes to a kill
criterion are dated amendments to `falsification_plan.md`, not edits to
this table.

---

## 4. Phase Gates

V2 executes in four phases. Each phase has an entry gate and an exit gate.
No phase begins before the previous phase's exit gate is satisfied.

### 4.1 Phase A — Falsification

| Gate | Criterion |
|---|---|
| **Entry** | `docs/v2/problem_framing.md`, `falsification_plan.md`, `documentation_map.md`, and this document exist and are reviewed |
| **Exit** | `reports/v2_falsification.md` exists; all six verdicts recorded; no hypothesis is `Blocked` |

**Exit criterion in detail:** the report is written only when every
hypothesis has a verdict from the set in `falsification_plan.md` §5. A
`Blocked` verdict does not count as an exit — it is a diagnostic signal
that must be resolved before the report is finalized.

### 4.2 Phase B — Depth on Survivors

| Gate | Criterion |
|---|---|
| **Entry** | Phase A exit satisfied; **at least one** hypothesis has verdict `Survived` |
| **Exit** | For each surviving hypothesis: conditional protocol doc exists, implementation exists, result is reported, verdict on the Phase B work is recorded |

**Exit criterion in detail:** Phase B is bounded by the survivors of
Phase A. If H1 and H4 survive, Phase B consists of exactly two builds:
capacity-aware policy and drift detector. No other components enter
Phase B without the mid-flight scope gate (§8).

### 4.3 Phase C — Causal Evaluation (Conditional)

| Gate | Criterion |
|---|---|
| **Entry** | Phase B exit satisfied; **H6 was killed** with a material bias estimate (> 5% of the V1 advantage) |
| **Exit** | Causal estimator built and reported; V1 headline either confirmed or amended in the affected stratum |

**Note:** Phase C is skipped if H6 survived. The direct estimate is
approximately unbiased, and no causal machinery is built.

### 4.4 Phase D — Communication

| Gate | Criterion |
|---|---|
| **Entry** | Phase B exit satisfied (Phase C not required for Phase D entry) |
| **Exit** | V1's paper has one V2 subsection; `docs/v2/cut_list.md` is written; README updated; blog post or LinkedIn series published; architecture diagram (if any component was built) exists |

**Exit criterion in detail:** Phase D is time-boxed (§6). If the paper
subsection, cut list, and README update are complete, Phase D exits even
if the blog post is not yet published. The blog post is the only
optional Phase D deliverable.

### 4.5 Phase Gate Summary

```
Phase A ──► Phase B ──► Phase D
                │
                └──► Phase C ──► Phase D
                     (only if H6 killed)
```

Phase C is not on the critical path. It is inserted between B and D
only when H6 is killed.

---

## 5. Project-Level Stop

V2 stops when **any** of the following conditions is met.

### 5.1 Complete Stop (Success)

All of:

- Every hypothesis has a verdict
- Phase B has produced a result for every surviving hypothesis
- Phase C has either produced a result or been formally skipped
- Phase D exit criteria are met

**Outcome:** V2 is done. Branch is merged or tagged. Portfolio artifact
is published. No further V2 work is authorized without a new charter.

### 5.2 Falsification-Only Stop (Legitimate Non-Outcome)

All of:

- Every hypothesis has a verdict
- **Zero** hypotheses survived
- Phase A exit criteria are met

**Outcome:** V2 is a falsification report only. Phase B and Phase D
collapse into: update V1's paper limitations section, publish
`reports/v2_falsification.md`, write a short blog post on the negative
result. This is a legitimate and portfolio-worthy outcome. It is **not**
a V2 failure.

### 5.3 Partial Stop (Time-Boxed)

All of:

- Every hypothesis has a verdict
- At least one survived
- Phase B has hit its time-box (§6) for at least one survivor without
  producing a Phase B result

**Outcome:** The un-built survivor's Phase B is dropped. Its verdict in
`reports/v2_falsification.md` is amended with a note: *"Survived Phase A;
Phase B time-boxed without result; retained as future work."* V2 completes
with the survivors that produced Phase B results.

### 5.4 Abandon Stop (Diagnostic)

Any of:

- More than one hypothesis is `Blocked` at Phase A exit (§7)
- V1's headline is contradicted and the contradiction cannot be resolved
  through V1 amendment
- The falsification plan cannot be executed on existing artifacts

**Outcome:** V2 is paused. Diagnose root cause. Do not proceed. Do not
report V2 as complete or abandoned until the root cause is resolved.

---

## 6. Time-Boxes

Time-boxes exist to prevent scope drift. They are the operational
enforcement of via negativa.

| Phase | Time-box | On overrun |
|---|---|---|
| Phase A — per hypothesis | 1 working day | Kill as `Inconclusive`; move to next hypothesis |
| Phase A — total | 5 working days | Write the falsification report with available verdicts; unresolved hypotheses recorded as `Inconclusive` |
| Phase B — per hypothesis | 3 working weeks | Drop Phase B for that survivor; record as future work |
| Phase B — total | 9 working weeks | Phase B exits with whatever survived; do not extend |
| Phase C | 4 working weeks | Drop Phase C; V1 headline is not causally validated; record as future work |
| Phase D | 1 working week | Paper subsection and cut list take priority; blog post becomes optional |

**Rule:** time-boxes are measured in **working days** and **working weeks**,
not calendar time.

**Rule:** hitting a time-box is not a kill criterion. It is a stop
condition. The hypothesis or component is dropped from scope, not reported
as falsified.

**Rule:** overruns are diagnosed. If a Phase A hypothesis takes more than
two days, the overrun is recorded and the *cause* is named. Repeated
overruns of the same kind signal a problem with the falsification plan,
not with the test.

---

## 7. Abandon Criteria

V2 is abandoned, not just paused, if **either** of the following is true
at Phase A exit:

1. **More than one `Blocked` verdict.** A single `Blocked` is a diagnostic
   signal. More than one suggests the falsification plan is not executable
   on existing artifacts, and the plan itself is the problem.
2. **A surviving hypothesis cannot be tested without violating V1's test
   window discipline.** If a survivor requires re-touching V1's frozen test
   window with new modeling, V2's framing is wrong. Abandon and re-charter.

**On abandonment:**

- Do **not** write a blog post claiming V2 succeeded.
- Do **not** merge the branch. Keep it as an archive.
- Do **not** delete `reports/v2_falsification.md` if it exists. It is
  evidence.
- Write a short note in `docs/v2/README.md` recording the abandonment and
  the reason.
- Do **not** open a new V2 attempt until the reason for abandonment is
  understood. Rebooting the same plan will fail the same way.

---

## 8. Mid-Flight Scope Gate

Phase B has a scope-drift risk: a survivor's Phase B work suggests an
adjacent improvement that was not pre-registered. Without a gate, Phase B
expands.

**Rule:** no addition to V2 scope after Phase A exits. All additions
require:

1. A pre-registered falsifiable hypothesis, written in
   `falsification_plan.md` as an amendment with a date
2. A Phase A–style cheapest test with a numeric kill criterion
3. A recorded pass of that cheapest test
4. An amendment to this document's Phase B time-box if the addition
   materially extends Phase B

**Additions that fail any of the four requirements are rejected.** They
are recorded in `docs/v2/cut_list.md` as explicitly out of scope.

**Corollary:** "While I'm here, I might as well…" is not an addition.
It is a scope violation.

---

## 9. Definition of Done for This Document

- [x] Non-duplication rule stated (§0)
- [x] Relationship to V1 and V2 docs stated (§2)
- [x] Per-hypothesis kill criteria referenced, not duplicated (§3)
- [x] Phase gates defined for A, B, C, D (§4)
- [x] Project-level stop conditions defined (§5)
- [x] Time-boxes defined per phase (§6)
- [x] Abandon criteria defined (§7)
- [x] Mid-flight scope gate defined (§8)

**Downstream (not blockers for this doc):**

- [ ] `docs/v2/documentation_map.md` — V1→V2 doc status table
- [ ] `docs/v2/README.md` — reading order for the folder
- [ ] `docs/v2/cut_list.md` — written at Phase D
- [ ] Run Phase A tests; write `reports/v2_falsification.md`

---

## 10. Guiding Rules

> Per-hypothesis kill criteria live in `falsification_plan.md` §3. This
> document references them; it does not duplicate them.

> Phase B is bounded by the survivors of Phase A. No other components
> enter Phase B without the mid-flight scope gate.

> Time-boxes are stop conditions, not kill criteria. Hitting a time-box
> drops the work; it does not falsify the hypothesis.

> V2 stops at the earliest of: all phases complete, all hypotheses killed,
> or one time-box overrun past its limit.

> A falsification-only V2 with zero survivors is a legitimate outcome. It
> is reported, not hidden.

> If V2 requires re-touching V1's frozen test window with new modeling,
> V2's framing is wrong. Abandon and re-charter.

> Additions after Phase A exit require a pre-registered hypothesis, a
> cheapest test, a pass, and a time-box amendment. Anything less is a
> scope violation.

---

## 11. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | v2.0-draft — initial stop criteria; phase gates for A/B/C/D; project-level stop conditions; time-boxes; abandon criteria; mid-flight scope gate; per-hypothesis kill criteria referenced from `falsification_plan.md` §3 | Meta-level companion to `falsification_plan.md` and `evaluation_framework.md`; adds the phase, project, and scope stop rules that do not exist elsewhere |
