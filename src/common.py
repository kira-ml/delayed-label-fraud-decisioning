from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"
CONFIGS = ROOT / "configs"

for _p in (DATA_INTERIM, DATA_PROCESSED, ARTIFACTS, REPORTS):
    _p.mkdir(parents=True, exist_ok=True)

FEATURE_EXCLUDE = {
    "transaction_id",
    "fraud_bool",
    "month",
    "label_month",
    "observed",
    "amount_proxy",
    "device_fraud_count",
}


def feature_columns(df):
    return [c for c in df.columns if c not in FEATURE_EXCLUDE]


def load_costs():
    with open(CONFIGS / "costs.yaml") as f:
        return yaml.safe_load(f)