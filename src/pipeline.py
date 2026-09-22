"""Supplementary pipeline orchestration.

Runs: load -> simulate_delay -> split -> train_baseline -> score -> decide -> backtest
"""
from src.data import load, simulate_delay, split
from src.models import train_baseline, score
from src.policy import decide
from src.evaluation import backtest


def main() -> None:
    print("=" * 60)
    print("Supplementary Pipeline")
    print("=" * 60)

    steps = [
        ("load",           load.main),
        ("simulate_delay", simulate_delay.main),
        ("split",          split.main),
        ("train_baseline", train_baseline.main),
        ("score",          score.main),
        ("decide",         decide.main),
        ("backtest",       backtest.main),
    ]
    for i, (name, fn) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {name}")
        fn()

    print("\n=== Supplementary pipeline complete ===")


if __name__ == "__main__":
    main()