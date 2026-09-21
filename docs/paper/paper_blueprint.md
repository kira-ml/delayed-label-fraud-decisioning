# IEEE Paper Blueprint: Delayed-Label Fraud Decisioning

Maps the project to the IEEE term-paper format used in the course sample.
Every paper section points to the project doc that feeds it.

## Front Matter

### Title
Cost-Sensitive Fraud Decisioning Under Delayed and Censored Labels:
A Temporal Backtest on the Bank Account Fraud Dataset

### Authors
[Full name of each member] — alphabetical or by contribution, instructor's call.
College of Computing and Information Technologies
National University Philippines
Manila, Philippines
[email addresses]

### Abstract
See `abstract_and_index_terms.md`.

### Index Terms
See `abstract_and_index_terms.md`.

## Section Map

| IEEE Section | Project Source | Paper Draft |
|---|---|---|
| 1. Introduction | problem_framing.md §3-4 | introduction_draft.md |
| 2. Related Work | paper/related_work.md | to write |
| 3. Methodology | paper/methodology.md | to write |
| 4. Dataset & Preprocessing | data_card.md §2-5 | to write |
| 5. Experimental Setup | evaluation_protocol.md §7-9 | to write |
| 6. Results | paper/results_narrative.md | to write |
| 7. Discussion | paper/discussion_notes.md | to write |
| 8. Limitations | reports/mvp_backtest.md §Limitations | to write |
| 9. Conclusion & Future Work | roadmap.md §5-7 | to write |
| References | paper/references.md | to write |

## Structural Convention (matching the sample)

- Numbered headings: `1. INTRODUCTION`, `2. RELATED WORK`, etc.
- Subsections: `A. Subheading`, `B. Subheading` (roman caps)
- One-sentence paragraphs in the abstract — no bullet points
- Statistics cited with author-year or author-number throughout the intro
- No bullet lists in the body — the sample uses prose. Tables and figures only.
- 2-column layout (that's a LaTeX/Word setting, not content)

## What Makes This Paper Different From the Sample

The sample (fare calculator) is a **systems** paper: it introduces a tool.

Your paper is a **methodology + evaluation** paper: it introduces a way of
framing fraud detection, and it *measures* it. That means:

- Longer Methodology and Experimental Setup sections
- A dedicated Results section with tables and CIs
- A real Limitations section (the sample barely has one)
- Fewer "future work" promises, more "what we measured" claims

This is a strength. The sample paper's contribution is a calculator. Yours
is a demonstrated reduction in realized cost with measured uncertainty.

## Length Target

8–10 pages IEEE two-column. Section budget:

| Section | Pages |
|---|---|
| Abstract + Index Terms | 0.25 |
| 1. Introduction | 1.0 |
| 2. Related Work | 1.0 |
| 3. Methodology | 2.0 |
| 4. Dataset & Setup | 1.0 |
| 5. Results | 2.0 |
| 6. Discussion | 0.75 |
| 7. Limitations | 0.5 |
| 8. Conclusion | 0.5 |
| References | 0.5 |

## Reviewer Trap to Avoid

The sample claims "excellent accuracy" without a baseline. Do NOT do that.
Every claim in your results section must be anchored to a baseline and,
where possible, a confidence interval. This is what makes your paper
stronger than a typical student submission — the evaluation protocol
already forbids unanchored claims.