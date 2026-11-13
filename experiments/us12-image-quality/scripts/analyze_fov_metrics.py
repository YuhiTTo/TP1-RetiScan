from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import csv
import statistics

from scipy.stats import spearmanr


METRICS = [
    "fov_area_ratio",
    "fov_width_ratio",
    "fov_height_ratio",
    "fov_center_offset",
]


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

    with args.input.open(
        encoding="utf-8",
        newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    valid_rows = [
        row for row in rows
        if not row["error"]
    ]

    print(
        f"\nImágenes válidas: "
        f"{len(valid_rows)}"
    )

    print("\n=== DISTRIBUCIÓN POR FIELD DEFINITION ===")

    by_field = defaultdict(list)

    for row in valid_rows:
        by_field[
            row["field_definition_gt"]
        ].append(row)

    for level in sorted(
        by_field,
        key=float
    ):
        print(
            f"\nField definition {level} "
            f"(n={len(by_field[level])})"
        )

        for metric in METRICS:

            values = [
                float(row[metric])
                for row in by_field[level]
            ]

            stats = summarize(values)

            print(
                f"  {metric}: "
                f"median={stats['median']:.6f} | "
                f"mean={stats['mean']:.6f} | "
                f"min={stats['min']:.6f} | "
                f"max={stats['max']:.6f}"
            )

    print("\n=== CORRELACIÓN SPEARMAN ===")

    field_values = [
        float(row["field_definition_gt"])
        for row in valid_rows
    ]

    for metric in METRICS:

        metric_values = [
            float(row[metric])
            for row in valid_rows
        ]

        rho, p_value = spearmanr(
            field_values,
            metric_values
        )

        print(
            f"{metric}: "
            f"rho={rho:.6f} | "
            f"p-value={p_value:.6e}"
        )


if __name__ == "__main__":
    main()
