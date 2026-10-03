# V2 — Operational Reality Testing

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Purpose:** Portfolio / resume — operational extension of the V1
> final-project system
> **Status:** Phase A complete; Phase B entered; Phase C skipped

---

## What V2 Is

V2 tests whether V1's cost-sensitive fraud decision policy — which
reduced realized cost by 57.91% vs. the strongest baseline under static,
single-delay, unconstrained conditions — survives operational reality:
finite review capacity, longer label delay, rolling retraining, input
drift, confounding, and group disparity.

V2 is a **falsification exercise**, not a feature extension. Six
hypotheses were pre-registered with numeric kill criteria written before
the tests ran. Three survived, one was confirmed-with-fragility, two
were killed.

**V1's headline is not overturned.** It is strengthened by H1
(capacity-robust) and H2 (delay-robust), confirmed-with-fragility by
H3, and challenged-but-not-broken by H4. Two proposed concerns (H5, H6)
were tested and dismissed.

---

## Reading Order — Reviewer / Instructor (30 minutes)

The five files that define what V2 claims and what it found.

1. [`problem_framing.md`](problem_framing.md) — what V2 tests and why
2. [`falsification_plan.md`](falsification_plan.md) §3 — the six
   hypotheses and their pre-registered kill criteria
3. [`falsification_plan.md`](falsification_plan.md) §12 — the six
   verdicts
4. [`../reports/v2_falsification.md`](../../reports/v2_falsification.md)
   — the assembled report
5. [`stop_criteria.md`](stop_criteria.md) §5 — the project-level stop
   and the Phase B / C / D decisions

Stop after those five if you only have 30 minutes.

---

## Reading Order — External Reader (GitHub visitor)

Understand what V2 found before the machinery that produced it.

1. [`../reports/v2_falsification.md`](../../reports/v2_falsification.md)
   — the assembled report
2. [`findings.md`](findings.md) §1–§4 — headline result and V1
   headline status
3. [`problem_framing.md`](problem_framing.md) §3 — the fundamental
   question
4. [`stop_criteria.md`](stop_criteria.md) §4.2 — why Phase B is exactly
   two builds

---

## Reading Order — Paper Team

Four files, in this order.

1. [`../reports/v2_falsification.md`](../../reports/v2_falsification.md)
   — the report
2. [`documentation_map.md`](documentation_map.md) — V1→V2 status
3. [`findings.md`](findings.md) §8 — V1 amendment summary
4. [`evaluation_framework.md`](evaluation_framework.md) §7 — reporting
   format

**Rule:** if a sentence in a V2 paper subsection states a number, it
must appear in `reports/v2_falsification.md`. If it states a claim, it
must appear in `problem_framing.md` or `falsification_plan.md` §3.

---

## All V2 Documents

| Document | Purpose |
|---|---|
| [`problem_framing.md`](problem_framing.md) | V2 charter — what V2 tests and why |
| [`falsification_plan.md`](falsification_plan.md) | The six hypotheses, cheapest tests, kill criteria, and Phase A results |
| [`evaluation_framework.md`](evaluation_framework.md) | Metric definitions and per-hypothesis evaluation framework |
| [`stop_criteria.md`](stop_criteria.md) | Phase gates, time-boxes, project-level stop |
| [`findings.md`](findings.md) | Consolidated Phase A numbers reference |
| [`documentation_map.md`](documentation_map.md) | V1→V2 document status |
| [`TODO.md`](TODO.md) | Open work for Phase A exit, Phase B, Phase D |
| [`protocols/decision_policy_capacity.md`](protocols/decision_policy_capacity.md) | Capacity-aware policy protocol (Phase B) |
| [`protocols/monitoring.md`](protocols/monitoring.md) | Drift detector protocol (Phase B) |
| [`cut_list.md`](cut_list.md) | What V2 does not do and why (Phase D) |
| [`architecture.md`](architecture.md) | V2 as-built (written after Phase B) |

---

## Reports (in `/reports/v2`)

| Report | Contents |
|---|---|
| [`../reports/v2_falsification.md`](../../reports/v2_falsification.md) | Phase A assembled report — one section per hypothesis |
| `../reports/v2/intermediate/h1_capacity.json` | H1 evidence |
| `../reports/v2/intermediate/h2_delay_2m.json` | H2 evidence |
| `../reports/v2/intermediate/h3_rolling_retrain.json` | H3 evidence |
| `../reports/v2/intermediate/h4_drift.json` | H4 evidence |
| `../reports/v2/intermediate/h4_importance_crossref.json` | H4 importance cross-reference |
| `../reports/v2/intermediate/h5_fairness.json` | H5 evidence |
| `../reports/v2/intermediate/h6_stratified_calibration.json` | H6 evidence |

---

## Document Status Key

- **inherited** — unchanged from V1; V2 does not re-derive it
- **extended** — V2 adds sections or fields without altering V1 text
- **superseded** — V2 work no longer reads it as a live source
- **amended** — a V1 claim is preserved with a dated conditions note

See [`documentation_map.md`](documentation_map.md) for the full status
of every V1 document under V2.

---

## What V2 Does Not Do

- No new hypotheses beyond H1–H6
- No new classifier search (V1's noise band is closed; H3 confirmed it)
- No new cost matrix
- No cost-sensitive training
- No calibration method comparison
- No fairness constraint build (H5 killed)
- No IPW or doubly robust estimation (Phase C skipped)
- No MLflow, DVC, Docker, CI/CD, or FastAPI
- No re-touching V1's frozen test window with new modeling

See [`cut_list.md`](cut_list.md) for the full list with reasons.

---

## Guiding Rules

> V1 asked whether a decision-centric framing beats a classification
> framing. V2 asks whether the decision-centric framing survives
> operational reality. These are different questions with different
> methods.

> Every V2 hypothesis has a cheapest test and a numeric kill criterion
> written before the test is run. No exceptions.

> A hypothesis that fails its kill criterion is reported as a
> non-finding and dropped from scope. Dropping a hypothesis is a
> legitimate outcome.

> Complexity is added only against a measured failure of the V1 system.
> The V1 system has no measured failure under V1 conditions. Every V2
> addition must be justified by its own measured failure under harder
> conditions.

> If V2 contradicts V1, V1 is amended. The V1 headline is not defended.