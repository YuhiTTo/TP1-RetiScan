from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import csv
import statistics

from scipy.stats import spearmanr


def summarize(values):
    values = sorted(values)

    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    by_clarity = defaultdict(list)
    by_quality = defaultdict(list)

    clarity_gt_values = []
    laplacian_values = []

    with args.input.open(
        encoding="utf-8",
        newline=""
    ) as file:

        rows = list(csv.DictReader(file))

    valid_rows = [
        row for row in rows
        if row["clarity_laplacian"]
        and not row["error"]
    ]

    for row in valid_rows:

        value = float(
            row["clarity_laplacian"]
        )

        clarity_gt = float(
            row["clarity_gt"]
        )

        by_clarity[
            row["clarity_gt"]
        ].append(value)

        by_quality[
            row["overall_quality"]
        ].append(value)

        clarity_gt_values.append(
            clarity_gt
        )

        laplacian_values.append(
            value
        )

    print("\n=== CLARITY GT ===")

    for level in sorted(
        by_clarity,
        key=float
    ):

        stats = summarize(
            by_clarity[level]
        )

        print(
            f"Clarity {level}: "
            f"n={stats['n']} | "
            f"mean={stats['mean']:.2f} | "
            f"median={stats['median']:.2f} | "
            f"min={stats['min']:.2f} | "
            f"max={stats['max']:.2f}"
        )

    print("\n=== OVERALL QUALITY ===")

    for quality in sorted(
        by_quality
    ):

        label = (
            "INSUFICIENTE"
            if quality == "0"
            else "SUFICIENTE"
        )

        stats = summarize(
            by_quality[quality]
        )

        print(
            f"{label}: "
            f"n={stats['n']} | "
            f"mean={stats['mean']:.2f} | "
            f"median={stats['median']:.2f} | "
            f"min={stats['min']:.2f} | "
            f"max={stats['max']:.2f}"
        )

    rho, p_value = spearmanr(
        clarity_gt_values,
        laplacian_values
    )

    print("\n=== CORRELACIÓN SPEARMAN ===")

    print(
        f"rho = {rho:.6f}"
    )

    print(
        f"p-value = {p_value:.6e}"
    )


if __name__ == "__main__":
    main()
