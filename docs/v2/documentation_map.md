# V2 Documentation Map

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Document:** V1→V2 documentation status
> **Status:** v1.0 — Phase A exit artifact
> **Last updated:** 2026-10-03
> **Governing documents:** `docs/v2/problem_framing.md` §7,
> `docs/v2/falsification_plan.md` §7

---

## 0. Purpose

This document records the status of every V1 document under V2. It is
required by `problem_framing.md` §7 and referenced by
`stop_criteria.md` §9.

**Rule:** No V1 document is silently altered. If V2 contradicts a V1
claim, the V1 claim is amended with a dated note, and the change is
recorded here.

**Rule:** A V1 document marked **inherited** means V2 does not change
it. A document marked **extended** means V2 adds sections or fields
without altering V1's existing text. A document marked **superseded**
means V2 work no longer reads it as a live source.

---

## 1. V1 Foundation Documents

| Document | V2 status | V2 change | Result that caused it |
|---|---|---|---|
| `docs/problem_framing.md` | **inherited** | none | V2 does not re-derive the decision-centric framing |
| `docs/first_principles_decomposition.md` | **inherited** | none | V2 does not re-derive the derivation |
| `docs/data_card.md` | **extended** | §5 delay rules extended with 2-month regime | H2 survived |
| `docs/decision_policy.md` | **extended** | §8 (Capacity Override) moves from "specification, deferred" to "implemented" in Phase B | H1 survived |
| `docs/evaluation_protocol.md` | **extended** | V2 metric categories (capacity, multi-regime delay, rolling, drift, fairness, causal validity) added as extensions | H1, H2, H3, H4, H5, H6 |

---

## 2. V1 Build and Implementation Documents

| Document | V2 status | V2 change | Result that caused it |
|---|---|---|---|
| `docs/mvp_architecture.md` | **inherited** | none | Still describes V1 as-built; V2 architecture written separately as `docs/v2/architecture.md` after Phase B builds |

---

## 3. V1 Process and Plan Documents

| Document | V2 status | V2 change | Result that caused it |
|---|---|---|---|
| `docs/roadmap.md` | **superseded for V2** | V1 roadmap archived; V2 roadmap written in `docs/v2/falsification_plan.md` §4 and `docs/v2/stop_criteria.md` §4 | V2 has its own phased plan |
| `docs/TODO.md` | **superseded for V2** | V2 TODO is `docs/v2/TODO.md` (created 2026-10-03) | V2 has its own open work list |

---

## 4. V1 Paper Documents

| Document | V2 status | V2 change | Result that caused it |
|---|---|---|---|
| `docs/paper/paper_blueprint.md` | **extended** | V2 subsection location noted | H1–H6 |
| `docs/paper/reference_sheet.md` | **extended** | V2 numbers added to §1, V1 numbers preserved with "V1 conditions" labels | H1–H6 |
| `docs/paper/introduction_draft.md` | **inherited** | none | V2 introduces no new framing |
| `docs/paper/abstract_and_index_terms.md` | **inherited** | none | V2 does not rewrite the abstract |

---

## 5. V1 Documentation Directory

| Document | V2 status | V2 change | Result that caused it |
|---|---|---|---|
| `documentation/data_dictionary.md` | **inherited** | none | Features are unchanged |
| `documentation/technical_documentation.md` | **extended** | Phase B component entry points added after Phase B | H1, H4 |
| `documentation/app_guide.md` | **inherited** | none | V2 adds no app surface |

---

## 6. V1 Amendments Recorded

Per `falsification_plan.md` §7, each amendment is dated and preserved
at the point of the claim. This table is the index.

| H | V1 document | V1 claim amended | Nature of amendment |
|---|---|---|---|
| H1 | Limitations section of V1 paper | Advantage stated as unconditional | Capacity envelope added: 44.25% at 2%, 53.11% at 5%, 57.91% unconstrained |
| H2 | Limitations section of V1 paper | Delay stated as 1 month only | Delay envelope added: 58.08% at 2-month delay |
| H3 | Classifier-selection subsection of V1 paper | LR selected over LGBM at 1.07% gap | Fragility note: 4.25% / 4.17% under rolling |
| H4 | Limitations section of V1 paper | Drift named but not quantified | 23/28 features drift; concentrated on low-importance features |
| H5 | Limitations section of V1 paper | Segment disparity out of scope | Non-finding: block-rate disparity < 5pp across tested groupings |
| H6 | Limitations section of V1 paper | Direct estimate assumed unbiased | Non-finding: block-stratum ECE 0.0600; bias ~2.1% |

**No amendment overturns V1's headline.** The V1 headline is preserved
with a conditions label wherever it appears in a V1 document.

---

## 7. Definition of Done

- [x] All V1 foundation documents mapped
- [x] All V1 build documents mapped
- [x] All V1 process documents mapped
- [x] All V1 paper documents mapped
- [x] All V1 documentation-directory documents mapped
- [x] V1 amendments indexed with the hypothesis that caused them
- [x] Rule stated: no V1 document is silently altered