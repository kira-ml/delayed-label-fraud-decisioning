"""Pytest configuration: ensure repo root is on sys.path.

Without this, `pytest` invoked directly from the repo root cannot
resolve `from src.policy.decide import ...`. `python -m pytest` works
because `-m` adds the cwd to sys.path; plain `pytest` does not.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))