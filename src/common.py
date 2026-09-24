"""Shared constants, paths, and utilities for the fraud decisioning project."""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42


def set_seed(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


# ---------------------------------------------------------------------------
# Canonical paths
# ---------------------------------------------------------------------------
DATA_RAW       = Path("data/original")
DATA_INTERIM   = Path("data/interim")
DATA_PROCESSED = Path("data/processed")
MODELS         = Path("models")
ARTIFACTS      = Path("artifacts")
REPORTS        = Path("reports")
CONFIGS        = Path("configs")

COSTS_PATH = CONFIGS / "costs.yaml"


# ---------------------------------------------------------------------------
# Feature column policy (see docs/data_card.md §4.2)
# ---------------------------------------------------------------------------
FEATURE_EXCLUDE = [
    "transaction_id",        # row identifier
    "fraud_bool",            # target
    "month",                 # time index used for splits
    "label_month",           # derived from month
    "observed",              # derived from delay simulation
    "amount_proxy",          # reserved as cost input
    "proposed_credit_limit", # same value as amount_proxy
    "device_fraud_count",    # post-decision risk field
]

CATEGORICAL_COLS = [
    "payment_type",
    "employment_status",
    "housing_status",
    "source",
    "device_os",
]


# ---------------------------------------------------------------------------
# Split month definitions
# ---------------------------------------------------------------------------
# Single chronological split — docs/data_card.md §5.2
SUPP_TRAIN_MONTHS    = [0, 1, 2]
SUPP_VAL_MONTHS      = [3, 4]
SUPP_TEST_MONTHS     = [5, 6]
SUPP_CENSORED_MONTHS = [7]

# ---------------------------------------------------------------------------
# Cost configuration
# ---------------------------------------------------------------------------
def load_costs(path: Path | str = COSTS_PATH) -> dict[str, Any]:
    """Load the frozen cost matrix from configs/costs.yaml.

    See docs/evaluation_protocol.md §5.1 for the schema and rationale.
    """
    with open(path) as f:
        return yaml.safe_load(f)