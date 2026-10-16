---
version: 1
slug: "app-streamlit-app-py"
primary_target: "app/streamlit_app.py"
related_targets: []
---

# Surface: Fraud Decision Desk (app/streamlit_app.py)

Mode: Operate. Audience: non-technical panel watching a live projector demo; presenter drives.
Job: show what the system decides for an application and why, in seconds.
Constraints: Streamlit 1.64; numbers must match docs/main.tex; no accuracy/production claims.

## Direction contract

THESIS: A teller's desk that stamps every application APPROVED, FOR REVIEW or BLOCKED and prints the reason beside the stamp. Refuses the dark ML dashboard of metric tiles and probability tables.

OWN-WORLD: Passbook-cover navy shell band with a fine guilloche line field; pale security-tint paper ground; white ruled sheets with hairline rules; amounts and percentages in teller-printed tabular mono; three stamp inks (green approve, ochre review, red block) used only for decisions; one blue action color only on pressable things.

STORY: Viewer sees an application, sees the stamp, reads one plain sentence of why, watches a bigger credit limit push the same application into review, then sees the study's 57.91% result.

FIRST VIEWPORT: Navy band with title and one-line promise. Standard tabs below. "Check one application": left column sample picker + credit-limit slider; right column the stamp at large scale, the risk-zone scale for this amount, and a ruled three-row cost slip with the cheapest row marked.

FORM: Bank passbook and teller validation stamp, position 6 of 7 on the grounded list. seed:f064024a51ad7a09. Raises: action color only on pressable things (warm consumer app); one result owns the right column (vertical feed); tabular numerals throughout (datamatics). Signature interaction: stamp press-in on decision change.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
