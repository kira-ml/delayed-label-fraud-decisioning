"""Streamlit application for BAF fraud classification.

Loads the same model + preprocessing pipeline reported in the paper.
Run locally with:  streamlit run app/streamlit_app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import joblib

from src.common import CATEGORICAL_COLS
from src.models.preprocess import get_feature_columns

MODEL_PATH = Path("models/best_model.pkl")
PREPROC_PATH = Path("models/preprocessing.pkl")


@st.cache_resource(show_spinner=False)
def load_artifacts():
    if not MODEL_PATH.exists() or not PREPROC_PATH.exists():
        st.error(
            "Model artifacts not found. Run the primary pipeline first:\n\n"
            "```\npython -m src.models.train_compare\n"
            "python -m src.models.evaluate_compare\n```"
        )
        st.stop()
    model = joblib.load(MODEL_PATH)
    pre = joblib.load(PREPROC_PATH)
    return model, pre


def _predict(model, pre, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    X_t = pre.transform(X)
    if hasattr(X_t, "toarray"):
        X_t = X_t.toarray()
    preds = model.predict(X_t)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_t)[:, 1]
    else:
        proba = np.full(len(X_t), np.nan)
    return preds, proba


def _validate(df: pd.DataFrame, required: list[str]) -> list[str]:
    problems = []
    missing = [c for c in required if c not in df.columns]
    if missing:
        problems.append(f"Missing required columns: {missing}")
    for c in CATEGORICAL_COLS:
        if c in df.columns and df[c].isna().any():
            problems.append(f"Categorical column '{c}' contains missing values.")
    return problems


def main() -> None:
    st.set_page_config(page_title="BAF Fraud Classifier", layout="wide")
    st.title("Bank Account Fraud Classifier")
    st.caption(
        "Predicts `fraud_bool` from transaction features using the selected "
        "primary model. Output: 0 = legitimate, 1 = fraud."
    )

    model, pre = load_artifacts()

    with st.sidebar:
        st.header("Model")
        st.write(f"Type: `{type(model).__name__}`")
        st.write("Output: `0 = legit`, `1 = fraud`")
        st.write("Input: CSV with the same columns as the BAF `Base.csv`.")
        st.write(
            "See `documentation/data_dictionary.md` for feature units and "
            "allowed values."
        )

    tab_upload, tab_manual = st.tabs(["CSV upload", "Manual input"])

    with tab_upload:
        uploaded = st.file_uploader("Upload a CSV of transactions", type=["csv"])
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")
                return

            required = get_feature_columns(df)
            problems = _validate(df, required)
            if problems:
                for p in problems:
                    st.error(p)
                return

            with st.spinner("Scoring..."):
                preds, proba = _predict(model, pre, df[required])

            out = df.copy()
            out["prediction"] = preds
            out["fraud_probability"] = proba
            st.success(f"Scored {len(out):,} rows.")
            st.dataframe(out[["prediction", "fraud_probability"]].head(50))
            st.download_button(
                "Download predictions CSV",
                out.to_csv(index=False).encode("utf-8"),
                "predictions.csv",
                "text/csv",
            )

    with tab_manual:
        st.info(
            "Manual entry is provided for a small subset of common features. "
            "For a full feature vector, use the CSV upload tab."
        )
        with st.form("manual"):
            proposed_credit_limit = st.number_input(
                "proposed_credit_limit (proxy for amount)",
                min_value=0.0, value=500.0, step=50.0,
            )
            customer_age = st.number_input(
                "customer_age", min_value=0, max_value=120, value=35,
            )
            payment_type = st.selectbox("payment_type", ["AA", "AB", "AC", "AD", "AE"])
            employment_status = st.selectbox(
                "employment_status", ["CA", "CB", "CC", "CD", "CE", "CF", "CG"]
            )
            submitted = st.form_submit_button("Predict")
        if submitted:
            row = {
                "proposed_credit_limit": proposed_credit_limit,
                "amount_proxy": proposed_credit_limit,
                "customer_age": customer_age,
                "payment_type": payment_type,
                "employment_status": employment_status,
            }
            # Fill any other required columns with sensible defaults so the
            # pipeline can run. In production this form would include all
            # features, or the app would refuse the input.
            required = get_feature_columns(pd.DataFrame([row]))
            for c in required:
                row.setdefault(c, 0)
            df = pd.DataFrame([row])[required]
            try:
                preds, proba = _predict(model, pre, df)
                label = "FRAUD" if preds[0] == 1 else "LEGITIMATE"
                st.metric("Prediction", label)
                st.metric("Fraud probability", f"{proba[0]:.4f}")
            except Exception as e:
                st.error(f"Prediction failed: {e}")


if __name__ == "__main__":
    main()