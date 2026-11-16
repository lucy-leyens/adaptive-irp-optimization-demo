from __future__ import annotations

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_csv")
    args = parser.parse_args()

    df = pd.read_csv(args.trace_csv)
    plt.figure()
    plt.step(df["seconds"], df["best_objective"], where="post")
    plt.xlabel("Runtime [s]")
    plt.ylabel("Best objective")
    plt.title("Best objective over time")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
