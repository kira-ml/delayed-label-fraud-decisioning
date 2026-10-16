"""Fraud Decision Desk: Streamlit app for the BAF cost-sensitive policy.

Loads the same model + preprocessing pipeline reported in the paper and
routes each application to approve / review / block by the argmin of
expected cost. Written for a non-technical audience first; technical
detail sits in expanders.

Run locally with:  streamlit run app/streamlit_app.py
"""
# --- Repo root path bootstrap ---
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _APP_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
# --------------------------------

import base64
import html
import json
import math
from urllib.parse import quote

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import joblib

from src.common import CATEGORICAL_COLS
from src.policy.decide import choose_actions, load_costs

MODELS = _REPO_ROOT / "models"
MODEL_PATH = MODELS / "best_model.pkl"
PREPROC_PATH = MODELS / "preprocessing.pkl"
FEATURES_PATH = MODELS / "feature_columns.json"
DEFAULTS_PATH = MODELS / "feature_defaults.json"
IMPORTANCES_PATH = MODELS / "feature_importances.json"
COSTS_PATH = _REPO_ROOT / "configs" / "costs.yaml"
CV_RESULTS_PATH = _REPO_ROOT / "reports" / "cv_results.json"
SAMPLE_BATCH_PATH = _REPO_ROOT / "sample_500.csv"
FONTS_DIR = _APP_DIR / "static" / "fonts"

ACTION_ORDER = ["approve", "review", "block"]
STAMP_TEXT = {"approve": "APPROVED", "review": "FOR REVIEW", "block": "BLOCKED"}
ACTION_PLAIN = {
    "approve": "Let it through",
    "review": "Send for a manual check",
    "block": "Block it",
}

# Training-window fraud rate (docs/data_card.md §2.1). Used only for the
# out-of-distribution note on batch uploads.
TRAIN_FRAUD_RATE = 0.0103

# Three real rows from sample_500.csv used as one-click demo examples.
# Row indices were chosen so the demo shows each decision reliably.
PRESETS = {
    "Everyday": {
        "row": 6,
        "blurb": "A typical application with a low fraud risk.",
    },
    "Unusual": {
        "row": 17,
        "limit": 200,
        "blurb": "Some warning signs. Watch what a bigger credit limit does.",
    },
    "Suspicious": {
        "row": 295,
        "blurb": "Strong warning signs. In the synthetic dataset, this one is labelled fraud.",
    },
}

# Paper results (docs/main.tex, reports/decision_backtest.md,
# reports/bootstrap.md, reports/sensitivity.md). Do not edit without
# re-running the pipeline.
BASELINE_COSTS = [
    ("Block everyone", 0.098742),
    ("Random decisions", 0.047484),
    ("Approve everyone", 0.018928),
    ("Random Forest + 50% cut-off", 0.018928),
    ("Logistic Regression + 50% cut-off", 0.018737),
    ("LightGBM + 50% cut-off (best simple rule)", 0.017798),
    ("Decision desk (cost-based)", 0.007491),
]
SENSITIVITY = [
    ("As planned", 0.007491, 57.91),
    ("Wrongly blocking costs half as much", 0.007037, 60.36),
    ("Wrongly blocking costs twice as much", 0.007625, 57.38),
    ("Manual checks cost half as much", 0.006253, 64.87),
    ("Manual checks cost twice as much", 0.009298, 47.76),
    ("Checks catch more of the loss", 0.006588, 62.99),
    ("Checks catch less of the loss", 0.008700, 51.12),
]

# ---------------------------------------------------------------------------
# Palette: passbook cover, security-tint paper, stamp inks, one action blue.
# ---------------------------------------------------------------------------
PALETTE = {
    "cover":        "#13294B",
    "cover_deep":   "#0C1C36",
    "cover_ink":    "#EEF2F8",
    "cover_muted":  "#AFC0DA",
    "paper":        "#F3F5EF",
    "sheet":        "#FFFFFF",
    "rule":         "#D6DBD0",
    "rule_strong":  "#B9C0B3",
    "ink":          "#1B2430",
    "ink_muted":    "#3E4752",
    "action":       "#1F55D6",
    "action_hover": "#1746B4",
    "neutral_bar":  "#B8C0C9",
    "approve":      "#1E7A46",
    "approve_tint": "#E6F2EA",
    "review":       "#A8660F",
    "review_tint":  "#F8EEDC",
    "block":        "#B42318",
    "block_tint":   "#FBE9E7",
}
UI_FONT = "'Public Sans', 'Segoe UI', system-ui, sans-serif"
NUM_FONT = "'JetBrains Mono', 'Consolas', ui-monospace, monospace"
STAMP_FONT = "'Barlow Condensed', 'Arial Narrow', sans-serif"


# ============================================================
# Pure functions
# ============================================================
def validate_input(df: pd.DataFrame, required: list[str]) -> list[str]:
    errors: list[str] = []
    if df is None or df.empty:
        return ["Input contains no rows."]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    for c in CATEGORICAL_COLS:
        if c in df.columns and df[c].isna().any():
            errors.append(f"Categorical column '{c}' contains missing values.")
    if "customer_age" in df.columns:
        bad = df[(df["customer_age"] < 0) | (df["customer_age"] > 120)]
        if len(bad):
            errors.append(f"{len(bad)} rows have customer_age outside [0, 120].")
    return errors


def predict(model, pre, X: pd.DataFrame):
    X_t = pre.transform(X)
    if hasattr(X_t, "toarray"):
        X_t = X_t.toarray()
    preds = model.predict(X_t)
    proba = (
        model.predict_proba(X_t)[:, 1]
        if hasattr(model, "predict_proba")
        else np.full(len(X_t), np.nan)
    )
    return preds, proba


def route_actions(p, amounts, costs_override: dict | None = None) -> dict:
    """Apply the argmin-expected-cost policy and return everything the UI needs.

    Returns a dict with actions, per-row expected costs for all three
    actions, chosen cost, expected savings vs. approve-all, and the
    derived policy thresholds.
    """
    costs = dict(load_costs(COSTS_PATH))
    if costs_override:
        costs.update(costs_override)

    p = np.asarray(p, dtype=float)
    n = len(p)

    if costs.get("amount_scaled", False) and amounts is not None:
        amounts = np.asarray(amounts, dtype=float)
        fraud_loss = amounts * float(costs["fraud_loss_rate"])
    else:
        fraud_loss = np.full(n, float(costs["fraud_loss"]))

    c_app = p * fraud_loss
    c_rev = float(costs["review_cost"]) + p * float(costs["residual_fraud_loss"])
    c_blk = (1.0 - p) * float(costs["false_positive_cost"])

    actions, chosen_cost, _ = choose_actions(p, costs, amounts)
    expected_savings = c_app - chosen_cost

    # Derived thresholds (diagnostic; argmin is the source of truth).
    fl_const = float(costs["fraud_loss"])
    rfl = float(costs["residual_fraud_loss"])
    rc = float(costs["review_cost"])
    fpc = float(costs["false_positive_cost"])
    denom_rev = fl_const - rfl
    p_review = (rc / denom_rev) if denom_rev > 0 else float("nan")
    denom_blk = fpc + rfl
    p_block = ((fpc - rc) / denom_blk) if denom_blk > 0 else float("nan")

    return {
        "actions": actions,
        "chosen_cost": chosen_cost,
        "expected_cost_approve": c_app,
        "expected_cost_review":  c_rev,
        "expected_cost_block":   c_blk,
        "expected_savings": expected_savings,
        "costs": costs,
        "p_review": p_review,
        "p_block": p_block,
    }


def decision_zones(amount: float, costs_override: dict | None,
                   resolution: int = 4001) -> list[tuple[str, float, float]]:
    """Risk ranges that map to each action for one credit limit.

    Evaluates the same argmin policy over a grid of probabilities, so the
    zones always agree with the decision the app shows.
    """
    grid = np.linspace(0.0, 1.0, resolution)
    actions = route_actions(grid, np.full(resolution, amount), costs_override)["actions"]
    zones: list[tuple[str, float, float]] = []
    start = 0
    for i in range(1, resolution + 1):
        if i == resolution or actions[i] != actions[start]:
            zones.append((str(actions[start]), float(grid[start]), float(grid[i - 1])))
            start = i
    return zones


def next_switch_amount(p: float, amount: float, costs_override: dict | None,
                       upper: float = 5000.0) -> tuple[float, str] | None:
    """Smallest credit limit above `amount` where the same risk changes action."""
    amounts = np.arange(math.floor(amount / 10) * 10 + 10, upper + 10, 10.0)
    if len(amounts) == 0:
        return None
    current = route_actions([p], [amount], costs_override)["actions"][0]
    acts = route_actions(np.full(len(amounts), p), amounts, costs_override)["actions"]
    changed = np.where(acts != current)[0]
    if len(changed) == 0:
        return None
    i = int(changed[0])
    return float(amounts[i]), str(acts[i])


def fmt_pct(p: float) -> str:
    return f"{p * 100:.1f}%" if p >= 0.001 else "<0.1%"


def fmt_amount(x: float) -> str:
    return f"{x:,.0f}"


# ============================================================
# Artifact loading
# ============================================================
@st.cache_resource(show_spinner=False)
def load_artifacts():
    for p in (MODEL_PATH, PREPROC_PATH, FEATURES_PATH):
        if not p.exists():
            st.error(
                f"Missing artifact: `{p}`.\n\nRun: `python -m src.pipeline`"
            )
            st.stop()
    model = joblib.load(MODEL_PATH)
    pre = joblib.load(PREPROC_PATH)
    features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
    defaults = (
        json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))
        if DEFAULTS_PATH.exists() else {}
    )
    importances = (
        json.loads(IMPORTANCES_PATH.read_text(encoding="utf-8"))
        if IMPORTANCES_PATH.exists() else None
    )
    cv_results = (
        json.loads(CV_RESULTS_PATH.read_text(encoding="utf-8"))
        if CV_RESULTS_PATH.exists() else None
    )
    return model, pre, features, defaults, importances, cv_results


@st.cache_data(show_spinner=False)
def _read_sample_batch(mtime: float) -> pd.DataFrame:
    # mtime is part of the cache key, so a replaced file is re-read.
    return pd.read_csv(SAMPLE_BATCH_PATH)


def load_sample_batch() -> pd.DataFrame | None:
    # Check existence outside the cache so a missing file is never cached:
    # once it is deployed, the next rerun picks it up.
    if not SAMPLE_BATCH_PATH.exists():
        return None
    return _read_sample_batch(SAMPLE_BATCH_PATH.stat().st_mtime)


# ============================================================
# Styling
# ============================================================
def guilloche_uri() -> str:
    """Security-print line field for the header band, as an SVG data URI."""
    w, h = 1200, 140
    paths = []
    for k in range(9):
        amp = 18 + 3 * k
        phase = k * 0.55
        freq = 2 * math.pi / (260 + 14 * k)
        pts = [
            f"{x},{h / 2 + amp * math.sin(freq * x + phase):.1f}"
            for x in range(0, w + 1, 12)
        ]
        paths.append(
            f"<polyline points='{' '.join(pts)}' fill='none' "
            f"stroke='white' stroke-opacity='0.11' stroke-width='1.2'/>"
        )
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}'>{''.join(paths)}</svg>"
    )
    return "data:image/svg+xml;utf8," + quote(svg)


@st.cache_data(show_spinner=False)
def font_face_css() -> str:
    """Self-hosted @font-face rules (base64), so the demo works offline."""
    fonts = [
        ("Public Sans", "PublicSans-var.woff2", "100 900"),
        ("JetBrains Mono", "JetBrainsMono-var.woff2", "100 800"),
        ("Barlow Condensed", "BarlowCondensed-700.woff2", "700"),
    ]
    rules = []
    for family, fname, weight in fonts:
        path = FONTS_DIR / fname
        if not path.exists():
            continue
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f"@font-face {{ font-family: '{family}'; font-weight: {weight}; "
            f"font-style: normal; font-display: swap; "
            f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}"
        )
    return "\n".join(rules)


def inject_css() -> None:
    P = PALETTE
    st.html(
        f"""
<style>
{font_face_css()}

:root {{ color-scheme: light; }}
.stApp {{ background: {P["paper"]}; color: {P["ink"]}; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] {{
  font-family: {UI_FONT};
}}
.stApp [data-testid="stIconMaterial"] {{ font-family: "Material Symbols Rounded" !important; }}
::selection {{ background: {P["action"]}; color: #fff; }}
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"], .main .block-container {{
  padding-top: 1.2rem; padding-bottom: 4rem; max-width: 1240px;
}}
.stApp h2 {{ font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em; color: {P["ink"]}; margin: 0.4rem 0 0.25rem; }}
.stApp h3 {{ font-size: 1.12rem; font-weight: 700; letter-spacing: -0.01em; color: {P["ink"]}; margin: 1.6rem 0 0.35rem; }}
.stApp p, .stApp li {{ font-size: 1.02rem; line-height: 1.55; }}
.muted {{ color: {P["ink_muted"]}; }}
.num {{ font-family: {NUM_FONT}; font-variant-numeric: tabular-nums; }}

/* ---- Header band: passbook cover ---- */
.desk-band {{
  background:
    linear-gradient(90deg, {P["cover"]} 0%, {P["cover"]} 52%, rgba(19, 41, 75, 0) 82%),
    {P["cover"]} url("{guilloche_uri()}") center / cover no-repeat;
  color: {P["cover_ink"]};
  border-radius: 14px;
  padding: 1.1rem 1.8rem;
  margin-bottom: 0.2rem;
  box-shadow: 0 6px 18px rgba(12, 28, 54, 0.18);
  display: flex; justify-content: space-between; align-items: center; gap: 1.2rem;
  flex-wrap: wrap;
}}
.desk-band h1 {{
  font-family: {UI_FONT}; font-size: 1.9rem; font-weight: 700;
  letter-spacing: -0.025em; margin: 0; padding: 0; color: {P["cover_ink"]}; line-height: 1.1;
}}
.desk-band p {{ margin: 0.3rem 0 0; color: {P["cover_muted"]}; font-size: 1.05rem; max-width: 70ch; }}
.stApp [data-testid="stCaptionContainer"] {{ opacity: 1 !important; }}
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * {{ color: {P["ink_muted"]} !important; font-size: 0.98rem; }}
.st-key-preset button {{ flex: 1 1 0; min-width: 0; }}
@media (max-width: 420px) {{
  .st-key-preset button {{ padding-left: 0.3rem; padding-right: 0.3rem; }}
  .st-key-preset button p {{ font-size: 0.92rem; }}
}}
.desk-band .legend {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
.desk-band .legend span {{
  font-family: {STAMP_FONT}; font-weight: 700; letter-spacing: 0.08em; font-size: 0.95rem;
  padding: 0.2rem 0.6rem; border-radius: 4px; border: 1.5px solid currentColor;
  background: rgba(255,255,255,0.94);
}}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{ gap: 0.25rem; border-bottom: 1px solid {P["rule_strong"]}; }}
.stTabs button[data-baseweb="tab"] {{ padding: 0.7rem 1rem; }}
.stTabs button[data-baseweb="tab"] p {{ font-size: 1.02rem; font-weight: 600; color: {P["ink_muted"]}; }}
.stTabs button[data-baseweb="tab"][aria-selected="true"] p {{ color: {P["ink"]}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {P["cover"]}; height: 3px; }}
.stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* ---- Sheets: ruled white work surfaces ---- */
.st-key-sheet-left, .st-key-sheet-right, .st-key-batch-sheet {{
  background: {P["sheet"]}; border: 1px solid {P["rule"]}; border-radius: 14px;
  padding: 1.2rem 1.4rem 1.3rem;
}}
.step-label {{
  font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  color: {P["ink_muted"]}; margin: 0.2rem 0 0.35rem;
}}

/* ---- Controls ---- */
.stButton > button, .stDownloadButton > button {{
  border-radius: 8px; font-weight: 600; border: 1px solid {P["rule_strong"]};
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: {P["action"]}; border-color: {P["action"]}; color: #fff;
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
  background: {P["action_hover"]}; border-color: {P["action_hover"]};
}}
.stApp :focus-visible {{ outline: 2px solid {P["action"]}; outline-offset: 2px; }}
[data-testid="stExpander"] details {{ border: 1px solid {P["rule"]}; border-radius: 10px; background: {P["sheet"]}; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}
[data-testid="stDataFrame"] {{ border: 1px solid {P["rule"]}; border-radius: 10px; overflow: hidden; }}
[data-testid="stFileUploaderDropzone"] {{ background: {P["paper"]}; border: 1.5px dashed {P["rule_strong"]}; }}

/* ---- The stamp (signature) ---- */
.stamp-wrap {{ display: flex; align-items: center; gap: 1.4rem; flex-wrap: wrap; margin: 0.2rem 0 0.6rem; }}
.stamp {{
  display: inline-flex; flex-direction: column; align-items: center;
  padding: 0.55rem 1.3rem 0.45rem; border: 4px double currentColor; border-radius: 10px;
  transform: rotate(-5deg); animation: stamp-press 420ms cubic-bezier(.2,.9,.25,1) both;
  background: rgba(255,255,255,0.6);
}}
.stamp .word {{ font-family: {STAMP_FONT}; font-weight: 700; font-size: 2.6rem; letter-spacing: 0.08em; line-height: 1; }}
.stamp .date {{ font-family: {NUM_FONT}; font-size: 0.78rem; letter-spacing: 0.12em; margin-top: 0.2rem; opacity: 0.9; }}
.ink-approve {{ color: {P["approve"]}; }}
.ink-review  {{ color: {P["review"]}; }}
.ink-block   {{ color: {P["block"]}; }}
@keyframes stamp-press {{
  0%   {{ transform: rotate(-5deg) scale(1.35); opacity: 0; filter: blur(2px); }}
  70%  {{ transform: rotate(-5deg) scale(0.97); opacity: 1; filter: blur(0); }}
  100% {{ transform: rotate(-5deg) scale(1); }}
}}
@media (prefers-reduced-motion: reduce) {{ .stamp {{ animation: none; }} }}
.stamp-meta .id {{ font-size: 0.85rem; color: {P["ink_muted"]}; }}
.stamp-meta .say {{ font-size: 1.25rem; font-weight: 700; color: {P["ink"]}; margin-top: 0.15rem; }}
.why {{ font-size: 1.06rem; line-height: 1.55; color: {P["ink"]}; max-width: 62ch; margin: 0.3rem 0 0.2rem; }}

/* ---- Risk zone scale ---- */
.scale {{ position: relative; margin: 0.2rem 0 0.2rem; padding-top: 1.7rem; }}
.scale .pin {{ position: absolute; top: 0; font-size: 0.88rem; color: {P["ink"]}; white-space: nowrap; }}
.scale .bar {{ position: relative; display: flex; height: 32px; border-radius: 6px; gap: 2px; background: {P["sheet"]}; }}
.scale .zone {{ height: 100%; }}
.scale .names {{ display: flex; gap: 2px; margin-top: 0.4rem; }}
.scale .zone-note {{ margin-top: 0.3rem; font-size: 0.92rem; color: {P["ink_muted"]}; }}
.scale .zone-note span {{ font-weight: 700; }}
.scale .names div {{ text-align: center; font-size: 0.88rem; font-weight: 700; white-space: nowrap; overflow: hidden; }}
.scale .zone:first-child {{ border-radius: 6px 0 0 6px; }}
.scale .zone:last-of-type {{ border-radius: 0 6px 6px 0; }}
.zone-approve {{ background: {P["approve_tint"]}; color: {P["approve"]}; }}
.zone-review  {{ background: {P["review_tint"]};  color: {P["review"]}; }}
.zone-block   {{ background: {P["block_tint"]};   color: {P["block"]}; }}
.scale .marker {{ position: absolute; top: -6px; bottom: -6px; width: 3px; background: {P["ink"]}; border-radius: 2px;
  box-shadow: 0 0 0 2px {P["sheet"]}; }}
.scale .ticks {{ position: relative; height: 1.3rem; margin-top: 0.35rem; font-size: 0.95rem; color: {P["ink_muted"]};
  font-family: {NUM_FONT}; }}
.scale .ticks span {{ position: absolute; transform: translateX(-50%); }}
.scale .ticks span:first-child {{ transform: none; }}
.scale .ticks span:last-child {{ transform: translateX(-100%); }}
.st-key-sheet-right h3 {{ margin-top: 0.6rem; }}
.st-key-sheet-right [data-testid="stVerticalBlock"] {{ gap: 0.55rem; }}

/* ---- Cost slip: ruled ledger rows ---- */
.slip {{ width: 100%; border-collapse: collapse; margin-top: 0.4rem; }}
.slip td {{ padding: 0.55rem 0.4rem; border-top: 1px solid {P["rule"]}; vertical-align: middle; }}
.slip tr:last-child td {{ border-bottom: 1px solid {P["rule"]}; }}
.slip .opt {{ font-weight: 600; width: 38%; }}
.slip .val {{ text-align: right; width: 16%; font-family: {NUM_FONT}; font-variant-numeric: tabular-nums; }}
.slip .trk {{ width: 34%; }}
.slip .trk div {{ height: 8px; border-radius: 0 4px 4px 0; background: {P["neutral_bar"]}; min-width: 2px; }}
.slip .tag {{ width: 12%; text-align: right; font-family: {STAMP_FONT}; font-weight: 700; letter-spacing: 0.06em; font-size: 0.95rem; }}
.slip tr.win .opt {{ color: {P["ink"]}; }}
.slip tr:not(.win) .opt, .slip tr:not(.win) .val {{ color: {P["ink_muted"]}; }}

/* ---- Batch mix bar ---- */
.mix {{ display: flex; height: 34px; gap: 2px; border-radius: 6px; overflow: hidden; margin: 0.6rem 0 0.5rem; }}
.mix div {{ min-width: 6px; }}
.mix-legend {{ display: flex; gap: 1.4rem; flex-wrap: wrap; font-size: 0.98rem; }}
.mix-legend .sw {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 0.45rem; vertical-align: -1px; }}

/* ---- Ledger of totals ---- */
.ledger {{ width: 100%; max-width: 640px; border-collapse: collapse; margin: 0.5rem 0 0.3rem; font-size: 1.02rem; }}
.ledger td, .ledger th {{ padding: 0.55rem 0.4rem; border-top: 1px solid {P["rule"]}; text-align: left; }}
.ledger th {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: {P["ink_muted"]}; border-top: none; }}
.ledger td.n, .ledger.sum td:last-child {{ text-align: right; font-family: {NUM_FONT}; font-variant-numeric: tabular-nums; }}
.ledger th.n {{ text-align: right; }}
.ledger tr:last-child td {{ border-bottom: 1px solid {P["rule"]}; }}
.ledger tr.total td {{ border-top: 2px solid {P["ink"]}; font-weight: 700; }}
.ledger tr.hl td {{ font-weight: 700; }}
.ledger.wide {{ max-width: 100%; }}

/* ---- Results headline ---- */
.headline {{ font-size: 2.4rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; margin: 0.4rem 0 0.4rem; color: {P["ink"]}; }}
.headline .num {{ color: {P["cover"]}; font-family: {UI_FONT}; }}
.steps {{ width: 100%; border-collapse: collapse; margin: 0.6rem 0 0.4rem; background: {P["sheet"]}; border-radius: 12px; overflow: hidden; }}
.steps td {{ padding: 0.8rem 1rem; border-top: 1px solid {P["rule"]}; vertical-align: top; font-size: 1.02rem; }}
.steps tr:first-child td {{ border-top: none; }}
.steps td.k {{ width: 3rem; font-family: {NUM_FONT}; font-weight: 600; color: {P["cover"]}; font-size: 1.1rem; }}
.steps td.t {{ width: 30%; font-weight: 700; color: {P["cover"]}; }}
.steps td.d {{ color: {P["ink_muted"]}; }}
@media (max-width: 760px) {{
  [data-testid="stMainBlockContainer"], .main .block-container {{ padding-top: 3.4rem; }}
  .steps td.t {{ width: auto; }}
  .desk-band {{ padding: 1.2rem 1.1rem; }}
  .desk-band h1 {{ font-size: 1.6rem; }}
  .stamp .word {{ font-size: 2rem; }}
  .headline {{ font-size: 1.8rem; }}
}}
</style>
"""
    )


def altair_theme() -> None:
    def _theme():
        return {
            "config": {
                "background": "transparent",
                "font": "Public Sans",
                "view": {"stroke": None},
                "axis": {
                    "labelColor": PALETTE["ink_muted"], "titleColor": PALETTE["ink_muted"],
                    "gridColor": PALETTE["rule"], "domainColor": PALETTE["rule_strong"],
                    "tickColor": PALETTE["rule_strong"], "labelFontSize": 13, "titleFontSize": 12,
                    "titleFontWeight": 600,
                },
            }
        }
    if hasattr(alt, "theme"):  # Altair >= 5.5
        alt.theme.register("desk", enable=True)(_theme)
    else:
        alt.themes.register("desk", _theme)
        alt.themes.enable("desk")


# ============================================================
# Shared fragments
# ============================================================
def header_band() -> None:
    st.html(
        f"""
<div class="desk-band">
  <div>
    <h1>Fraud Decision Desk</h1>
    <p>Approve, review or block each application now, before the fraud report arrives.</p>
  </div>
  <div class="legend">
    <span class="ink-approve">APPROVED</span>
    <span class="ink-review">FOR REVIEW</span>
    <span class="ink-block">BLOCKED</span>
  </div>
</div>
"""
    )


def stamp_html(action: str) -> str:
    """The stamp alone. Its markup depends only on the action and the date,
    so Streamlit keeps the same DOM (and skips the press animation) until the
    decision itself changes."""
    today = pd.Timestamp.today().strftime("%d %b %Y").upper()
    return f"""
<div class="stamp-wrap">
  <div class="stamp ink-{action}" role="img" aria-label="Decision: {STAMP_TEXT[action]}">
    <span class="word">{STAMP_TEXT[action]}</span>
    <span class="date">{today}</span>
  </div>
</div>
"""


def stamp_meta_html(caption: str, headline: str) -> str:
    return f"""
<div class="stamp-meta">
  <div class="id">{html.escape(caption)}</div>
  <div class="say">{html.escape(headline)}</div>
</div>
"""


def risk_scale_html(p: float, zones: list[tuple[str, float, float]]) -> str:
    axis_max = 0.4 if p <= 0.36 else min(1.0, math.ceil(p * 1.15 * 10) / 10)
    segs, names, unnamed = [], [], []
    for action, lo, hi in zones:
        lo_c, hi_c = min(lo, axis_max), min(hi, axis_max)
        width = (hi_c - lo_c) / axis_max * 100
        if width <= 0:
            continue
        label = {"approve": "Let through", "review": "Check", "block": "Block"}[action]
        flex = f"flex: 0 0 calc({width:.3f}% - 2px)"
        segs.append(
            f'<div class="zone zone-{action}" style="{flex}" '
            f'title="{label}: {fmt_pct(lo)} to {fmt_pct(hi)}"></div>'
        )
        names.append(
            f'<div class="ink-{action}" style="{flex}">{label if width > 8 else ""}</div>'
        )
        if width <= 8:  # too narrow to label in place; name it below instead
            span = (f"below {fmt_pct(hi)}" if lo == 0 else
                    f"above {fmt_pct(lo)}" if hi >= 1 else
                    f"{fmt_pct(lo)} to {fmt_pct(hi)}")
            unnamed.append(f'<span class="ink-{action}">{label}</span> {span}')
    pos = min(p, axis_max) / axis_max * 100
    n_ticks = 5
    ticks = "".join(
        f'<span style="left:{i / (n_ticks - 1) * 100:.1f}%">'
        f'{axis_max * i / (n_ticks - 1) * 100:.0f}%</span>'
        for i in range(n_ticks)
    )
    # Anchor the label to the marker, flipping sides near the edges.
    if pos < 25:
        label_style = f"left: {pos:.2f}%; transform: translateX(-6px)"
    elif pos > 75:
        label_style = f"left: {pos:.2f}%; transform: translateX(calc(-100% + 6px))"
    else:
        label_style = f"left: {pos:.2f}%; transform: translateX(-50%)"
    return f"""
<div class="scale" aria-label="Fraud risk scale for this credit limit">
  <div class="pin" style="{label_style}">This application: <b class="num">{fmt_pct(p)}</b></div>
  <div class="bar">{''.join(segs)}
    <div class="marker" style="left: calc({pos:.2f}% - 1.5px)"></div>
  </div>
  <div class="names">{''.join(names)}</div>
  <div class="ticks">{ticks}</div>
  {f'<div class="zone-note">Narrow zone · {" · ".join(unnamed)}</div>' if unnamed else ''}
</div>
"""


def cost_slip_html(c_app: float, c_rev: float, c_blk: float, chosen: str) -> str:
    rows = [("approve", c_app), ("review", c_rev), ("block", c_blk)]
    top = max(c for _, c in rows) or 1.0
    out = []
    for action, c in rows:
        win = action == chosen
        bar_color = f"background:{PALETTE[action]};" if win else ""
        tag = f'<span class="ink-{action}">CHEAPEST</span>' if win else ""
        out.append(
            f'<tr class="{"win" if win else ""}">'
            f'<td class="opt">{ACTION_PLAIN[action]}</td>'
            f'<td class="trk"><div style="width:{c / top * 100:.1f}%;{bar_color}"></div></td>'
            f'<td class="val">{c:.4f}</td>'
            f'<td class="tag">{tag}</td></tr>'
        )
    return f'<table class="slip">{"".join(out)}</table>'


def why_sentence(action: str, p: float, amount: float) -> str:
    risk = fmt_pct(p)
    amt = fmt_amount(amount)
    if action == "approve":
        return (f"The fraud risk is {risk}. For a credit limit of {amt}, the expected "
                "loss from letting it through is smaller than the cost of checking "
                "or refusing it.")
    if action == "review":
        return (f"The fraud risk is {risk}. That is too high to ignore for a credit "
                f"limit of {amt}, but not high enough to turn the customer away. A "
                "manual check costs less than the possible loss.")
    return (f"The fraud risk is {risk}. Refusing now costs less than the likely "
            "loss, even after counting the chance of turning away a genuine customer.")


# ============================================================
# Sidebar: advanced cost settings
# ============================================================
def sidebar_settings() -> dict:
    base = load_costs(COSTS_PATH)
    with st.sidebar:
        st.markdown("### Cost settings")
        st.caption(
            "Advanced. These are the costs the desk weighs. The study froze "
            "them before any modelling; changing them here is a what-if only."
        )
        fpc = st.slider(
            "Cost of wrongly blocking a genuine customer",
            min_value=0.01, max_value=0.50,
            value=float(base["false_positive_cost"]), step=0.01,
            help="false_positive_cost",
        )
        rc = st.slider(
            "Cost of one manual check",
            min_value=0.001, max_value=0.10,
            value=float(base["review_cost"]), step=0.001, format="%.3f",
            help="review_cost",
        )
        rfl = st.slider(
            "Share of the loss still suffered after a check",
            min_value=0.05, max_value=0.90,
            value=float(base["residual_fraud_loss"]), step=0.05,
            help="residual_fraud_loss",
        )
        st.caption(
            "1 cost unit = the loss from one fraudulent application of average "
            "size (credit limit ≈ 521)."
        )
    return {
        "false_positive_cost": fpc,
        "review_cost": rc,
        "residual_fraud_loss": rfl,
    }


# ============================================================
# Tab 1: check one application
# ============================================================
def tab_single(features, model, pre, costs_override) -> None:
    sample = load_sample_batch()
    if sample is None:
        st.error("`sample_500.csv` is missing, so the example applications are unavailable.")
        return

    left, right = st.columns([5, 7], gap="large")

    with left.container(key="sheet-left"):
        st.html('<div class="step-label">1 · Pick an application</div>')
        choice = st.segmented_control(
            "Example application", list(PRESETS), default="Everyday",
            key="preset", label_visibility="collapsed", required=True,
            width="stretch",
        )
        preset = PRESETS[choice]
        base_row = sample.iloc[preset["row"]]
        st.caption(preset["blurb"])

        st.html('<div class="step-label" style="margin-top:1rem">2 · Set the requested credit limit</div>')
        amount = st.slider(
            "Requested credit limit", min_value=200, max_value=2500, step=50,
            value=int(preset.get("limit", base_row["proposed_credit_limit"])),
            key=f"limit-{choice}", label_visibility="collapsed",
        )
        st.caption("Drag it up. The fraud risk stays the same, but a bigger limit means a bigger possible loss.")

        row = base_row.to_dict()
        with st.expander("More application details"):
            st.caption("Category codes are anonymised in the dataset, so they appear as letter codes.")
            age = st.number_input(
                "Customer age", min_value=0, max_value=120, step=1,
                value=int(row["customer_age"]), key=f"age-{choice}",
            )
            row["customer_age"] = age
            c1, c2 = st.columns(2)
            for i, col in enumerate(CATEGORICAL_COLS):
                opts = sorted(sample[col].astype(str).unique())
                cur = str(row[col])
                if cur not in opts:
                    opts.append(cur)
                with (c1 if i % 2 == 0 else c2):
                    row[col] = st.selectbox(
                        col.replace("_", " ").capitalize(), opts,
                        index=opts.index(cur), key=f"{col}-{choice}",
                    )
        row["proposed_credit_limit"] = float(amount)

    df_row = pd.DataFrame([{k: row.get(k) for k in features}])
    errs = validate_input(df_row, features)
    with right.container(key="sheet-right"):
        if errs:
            for e in errs:
                st.error(e)
            return
        try:
            _, proba = predict(model, pre, df_row)
        except Exception as e:
            st.error(f"Scoring failed: {type(e).__name__}: {e}")
            return
        p = float(proba[0])
        routing = route_actions(proba, np.array([amount], dtype=float), costs_override)
        action = str(routing["actions"][0])

        c_stamp, c_meta = st.columns([6, 5], vertical_alignment="center", gap="small")
        with c_stamp:
            st.html(stamp_html(action))
        with c_meta:
            st.html(stamp_meta_html(
                f"Application #{int(row.get('transaction_id', preset['row']))} · "
                f"credit limit {fmt_amount(amount)}",
                ACTION_PLAIN[action],
            ))
        st.html(f'<p class="why">{html.escape(why_sentence(action, p, amount))}</p>')

        st.markdown("### Where this risk falls, for this credit limit")
        st.html(risk_scale_html(p, decision_zones(amount, costs_override)))
        switch = next_switch_amount(p, amount, costs_override)
        if switch:
            amt_s, act_s = switch
            verb = {"approve": "approved", "review": "sent for review", "block": "blocked"}[act_s]
            st.caption(
                f"Same risk, bigger limit: above about {fmt_amount(amt_s)}, this "
                f"application would be {verb}."
            )

        st.markdown("### Expected loss of each option")
        st.html(cost_slip_html(
            float(routing["expected_cost_approve"][0]),
            float(routing["expected_cost_review"][0]),
            float(routing["expected_cost_block"][0]),
            action,
        ))
        st.caption("In cost units. The desk always picks the cheapest row.")


# ============================================================
# Tab 2: check a batch
# ============================================================
def tab_batch(features, model, pre, costs_override) -> None:
    st.markdown("## Check many applications at once")
    c1, c2 = st.columns([3, 2], gap="large", vertical_alignment="bottom")
    with c1:
        uploaded = st.file_uploader(
            "Upload a CSV in the format of the study's synthetic Bank Account Fraud data",
            type=["csv"],
        )
    with c2:
        if st.button("Use the 500-application sample", type="primary", width="stretch"):
            st.session_state["use_sample"] = True
        st.caption("A slice of the test months, with known outcomes.")

    df = None
    source = ""
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            source = f"from {uploaded.name}"
        except Exception as e:
            st.error(f"Could not read that file as a CSV: {e}")
            return
    elif st.session_state.get("use_sample"):
        df = load_sample_batch()
        source = "sample"
    if df is None:
        st.info("Upload a file or use the sample to see the decisions.")
        return

    df = df.copy()
    if "amount_proxy" not in df.columns and "proposed_credit_limit" in df.columns:
        df["amount_proxy"] = df["proposed_credit_limit"].astype(float)
    errs = validate_input(df, features)
    if errs:
        st.error("This file can't be scored yet. Fix these and upload again:")
        for e in errs:
            st.error(e)
        return

    with st.spinner("Scoring applications..."):
        preds, proba = predict(model, pre, df[features])
        amt = df["amount_proxy"].values if "amount_proxy" in df.columns else None
        routing = route_actions(proba, amt, costs_override)

    actions = routing["actions"]
    counts = pd.Series(actions).value_counts().reindex(ACTION_ORDER, fill_value=0)
    n = len(df)

    title = (f"{n:,} sample applications checked" if source == "sample"
             else f"{n:,} applications checked {source}")
    st.markdown(f"### {title}")
    mix = "".join(
        f'<div style="flex:{max(counts[a], 0.0001)}; background:{PALETTE[a]}" '
        f'title="{STAMP_TEXT[a]}: {counts[a]:,}"></div>'
        for a in ACTION_ORDER if counts[a] > 0
    )
    legend = "".join(
        f'<span><span class="sw" style="background:{PALETTE[a]}"></span>'
        f'<b>{STAMP_TEXT[a].capitalize()}</b> <span class="num">{counts[a]:,}</span> '
        f'<span class="muted">({counts[a] / n:.1%})</span></span>'
        for a in ACTION_ORDER
    )
    st.html(f'<div class="mix">{mix}</div><div class="mix-legend">{legend}</div>')

    approve_all = float(routing["expected_cost_approve"].sum())
    policy = float(routing["chosen_cost"].sum())
    saved = approve_all - policy
    pct = saved / approve_all if approve_all else 0.0
    st.markdown("### Expected loss on this batch (model estimate)")
    st.html(
        f"""
<table class="ledger sum">
  <tr><td>If we simply approved everyone</td><td>{approve_all:,.2f}</td></tr>
  <tr><td>With the decision desk</td><td>{policy:,.2f}</td></tr>
  <tr class="total"><td>Estimated saving vs approving everyone</td><td>{saved:,.2f} &nbsp;({pct:.1%})</td></tr>
</table>
"""
    )
    st.caption(
        "Estimated by the model, in cost units. The study's measured result, on "
        "the recorded outcomes of the synthetic test months, is on the Study results tab."
    )
    mean_p = float(np.mean(proba))
    if mean_p > 3 * TRAIN_FRAUD_RATE:
        st.warning(
            f"This batch looks riskier than the data the model learned from "
            f"(average risk {fmt_pct(mean_p)} vs about {fmt_pct(TRAIN_FRAUD_RATE)}). "
            "Treat the scores with caution."
        )

    st.markdown("### Worklist: the applications that matter most")
    out = df.copy()
    out["fraud_risk"] = proba
    out["decision"] = [STAMP_TEXT[a] for a in actions]
    out["expected_saving"] = routing["expected_savings"]
    out["expected_cost_approve"] = routing["expected_cost_approve"]
    out["expected_cost_review"] = routing["expected_cost_review"]
    out["expected_cost_block"] = routing["expected_cost_block"]
    out["chosen_expected_cost"] = routing["chosen_cost"]
    out["prediction"] = preds
    out = out.sort_values("expected_saving", ascending=False).reset_index(drop=True)
    out["rank"] = out.index + 1

    view_cols = ["rank", "transaction_id", "decision", "fraud_risk",
                 "proposed_credit_limit", "expected_saving"]
    view_cols = [c for c in view_cols if c in out.columns]
    ink = {v: PALETTE[k] for k, v in STAMP_TEXT.items()}
    styled = (
        out[view_cols].head(50).style
        .map(lambda v: f"color: {ink.get(v, PALETTE['ink'])}; font-weight: 700",
             subset=["decision"])
        .format({"fraud_risk": "{:.1%}", "expected_saving": "{:.4f}",
                 "proposed_credit_limit": "{:,.0f}"})
    )
    st.dataframe(
        styled, hide_index=True, width="stretch",
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "transaction_id": st.column_config.NumberColumn("Application ID", format="%d"),
            "decision": "Decision",
            "fraud_risk": "Fraud risk",
            "proposed_credit_limit": "Credit limit",
            "expected_saving": st.column_config.NumberColumn(
                "Saving vs approving", help="Expected cost units saved by this decision."),
        },
    )
    st.caption("Sorted by how much each decision is expected to save. Top 50 shown.")
    st.download_button(
        "Download all decisions (CSV)",
        out.to_csv(index=False).encode("utf-8"),
        "decisions.csv", "text/csv",
    )

    with st.expander("Analyst tools: review capacity and segments"):
        review_capacity_panel(routing, n)
        segment_breakdown(df, proba, actions)


def review_capacity_panel(routing, n: int) -> None:
    st.markdown("#### If the team can only check K applications")
    savings = routing["expected_savings"]
    total_savings = float(np.sum(np.clip(savings, 0, None)))
    k = st.slider(
        "Applications the team can act on",
        min_value=1, max_value=max(1, n),
        value=min(max(1, int(0.02 * n)), n),
        step=max(1, n // 100),
    )
    top = np.argsort(-savings)[:k]
    covered = float(np.sum(np.clip(savings[top], 0, None)))
    cov_pct = covered / total_savings if total_savings else 0.0
    st.markdown(
        f"Acting on the top **{k:,}** captures **{cov_pct:.1%}** of the total "
        f"expected saving ({covered:,.2f} of {total_savings:,.2f} cost units)."
    )
    st.caption(
        "A ranking view, not a re-decision. See `docs/evaluation_protocol.md` §10."
    )


def segment_breakdown(df, proba, actions) -> None:
    cats_present = [c for c in CATEGORICAL_COLS if c in df.columns]
    if not cats_present:
        return
    st.markdown("#### Decisions by segment")
    seg = st.selectbox("Group by", cats_present, key="seg_col")
    tmp = pd.DataFrame({
        "segment": df[seg].astype(str).values,
        "p_fraud": proba,
        "action": actions,
    })
    grouped = tmp.groupby("segment").agg(rows=("p_fraud", "size"),
                                         mean_p=("p_fraud", "mean"))
    action_mix = (
        tmp.groupby(["segment", "action"]).size().unstack(fill_value=0)
        .reindex(columns=ACTION_ORDER, fill_value=0)
    )
    table = grouped.join(action_mix).sort_values("mean_p", ascending=False)
    table.columns = ["Applications", "Average risk", "Approved", "For review", "Blocked"]
    st.dataframe(
        table.style.format({"Average risk": "{:.2%}", "Applications": "{:,.0f}"}),
        width="stretch",
    )


# ============================================================
# Tab 3: how it decides
# ============================================================
def tab_how(model, features, importances, cv_results, costs_override) -> None:
    st.markdown("## How the desk decides")
    st.html(
        """
<table class="steps">
  <tr><td class="k">1</td><td class="t">Read the application</td>
      <td class="d">28 details: age, income, device, how fast requests arrive, and more.</td></tr>
  <tr><td class="k">2</td><td class="t">Estimate the fraud risk</td>
      <td class="d">A model trained on past months gives a probability, for example 3%.</td></tr>
  <tr><td class="k">3</td><td class="t">Price each option</td>
      <td class="d">What would letting it through, checking it, or blocking it cost on average?</td></tr>
  <tr><td class="k">4</td><td class="t">Stamp the cheapest</td>
      <td class="d">The option with the lowest expected loss wins. No fixed 50% cut-off.</td></tr>
</table>
"""
    )
    st.markdown("### The three prices, in plain words")
    st.markdown(
        "- **Let it through:** risk × size of the possible loss (bigger credit limit, bigger loss)\n"
        "- **Manual check:** the cost of the check + risk × the part of the loss a check can't stop\n"
        "- **Block it:** the chance it was a genuine customer × the cost of turning them away"
    )
    with st.expander("Show the formulas"):
        st.code(
            "E[cost(approve)] = p × amount × fraud_loss_rate\n"
            "E[cost(review)]  = review_cost + p × residual_fraud_loss\n"
            "E[cost(block)]   = (1 − p) × false_positive_cost\n"
            "action           = argmin of the three",
            language=None,
        )
        eff = {**load_costs(COSTS_PATH), **costs_override}
        st.dataframe(
            pd.DataFrame({
                "Setting": ["fraud_loss_rate", "false_positive_cost",
                            "review_cost", "residual_fraud_loss"],
                "Value": [f"{float(eff['fraud_loss_rate']):.10f}",
                          f"{float(eff['false_positive_cost']):.3f}",
                          f"{float(eff['review_cost']):.3f}",
                          f"{float(eff['residual_fraud_loss']):.2f}"],
            }),
            hide_index=True, width="content",
        )
        st.caption(
            "fraud_loss_rate = 1 / 521.1626, the average credit limit in the "
            "training months only. No test data was used to set any cost."
        )

    st.markdown("### Why bigger applications get more caution")
    rows = []
    for amt in (200, 500, 1000, 1500, 2000):
        z = {a: (lo, hi) for a, lo, hi in decision_zones(amt, costs_override)}
        # Quote each boundary once, as the start of the next zone, so
        # adjacent cells never disagree after rounding.
        rev_lo = z["review"][0] if "review" in z else None
        blk_lo = z["block"][0] if "block" in z else None
        upper_approve = rev_lo if rev_lo is not None else blk_lo
        let = fmt_pct(upper_approve) if "approve" in z and upper_approve is not None else "n/a"
        chk = (f"{fmt_pct(rev_lo)} to {fmt_pct(blk_lo)}"
               if rev_lo is not None and blk_lo is not None else "no check zone")
        blk = fmt_pct(z["block"][0]) if "block" in z else "no block zone"
        rows.append(f'<tr><td class="n">{amt:,}</td><td class="n">{let}</td>'
                    f'<td class="n">{chk}</td><td class="n">{blk}</td></tr>')
    st.html(
        '<table class="ledger wide"><tr><th class="n">Credit limit</th>'
        '<th class="n">Let through if risk below</th><th class="n">Check if risk between</th>'
        f'<th class="n">Block if risk above</th></tr>{"".join(rows)}</table>'
    )
    st.caption("Computed live from the cost settings. The cheapest-option rule is the source of truth.")

    with st.expander("Model card"):
        st.markdown(
            f"- **Model:** {type(model).__name__}, {len(features)} input features\n"
            "- **Learned from:** months 0–2 · **tuned on:** months 3–4 · **tested on:** months 5–6\n"
            "- **Fraud labels arrive one month late.** Month 7 (96,843 rows, 9.68%) "
            "has no label yet and is left out, not counted as legitimate.\n"
            "- **Probability check:** calibration error (ECE) 0.0033, well under the 0.05 gate"
        )
        if cv_results:
            results = cv_results.get("results", {})
            cv_rows = []
            for alg in ("logistic_regression", "random_forest", "lightgbm"):
                f1s = [r["macro_f1"] for r in results.get(alg, [])]
                if f1s:
                    cv_rows.append({"Algorithm": alg.replace("_", " ").title(),
                                    "Macro-F1 (mean)": round(float(np.mean(f1s)), 4),
                                    "Macro-F1 (sd)": round(float(np.std(f1s)), 4)})
            if cv_rows:
                st.dataframe(pd.DataFrame(cv_rows), hide_index=True, width="stretch")
        if importances and len(importances.get("features", [])) == len(importances.get("importances", [])):
            imp = (pd.DataFrame(importances).sort_values("importances", ascending=False).head(10))
            chart = (
                alt.Chart(imp)
                .mark_bar(color=PALETTE["cover"], cornerRadiusEnd=4, height=14)
                .encode(
                    x=alt.X("importances:Q", title="Importance"),
                    y=alt.Y("features:N", sort="-x", title=None),
                    tooltip=[alt.Tooltip("features:N", title="Feature"),
                             alt.Tooltip("importances:Q", title="Importance", format=".3f")],
                )
                .properties(height=300, title="Top 10 features")
            )
            st.altair_chart(chart, width="stretch")


# ============================================================
# Tab 4: study results
# ============================================================
def tab_results() -> None:
    st.html(
        '<div class="headline"><span class="num">57.91%</span> lower cost than the best simple rule</div>'
    )
    st.markdown(
        "Tested once on **227,491** applications from months the model never saw. "
        "We are 95% confident the true reduction is between **53.95%** and **62.13%**."
    )

    st.markdown("### Average cost per application, by strategy")
    data = pd.DataFrame(BASELINE_COSTS, columns=["Strategy", "Cost"])
    data["is_desk"] = data["Strategy"].str.startswith("Decision desk")
    base = alt.Chart(data).encode(
        y=alt.Y("Strategy:N", sort=None, title=None,
                axis=alt.Axis(labelLimit=320, labelFontSize=14)),
        x=alt.X("Cost:Q", title="Cost per application (lower is better)",
                axis=alt.Axis(format=".2f")),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=22).encode(
        color=alt.condition("datum.is_desk", alt.value(PALETTE["cover"]),
                            alt.value(PALETTE["neutral_bar"])),
        tooltip=[alt.Tooltip("Strategy:N"), alt.Tooltip("Cost:Q", format=".6f")],
    )
    labels = base.mark_text(align="left", dx=6, fontSize=13, color=PALETTE["ink"],
                            font="JetBrains Mono").encode(text=alt.Text("Cost:Q", format=".6f"))
    st.altair_chart((bars + labels).properties(height=330), width="stretch")
    st.caption(
        "A 50% cut-off barely beats approving everyone, because fraud is only "
        "about 1% of applications. Weighing costs is what makes the difference."
    )

    st.markdown("### Does it still hold if our cost guesses are off?")
    st.markdown(
        "We halved and doubled each cost one at a time without retraining. The "
        "desk stayed **at least 47.76%** cheaper in every case."
    )
    worst = min(s[2] for s in SENSITIVITY)
    sens_rows = "".join(
        f'<tr class="{"hl" if adv == worst else ""}"><td>{html.escape(name)}</td>'
        f'<td class="n">{cost:.6f}</td><td class="n">{adv:.2f}%</td></tr>'
        for name, cost, adv in SENSITIVITY
    )
    st.html(
        '<table class="ledger wide"><tr><th>Scenario</th><th class="n">Desk cost</th>'
        f'<th class="n">Cheaper by</th></tr>{sens_rows}</table>'
    )

    st.markdown("### What this does not show")
    st.markdown(
        "- The data is the **synthetic** Bank Account Fraud dataset, not a real bank's records\n"
        "- Only a **one-month** label delay was tested\n"
        "- The credit limit stands in for the amount at risk\n"
        "- Comparing the three models was a **non-finding** (1.07% apart, under the 5% bar), "
        "so the simplest one, Logistic Regression, is used"
    )

    with st.expander("Technical metrics (test window)"):
        st.dataframe(
            pd.DataFrame({
                "Metric": ["Policy recall", "Policy precision", "Recall @ 5%",
                           "Precision @ 5%", "ROC-AUC", "Calibration error (ECE)"],
                "Value": [0.5051, 0.0654, 0.4729, 0.1189, 0.8753, 0.0033],
            }),
            hide_index=True, width="content",
        )


# ============================================================
# Main
# ============================================================
def main() -> None:
    st.set_page_config(
        page_title="Fraud Decision Desk",
        page_icon=":material/approval:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    altair_theme()
    header_band()

    model, pre, features, _defaults, importances, cv_results = load_artifacts()
    costs_override = sidebar_settings()

    t1, t2, t3, t4 = st.tabs(
        ["Check one application", "Check a batch", "How it decides", "Study results"]
    )
    with t1:
        tab_single(features, model, pre, costs_override)
    with t2:
        tab_batch(features, model, pre, costs_override)
    with t3:
        tab_how(model, features, importances, cv_results, costs_override)
    with t4:
        tab_results()


if __name__ == "__main__":
    main()
