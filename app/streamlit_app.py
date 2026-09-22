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

ACTION_ICON = {"approve": "✅", "review": "🔎", "block": "⛔"}

# ---------------------------------------------------------------------------
# Palette (single source of truth for both the charts and the CSS)
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
}


# ============================================================
# Pure functions (unit-testable)
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


def route_actions(p, amounts):
    costs = load_costs(COSTS_PATH)
    actions, chosen_cost, _ = choose_actions(p, costs, amounts)
    return actions, chosen_cost


# ============================================================
# Artifact loading
# ============================================================
@st.cache_resource(show_spinner=False)
def load_artifacts():
    for p in (MODEL_PATH, PREPROC_PATH, FEATURES_PATH):
        if not p.exists():
            st.error(
                f"Missing artifact: `{p}`.\n\nRun: `python -m src.pipeline --primary`"
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
    return model, pre, features, defaults, importances


# ============================================================
# Matplotlib dark theme (matches the app palette)
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
# CSS
# ============================================================
def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        /* ---------- App shell ---------- */
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

        /* ---------- Headings ---------- */
        h1, h2, h3 {{ color: {PALETTE["text"]} !important;
                       letter-spacing: -0.01em; }}
        h1 {{ font-weight: 700; }}
        h3 {{ font-weight: 600; margin-top: 1.6rem; }}

        /* ---------- Metric tiles ---------- */
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

        /* ---------- Cards ---------- */
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

        /* ---------- Muted text ---------- */
        .muted {{
            color: {PALETTE["text_muted"]} !important;
            font-size: 0.9rem;
        }}

        /* ---------- Badges ---------- */
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

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background: {PALETTE["surface"]} !important;
            border-right: 1px solid {PALETTE["border"]};
        }}
        section[data-testid="stSidebar"] * {{
            color: {PALETTE["text"]};
        }}
        section[data-testid="stSidebar"] .muted {{
            color: {PALETTE["text_muted"]} !important;
        }}
        section[data-testid="stSidebar"] .card {{
            background: {PALETTE["surface_alt"]};
        }}

        /* ---------- Tabs ---------- */
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

        /* ---------- Inputs ---------- */
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

        /* ---------- Buttons ---------- */
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

        /* ---------- Dataframe ---------- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {PALETTE["border"]};
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ---------- Alerts ---------- */
        div[data-testid="stAlert"] {{
            border-radius: 10px;
        }}

        /* ---------- Divider ---------- */
        hr {{ border-color: {PALETTE["border"]}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UI sections
# ============================================================
def sidebar(model, features, importances) -> None:
    with st.sidebar:
        st.markdown("### Model")
        st.markdown(
            f"""
            <div class="card">
            <b>Algorithm</b><br><span class="muted">{type(model).__name__}</span><br>
            <b>Features</b><br><span class="muted">{len(features)}</span><br>
            <b>Output</b><br><span class="muted">0 = legitimate · 1 = fraud</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Metrics")
        st.markdown(
            """
            <div class="card">
            <b>Macro F1</b> 0.5336<br>
            <b>ROC-AUC</b> 0.8766<br>
            <b>Precision (fraud)</b> 0.3096<br>
            <b>Recall (fraud)</b> 0.0424
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Top feature importances"):
            if importances:
                imp_df = pd.DataFrame(importances).sort_values(
                    "importances", ascending=False
                ).head(15)
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
            "Precision/recall at default threshold 0.5. Operational decisions "
            "come from the cost-sensitive policy, not from thresholding at 0.5."
        )


def batch_analytics(df: pd.DataFrame, preds: np.ndarray,
                    proba: np.ndarray, actions: np.ndarray) -> None:
    st.markdown("### Batch analytics")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows scored", f"{len(df):,}")
    c2.metric("Predicted fraud", f"{int(preds.sum()):,}",
              f"{preds.mean():.2%}")
    c3.metric("Mean fraud probability", f"{proba.mean():.4f}")
    c4.metric("High-risk (p ≥ 0.5)", f"{int((proba >= 0.5).sum()):,}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Score distribution**")
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.hist(proba, bins=30, color=PALETTE["accent"],
                edgecolor=PALETTE["bg"])
        ax.set_xlabel("fraud probability")
        ax.set_ylabel("transactions")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

    with col_b:
        st.markdown("**Cost-sensitive routing**")
        counts = pd.Series(actions).value_counts().reindex(
            ["approve", "review", "block"], fill_value=0
        )
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(
            counts.index,
            counts.values,
            color=[PALETTE["approve"], PALETTE["review"], PALETTE["block"]],
        )
        ax.set_ylabel("transactions")
        ax.grid(True, alpha=0.25, axis="y")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

    st.markdown("**Cost-sensitive policy summary**")
    costs = load_costs(COSTS_PATH)
    approve_all_cost = (
        proba * (
            df["amount_proxy"].values * costs["fraud_loss_rate"]
            if costs.get("amount_scaled", False) and "amount_proxy" in df.columns
            else costs["fraud_loss"]
        )
    ).sum()
    policy_cost = route_actions(
        proba,
        df["amount_proxy"].values if "amount_proxy" in df.columns else None,
    )[1].sum()
    saved = approve_all_cost - policy_cost
    pct = saved / approve_all_cost if approve_all_cost else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Est. approve-all cost", f"{approve_all_cost:.2f}")
    c2.metric("Policy cost", f"{policy_cost:.2f}")
    c3.metric("Est. savings", f"{saved:.2f}", f"{pct:.1%}")
    st.caption(
        "Cost figures are model-based estimates on this batch. Ground-truth "
        "costs are reported in `reports/mvp_backtest.md` using labeled test data."
    )


def batch_results_table(df: pd.DataFrame, preds: np.ndarray,
                        proba: np.ndarray, actions: np.ndarray) -> None:
    st.markdown("### Highest-risk transactions")
    out = df.copy()
    out["prediction"] = preds
    out["fraud_probability"] = proba
    out["action"] = actions
    out = out.sort_values("fraud_probability", ascending=False)
    st.dataframe(
        out[["transaction_id", "fraud_probability", "prediction", "action"]].head(20),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "⬇ Download full predictions CSV",
        out.to_csv(index=False).encode("utf-8"),
        "predictions.csv",
        "text/csv",
    )


def manual_form(features, defaults, model, pre) -> None:
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
                min_value=0,
                max_value=120,
                value=int(row.get("customer_age", 35)),
            )
        with c2:
            payment_type = st.selectbox(
                "payment_type", ["AA", "AB", "AC", "AD", "AE"]
            )
            employment_status = st.selectbox(
                "employment_status",
                ["CA", "CB", "CC", "CD", "CE", "CF", "CG"],
            )
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
            amt = df_row["amount_proxy"].values if "amount_proxy" in df_row.columns else None
            actions, _ = route_actions(proba, amt)
            label = "FRAUD" if preds[0] == 1 else "LEGITIMATE"
            action = actions[0]
            st.markdown(
                f"""
                <div class="card">
                <div class="badge badge-{action}">
                    {ACTION_ICON[action]} {action.upper()}
                </div>
                <h3>{label}</h3>
                <span class="muted">Fraud probability: <b>{proba[0]:.4f}</b></span>
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

    model, pre, features, defaults, importances = load_artifacts()
    sidebar(model, features, importances)

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
            errs = validate_input(df, features)
            if errs:
                for e in errs:
                    st.error(e)
                return

            with st.spinner("Scoring..."):
                preds, proba = predict(model, pre, df[features])
                amt = df["amount_proxy"].values if "amount_proxy" in df.columns else None
                actions, _ = route_actions(proba, amt)

            batch_analytics(df, preds, proba, actions)
            batch_results_table(df, preds, proba, actions)

    with tab_manual:
        manual_form(features, defaults, model, pre)


if __name__ == "__main__":
    main()