from src.data import load, simulate_delay, split
from src.models import train_baseline, score
from src.policy import decide
from src.evaluation import backtest


STEPS = [
    ("load", load.run),
    ("simulate_delay", simulate_delay.run),
    ("split", split.run),
    ("train_baseline", train_baseline.run),
    ("score", score.run),
    ("decide", decide.run),
    ("backtest", backtest.main),
]


def main():
    for i, (name, fn) in enumerate(STEPS, 1):
        print(f"\n=== [{i}/{len(STEPS)}] {name} ===")
        fn()
    print("\nPipeline complete. See reports/mvp_backtest.md")


if __name__ == "__main__":
    main()