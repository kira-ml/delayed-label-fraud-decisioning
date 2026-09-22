"""Shared constants and utilities for the fraud decisioning project."""
import random
import numpy as np

SEED = 42

# Columns never used as model features.
# See docs/data_card.md §4.2 for the rationale behind each exclusion.
FEATURE_EXCLUDE = [
    "transaction_id",       # row identifier
    "fraud_bool",           # target
    "month",                # time index used for splits
    "label_month",          # derived from month
    "observed",             # derived from delay simulation
    "amount_proxy",         # reserved as cost input
    "proposed_credit_limit",# same value as amount_proxy
    "device_fraud_count",   # post-decision risk field
]

# Categorical columns in the BAF dataset.
CATEGORICAL_COLS = [
    "payment_type",
    "employment_status",
    "housing_status",
    "source",
    "device_os",
]

# Supplementary split months (see docs/data_card.md §6.4)
SUPP_TRAIN_MONTHS = [0, 1, 2]
SUPP_VAL_MONTHS = [3, 4]
SUPP_TEST_MONTHS = [5, 6]
SUPP_CENSORED_MONTHS = [7]

# Primary split months (chronological 80/20, see docs/data_card.md §5.2)
PRIMARY_TRAIN_MONTHS = [0, 1, 2, 3, 4, 5]
PRIMARY_TEST_MONTHS = [6, 7]


def set_seed(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)