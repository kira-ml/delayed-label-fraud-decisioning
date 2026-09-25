"""Streamlit application for BAF fraud classification.

Loads the same model + preprocessing pipeline reported in the paper.
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

import json

import numpy as np
import pandas as pd
import streamlit as st
import joblib
import matplotlib.pyplot as plt

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

ACTION_ICON = {"approve": "✅", "review": "🔎", "block": "⛔"}
ACTION_ORDER = ["approve", "review", "block"]

# Training-window fraud rate (docs/data_card.md §2.1). Used only for the
# out-of-distribution banner.
TRAIN_FRAUD_RATE = 0.0103

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
PALETTE = {
    "bg":            "#1a1d29",
    "surface":       "#252a3a",
    "surface_alt":   "#2d3346",
    "border":        "#343b52",
    "text":          "#e8ecf4",
    "text_muted":    "#9aa4b8",
    "accent":        "#7c9cff",
    "accent_soft":   "#3a4a75",
    "approve":       "#6ee7a8",
    "approve_bg":    "#1e3a2c",
    "review":        "#fbbf78",
    "review_bg":     "#3a2f1c",
    "block":         "#f28b8b",
    "block_bg":      "#3a2020",
    "warn":          "#fbbf78",
}


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


# ============================================================
# Matplotlib theme
# ============================================================
def apply_mpl_theme() -> None:
    plt.rcParams.update({
        "figure.facecolor":  PALETTE["surface"],
        "axes.facecolor":    PALETTE["surface"],
        "axes.edgecolor":    PALETTE["border"],
        "axes.labelcolor":   PALETTE["text_muted"],
        "axes.titlecolor":   PALETTE["text"],
        "xtick.color":       PALETTE["text_muted"],
        "ytick.color":       PALETTE["text_muted"],
        "text.color":        PALETTE["text"],
        "grid.color":        PALETTE["border"],
        "grid.alpha":        0.35,
        "savefig.facecolor": PALETTE["surface"],
        "font.size":         9,
    })


# ============================================================
# CSS (unchanged from before)
# ============================================================
def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg,
                        {PALETTE["bg"]} 0%,
                        {PALETTE["bg"]} 100%);
            color: {PALETTE["text"]};
        }}
        .main .block-container {{
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        h1, h2, h3 {{ color: {PALETTE["text"]} !important;
                       letter-spacing: -0.01em; }}
        h1 {{ font-weight: 700; }}
        h3 {{ font-weight: 600; margin-top: 1.6rem; }}

        div[data-testid="stMetric"] {{
            background: {PALETTE["surface"]};
            border: 1px solid {PALETTE["border"]};
            border-left: 3px solid {PALETTE["accent"]};
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
        }}
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {{
            color: {PALETTE["text_muted"]} !important;
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 600;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] * {{
            color: {PALETTE["text"]} !important;
            font-weight: 600;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricDelta"],
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] * {{
            color: {PALETTE["accent"]} !important;
        }}

        .card {{
            background: {PALETTE["surface"]};
            border: 1px solid {PALETTE["border"]};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
            color: {PALETTE["text"]};
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }}
        .card b, .card strong {{ color: {PALETTE["text"]}; }}
        .card h3 {{ color: {PALETTE["text"]} !important; margin-top: 0.4rem; }}
        .muted {{ color: {PALETTE["text_muted"]} !important; font-size: 0.9rem; }}

        .badge {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        .badge-approve {{
            background: {PALETTE["approve_bg"]};
            color: {PALETTE["approve"]} !important;
            border: 1px solid {PALETTE["approve"]}44;
        }}
        .badge-review {{
            background: {PALETTE["review_bg"]};
            color: {PALETTE["review"]} !important;
            border: 1px solid {PALETTE["review"]}44;
        }}
        .badge-block {{
            background: {PALETTE["block_bg"]};
            color: {PALETTE["block"]} !important;
            border: 1px solid {PALETTE["block"]}44;
        }}

        section[data-testid="stSidebar"] {{
            background: {PALETTE["surface"]} !important;
            border-right: 1px solid {PALETTE["border"]};
        }}
        section[data-testid="stSidebar"] * {{ color: {PALETTE["text"]}; }}
        section[data-testid="stSidebar"] .muted {{
            color: {PALETTE["text_muted"]} !important;
        }}
        section[data-testid="stSidebar"] .card {{
            background: {PALETTE["surface_alt"]};
        }}

        button[data-baseweb="tab"] {{
            color: {PALETTE["text_muted"]};
            font-weight: 600;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PALETTE["accent"]} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {PALETTE["accent"]} !important;
        }}
        div[data-baseweb="tab-border"] {{
            background-color: {PALETTE["border"]} !important;
        }}

        .stTextInput input, .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] > div {{
            background-color: {PALETTE["surface_alt"]} !important;
            color: {PALETTE["text"]} !important;
            border: 1px solid {PALETTE["border"]} !important;
            border-radius: 8px;
        }}
        .stFileUploader section {{
            background-color: {PALETTE["surface_alt"]};
            border: 1px dashed {PALETTE["border"]};
            border-radius: 12px;
        }}

        .stButton > button, .stDownloadButton > button {{
            background: {PALETTE["accent"]};
            color: #0f1220 !important;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background: {PALETTE["accent_soft"]};
            color: {PALETTE["text"]} !important;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {PALETTE["border"]};
            border-radius: 10px;
            overflow: hidden;
        }}
        div[data-testid="stAlert"] {{ border-radius: 10px; }}
        hr {{ border-color: {PALETTE["border"]}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Sidebar
# ============================================================
def sidebar(model, features, importances, cv_results) -> dict:
    """Render the sidebar. Returns cost overrides (may be empty)."""
    with st.sidebar:
        st.markdown("### Model card")
        st.markdown(
            f"""
            <div class="card">
            <b>Algorithm</b><br><span class="muted">{type(model).__name__}</span><br>
            <b>Training window</b><br><span class="muted">Months 0–2</span><br>
            <b>Validation window</b><br><span class="muted">Months 3–4</span><br>
            <b>Test window</b><br><span class="muted">Months 5–6</span><br>
            <b>Features</b><br><span class="muted">{len(features)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Policy metrics (test window)")
        st.markdown(
            """
            <div class="card">
            <b>Policy recall</b> 0.5051<br>
            <b>Policy precision</b> 0.0654<br>
            <b>Recall@5%</b> 0.4729<br>
            <b>Precision@5%</b> 0.1189<br>
            <b>ROC-AUC</b> 0.8753<br>
            <b>Calibration ECE</b> 0.0033
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Cost what-if ----
        base = load_costs(COSTS_PATH)
        st.markdown("### Cost what-if")
        with st.expander("Adjust cost matrix", expanded=False):
            fpc = st.slider(
                "false_positive_cost", min_value=0.01, max_value=0.50,
                value=float(base["false_positive_cost"]), step=0.01,
            )
            rc = st.slider(
                "review_cost", min_value=0.001, max_value=0.10,
                value=float(base["review_cost"]), step=0.001, format="%.3f",
            )
            rfl = st.slider(
                "residual_fraud_loss", min_value=0.05, max_value=0.90,
                value=float(base["residual_fraud_loss"]), step=0.05,
            )
        override = {
            "false_positive_cost": fpc,
            "review_cost": rc,
            "residual_fraud_loss": rfl,
        }

        # ---- Derived thresholds ----
        eff = {**base, **override}
        denom_rev = float(eff["fraud_loss"]) - float(eff["residual_fraud_loss"])
        p_rev = (float(eff["review_cost"]) / denom_rev) if denom_rev > 0 else float("nan")
        denom_blk = float(eff["false_positive_cost"]) + float(eff["residual_fraud_loss"])
        p_blk = (
            (float(eff["false_positive_cost"]) - float(eff["review_cost"])) / denom_blk
        ) if denom_blk > 0 else float("nan")

        st.markdown("### Derived thresholds")
        st.markdown(
            f"""
            <div class="card">
            <span class="muted">
            p &lt; <b>{p_rev:.4f}</b> → approve<br>
            {p_rev:.4f} ≤ p &lt; <b>{p_blk:.4f}</b> → review<br>
            p ≥ {p_blk:.4f} → block
            </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Diagnostic view only. The argmin of expected cost is the source "
            "of truth; thresholds are derived from the cost matrix."
        )

        # ---- 3-algorithm comparison ----
        with st.expander("3-algorithm comparison (2-fold CV)"):
            if cv_results:
                results = cv_results.get("results", {})
                rows = []
                for alg in ("logistic_regression", "random_forest", "lightgbm"):
                    f1s = [r["macro_f1"] for r in results.get(alg, [])]
                    if not f1s:
                        continue
                    rows.append({
                        "algorithm": alg,
                        "macro_f1_mean": float(np.mean(f1s)),
                        "macro_f1_sd":   float(np.std(f1s)),
                    })
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True,
                                 use_container_width=True)
                    st.caption(
                        "See `reports/model_comparison.md` for the selected "
                        "classifier and the selection justification."
                    )
            else:
                st.caption("Run `train_compare` to generate `cv_results.json`.")

        # ---- Feature importances ----
        with st.expander("Top feature importances"):
            if (
                importances
                and len(importances.get("features", []))
                    == len(importances.get("importances", []))
            ):
                imp_df = (
                    pd.DataFrame(importances)
                    .sort_values("importances", ascending=False)
                    .head(15)
                )
                fig, ax = plt.subplots(figsize=(4, 5))
                ax.barh(
                    imp_df["features"][::-1],
                    imp_df["importances"][::-1],
                    color=PALETTE["accent"],
                )
                ax.set_xlabel("importance")
                ax.tick_params(labelsize=8)
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
            else:
                st.caption("Run `evaluate_compare` to generate importances.")

        st.markdown("---")
        st.caption(
            "Operational decisions use the argmin of expected cost, not a "
            "0.5 probability threshold."
        )

    return override


# ============================================================
# Batch sections
# ============================================================
def drift_banner(proba: np.ndarray) -> None:
    """Warn if batch mean p_fraud is far from training-window rate."""
    mean_p = float(np.mean(proba))
    hi = 3.0 * TRAIN_FRAUD_RATE
    lo = TRAIN_FRAUD_RATE / 3.0
    if mean_p > hi:
        st.warning(
            f"Batch mean fraud probability ({mean_p:.4f}) is well above the "
            f"training-window fraud rate (~{TRAIN_FRAUD_RATE:.4f}). This batch "
            "may be out of distribution — interpret scores with caution."
        )
    elif mean_p < lo:
        st.info(
            f"Batch mean fraud probability ({mean_p:.4f}) is well below the "
            f"training-window rate (~{TRAIN_FRAUD_RATE:.4f}). The batch looks "
            "cleaner than the training data."
        )


def batch_summary(df, preds, proba, routing, amounts) -> None:
    st.markdown("### Batch summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows scored", f"{len(df):,}")
    c2.metric("Predicted fraud", f"{int(preds.sum()):,}", f"{preds.mean():.2%}")
    c3.metric("Mean fraud probability", f"{proba.mean():.4f}")
    c4.metric("High-risk (p ≥ 0.5)", f"{int((proba >= 0.5).sum()):,}")

    drift_banner(proba)

    approve_all_cost = float(routing["expected_cost_approve"].sum())
    policy_cost = float(routing["chosen_cost"].sum())
    saved = approve_all_cost - policy_cost
    pct = (saved / approve_all_cost) if approve_all_cost else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Est. approve-all cost", f"{approve_all_cost:,.2f}")
    c2.metric("Est. policy cost", f"{policy_cost:,.2f}")
    c3.metric("Est. expected savings", f"{saved:,.2f}", f"{pct:.1%}")
    st.caption(
        "Model-based estimates on this batch. Ground-truth costs are reported "
        "in `reports/decision_backtest.md` using labeled test data."
    )


def review_capacity_panel(routing, df) -> None:
    st.markdown("### Review capacity (top-K by expected savings)")
    savings = routing["expected_savings"]
    total_savings = float(np.sum(np.clip(savings, 0, None)))

    n = len(df)
    default_k = max(1, int(0.02 * n))
    k = st.slider(
        "Review slots (rows you can act on)",
        min_value=1, max_value=max(1, n),
        value=min(default_k, n),
        step=max(1, n // 100),
    )

    order = np.argsort(-savings)
    top = order[:k]
    covered = float(np.sum(np.clip(savings[top], 0, None)))
    cov_pct = (covered / total_savings) if total_savings else 0.0

    actions_in_top = pd.Series(routing["actions"][top]).value_counts().reindex(
        ACTION_ORDER, fill_value=0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Top-K savings captured", f"{covered:,.2f}",
              f"{cov_pct:.1%} of total")
    c2.metric("Rows in review in top-K", int(actions_in_top["review"]))
    c3.metric("Rows in block in top-K", int(actions_in_top["block"]))

    st.caption(
        "Ranking view, not a re-decision. Rows you cannot act on keep their "
        "unconstrained action. See `evaluation_protocol.md` §10 for the "
        "budget-constrained reporting convention."
    )


def segment_breakdown(df, proba, routing) -> None:
    """Fraud rate + action mix by categorical feature."""
    cats_present = [c for c in CATEGORICAL_COLS if c in df.columns]
    if not cats_present:
        return

    st.markdown("### Segment breakdown")
    seg = st.selectbox("Segment by", cats_present, key="seg_col")

    tmp = pd.DataFrame({
        "segment": df[seg].astype(str).values,
        "p_fraud": proba,
        "action": routing["actions"],
    })
    grouped = tmp.groupby("segment").agg(
        rows=("p_fraud", "size"),
        mean_p=("p_fraud", "mean"),
    )
    action_mix = (
        tmp.groupby(["segment", "action"]).size().unstack(fill_value=0)
        .reindex(columns=ACTION_ORDER, fill_value=0)
    )
    table = grouped.join(action_mix).sort_values("mean_p", ascending=False)
    table = table.rename(columns={
        "rows": "rows",
        "mean_p": "mean fraud prob",
        "approve": "approve",
        "review": "review",
        "block": "block",
    })

    st.dataframe(
        table.style.format({
            "mean fraud prob": "{:.4f}",
            "rows": "{:,.0f}",
            "approve": "{:,.0f}",
            "review": "{:,.0f}",
            "block": "{:,.0f}",
        }),
        use_container_width=True,
    )
    st.caption(
        "Mean fraud probability and policy action mix per segment. Useful for "
        "spotting concentrated signal or mispriced segments."
    )


def batch_results_table(df, preds, proba, routing) -> None:
    st.markdown("### Prioritised worklist (top 50 by expected savings)")

    out = df.copy()
    out["prediction"] = preds
    out["fraud_probability"] = proba
    out["action"] = routing["actions"]
    out["expected_cost_approve"] = routing["expected_cost_approve"]
    out["expected_cost_review"] = routing["expected_cost_review"]
    out["expected_cost_block"] = routing["expected_cost_block"]
    out["chosen_expected_cost"] = routing["chosen_cost"]
    out["expected_savings"] = routing["expected_savings"]

    out = out.sort_values("expected_savings", ascending=False).reset_index(drop=True)
    out["priority_rank"] = out.index + 1

    display_cols = [
        "priority_rank", "transaction_id", "fraud_probability", "action",
        "expected_savings", "chosen_expected_cost",
        "expected_cost_approve", "expected_cost_review", "expected_cost_block",
    ]
    display_cols = [c for c in display_cols if c in out.columns]

    st.dataframe(
        out[display_cols].head(50).style.format({
            "fraud_probability": "{:.4f}",
            "expected_savings": "{:.4f}",
            "chosen_expected_cost": "{:.4f}",
            "expected_cost_approve": "{:.4f}",
            "expected_cost_review": "{:.4f}",
            "expected_cost_block": "{:.4f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇ Download full predictions CSV (all rows, all columns)",
        out.to_csv(index=False).encode("utf-8"),
        "predictions.csv",
        "text/csv",
    )


# ============================================================
# Manual form
# ============================================================
def manual_form(features, defaults, model, pre, costs_override) -> None:
    st.info(
        "Manual entry exposes a subset of common fields. Missing features "
        "are filled with their **training-time median/mode** so the model "
        "receives the full feature vector it was trained on."
    )
    row = dict(defaults)
    with st.form("manual"):
        c1, c2 = st.columns(2)
        with c1:
            proposed_credit_limit = st.number_input(
                "proposed_credit_limit",
                min_value=0.0,
                value=float(row.get("proposed_credit_limit", 500.0)),
                step=50.0,
            )
            customer_age = st.number_input(
                "customer_age",
                min_value=0, max_value=120,
                value=int(row.get("customer_age", 35)),
            )
        cats = getattr(pre, "categories_", {}) or {}
        payment_opts = list(cats.get("payment_type", [])) or ["AA", "AB", "AC", "AD", "AE"]
        employ_opts  = list(cats.get("employment_status", [])) or ["CA", "CB", "CC", "CD", "CE", "CF", "CG"]
        with c2:
            payment_type = st.selectbox("payment_type", payment_opts)
            employment_status = st.selectbox("employment_status", employ_opts)
        submitted = st.form_submit_button("Predict")

    if submitted:
        row.update({
            "proposed_credit_limit": proposed_credit_limit,
            "customer_age": customer_age,
            "payment_type": payment_type,
            "employment_status": employment_status,
        })
        df_row = pd.DataFrame([{k: row.get(k) for k in features}])
        errs = validate_input(df_row, features)
        if errs:
            for e in errs:
                st.error(e)
            return
        try:
            preds, proba = predict(model, pre, df_row)
            amt = np.array([float(proposed_credit_limit)])
            routing = route_actions(proba, amt, costs_override)
            label = "FRAUD" if preds[0] == 1 else "LEGITIMATE"
            action = routing["actions"][0]
            savings = float(routing["expected_savings"][0])
            st.markdown(
                f"""
                <div class="card">
                <div class="badge badge-{action}">
                    {ACTION_ICON[action]} {action.upper()}
                </div>
                <h3>{label}</h3>
                <span class="muted">
                Fraud probability: <b>{proba[0]:.4f}</b><br>
                Expected savings vs approve: <b>{savings:.4f}</b>
                </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Prediction failed: {type(e).__name__}: {e}")


# ============================================================
# Main
# ============================================================
def main() -> None:
    st.set_page_config(
        page_title="BAF Fraud Classifier",
        page_icon="🛡️",
        layout="wide",
    )
    apply_mpl_theme()
    inject_css()

    st.title("🛡️ Bank Account Fraud Classifier")
    st.markdown(
        "<span class='muted'>Predicts fraud probability per transaction and "
        "routes each row to <b>approve</b>, <b>review</b>, or <b>block</b> "
        "using the cost-sensitive policy from the paper.</span>",
        unsafe_allow_html=True,
    )

    model, pre, features, defaults, importances, cv_results = load_artifacts()
    costs_override = sidebar(model, features, importances, cv_results)

    tab_upload, tab_manual = st.tabs(["📁 Batch upload", "✍️ Manual input"])

    with tab_upload:
        uploaded = st.file_uploader(
            "Upload a CSV with the same columns as BAF `Base.csv`",
            type=["csv"],
        )
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")
                return
            if "amount_proxy" not in df.columns and "proposed_credit_limit" in df.columns:
                df["amount_proxy"] = df["proposed_credit_limit"].astype(float)
            errs = validate_input(df, features)
            if errs:
                for e in errs:
                    st.error(e)
                return

            with st.spinner("Scoring..."):
                preds, proba = predict(model, pre, df[features])
                amt = (
                    df["amount_proxy"].values
                    if "amount_proxy" in df.columns else None
                )
                routing = route_actions(proba, amt, costs_override)

            batch_summary(df, preds, proba, routing, amt)
            review_capacity_panel(routing, df)
            batch_results_table(df, preds, proba, routing)
            segment_breakdown(df, proba, routing)

    with tab_manual:
        manual_form(features, defaults, model, pre, costs_override)


if __name__ == "__main__":
    main()