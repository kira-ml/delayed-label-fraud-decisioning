"""Pipeline orchestration for the fraud decisioning project.

Two pipelines:

  Supplementary (project depth):
      load -> simulate_delay -> split -> train_baseline -> score
      -> decide -> backtest

  Primary (course deliverable):
      primary_split -> train_compare -> evaluate_compare

Usage:
    python -m src.pipeline                  # runs supplementary (default)
    python -m src.pipeline --primary        # runs primary only
    python -m src.pipeline --all            # runs both, primary first
    python -m src.pipeline --list           # prints the step order and exits

The supplementary pipeline is the MVP deliverable described in
docs/mvp_architecture.md §8.3. The primary pipeline is the course
deliverable described in docs/evaluation_protocol.md §4.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from typing import Callable

# Supplementary components
from src.data import load, simulate_delay, split
from src.models import train_baseline, score
from src.policy import decide
from src.evaluation import backtest

# Primary components (course deliverable)
from src.data import primary_split
from src.models import train_compare, evaluate_compare


SUPPLEMENTARY_STEPS: list[tuple[str, Callable[[], None]]] = [
    ("load",           load.main),
    ("simulate_delay", simulate_delay.main),
    ("split",          split.main),
    ("train_baseline", train_baseline.main),
    ("score",          score.main),
    ("decide",         decide.main),
    ("backtest",       backtest.main),
]

PRIMARY_STEPS: list[tuple[str, Callable[[], None]]] = [
    ("primary_split",    primary_split.main),
    ("train_compare",    train_compare.main),
    ("evaluate_compare", evaluate_compare.main),
]


def _run_pipeline(name: str, steps: list[tuple[str, Callable[[], None]]]) -> None:
    """Run a named sequence of steps with timing and error reporting."""
    print("=" * 60)
    print(f"{name} Pipeline")
    print("=" * 60)

    t0 = time.perf_counter()
    for i, (step_name, fn) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {step_name}")
        print("-" * 60)
        t_step = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            elapsed = time.perf_counter() - t_step
            print(f"\n[FAIL] {step_name} raised after {elapsed:.1f}s: "
                  f"{type(exc).__name__}: {exc}")
            raise
        elapsed = time.perf_counter() - t_step
        print(f"[ok] {step_name} finished in {elapsed:.1f}s")

    total = time.perf_counter() - t0
    print(f"\n=== {name} pipeline complete in {total:.1f}s ===")


def _print_list() -> None:
    print("Supplementary steps:")
    for i, (name, _) in enumerate(SUPPLEMENTARY_STEPS, 1):
        print(f"  {i}. {name}")
    print("\nPrimary steps:")
    for i, (name, _) in enumerate(PRIMARY_STEPS, 1):
        print(f"  {i}. {name}")


def _run_analyses() -> None:
    """Run the standalone sensitivity and bootstrap analyses."""
    for module in ("src.evaluation.sensitivity", "src.evaluation.bootstrap"):
        print("=" * 60)
        print(f"Analysis: {module}")
        print("=" * 60)
        subprocess.run([sys.executable, "-m", module], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the fraud decisioning pipeline(s)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--primary", action="store_true",
        help="run the primary (course) 3-algorithm pipeline only",
    )
    group.add_argument(
        "--supplementary", action="store_true",
        help="run the supplementary cost-sensitive pipeline only (default)",
    )
    group.add_argument(
        "--all", action="store_true",
        help="run both pipelines, primary first",
    )
    group.add_argument(
        "--list", action="store_true",
        help="print the step order for both pipelines and exit",
    )
    parser.add_argument(
        "--analyses", action="store_true",
        help="after the supplementary pipeline, also run sensitivity + bootstrap",
    )
    args = parser.parse_args()

    if args.list:
        _print_list()
        return

    if args.all:
        _run_pipeline("Primary", PRIMARY_STEPS)
        _run_pipeline("Supplementary", SUPPLEMENTARY_STEPS)
    elif args.primary:
        _run_pipeline("Primary", PRIMARY_STEPS)
    else:
        # Default: supplementary only (backwards-compatible)
        _run_pipeline("Supplementary", SUPPLEMENTARY_STEPS)

    if args.analyses:
        _run_analyses()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nPipeline aborted: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        sys.exit(1)