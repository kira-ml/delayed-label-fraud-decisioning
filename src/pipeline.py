"""Pipeline orchestration for the fraud decisioning project.

Single decision pipeline:
    load -> simulate_delay -> split -> train_compare -> evaluate_compare
    -> score -> decide -> backtest

Usage:
    python -m src.pipeline              # runs the pipeline
    python -m src.pipeline --list       # prints the step order and exits
    python -m src.pipeline --analyses   # runs calibration, sensitivity, bootstrap
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from typing import Callable

from src.data import load, simulate_delay, split
from src.models import train_compare, evaluate_compare, score
from src.policy import decide
from src.evaluation import backtest


PIPELINE_STEPS: list[tuple[str, Callable[[], None]]] = [
    ("load",             load.main),
    ("simulate_delay",   simulate_delay.main),
    ("split",            split.main),
    ("train_compare",    train_compare.main),
    ("evaluate_compare", evaluate_compare.main),
    ("score",            score.main),
    ("decide",           decide.main),
    ("backtest",         backtest.main),
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
    print("Pipeline steps:")
    for i, (name, _) in enumerate(PIPELINE_STEPS, 1):
        print(f"  {i}. {name}")


def _run_analyses() -> None:
    for module in (
        "src.evaluation.calibration",
        "src.evaluation.sensitivity",
        "src.evaluation.bootstrap",
    ):
        print("=" * 60)
        print(f"Analysis: {module}")
        print("=" * 60)
        subprocess.run([sys.executable, "-m", module], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the fraud decisioning pipeline."
    )
    parser.add_argument(
        "--list", action="store_true",
        help="print the step order and exit",
    )
    parser.add_argument(
        "--analyses", action="store_true",
        help="after the pipeline, also run calibration, sensitivity, and bootstrap",
    )
    args = parser.parse_args()

    if args.list:
        _print_list()
        return

    _run_pipeline("Pipeline", PIPELINE_STEPS)

    if args.analyses:
        _run_analyses()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nPipeline aborted: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        sys.exit(1)