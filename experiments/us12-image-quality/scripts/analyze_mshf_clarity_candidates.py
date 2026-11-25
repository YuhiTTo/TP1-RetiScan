from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np


METRICS = [
    "clarity_laplacian",
    "clarity_laplacian_norm",
    "clarity_tenengrad",
    "clarity_tenengrad_norm",
    "clarity_gradient_p90",
    "clarity_gradient_p90_norm",
]


def average_ranks(values):
    values = np.asarray(values, dtype=float)

    order = np.argsort(
        values,
        kind="mergesort"
    )

    sorted_values = values[order]

    ranks = np.empty(
        len(values),
        dtype=float
    )

    i = 0

    while i < len(values):
        j = i + 1

        while (
            j < len(values)
            and sorted_values[j]
            == sorted_values[i]
        ):
            j += 1

        average_rank = (
            (i + 1) + j
        ) / 2.0

        ranks[
            order[i:j]
        ] = average_rank

        i = j

    return ranks


def auc_binary(labels, scores):
    labels = np.asarray(
        labels,
        dtype=int
    )

    scores = np.asarray(
        scores,
        dtype=float
    )

    positive = labels == 1
    negative = labels == 0

    n1 = int(
        np.sum(positive)
    )

    n0 = int(
        np.sum(negative)
    )

    if n0 == 0 or n1 == 0:
        return None

    ranks = average_ranks(
        scores
    )

    rank_sum_positive = float(
        np.sum(
            ranks[positive]
        )
    )

    u = (
        rank_sum_positive
        - n1 * (n1 + 1) / 2
    )

    return float(
        u / (n0 * n1)
    )


def analyze(rows, metric):
    labels = []
    values = []

    for row in rows:
        try:
            gt = int(
                row["clarity_gt"]
            )

            value = float(
                row[metric]
            )

        except (
            KeyError,
            ValueError,
            TypeError
        ):
            continue

        if (
            gt in {0, 1}
            and np.isfinite(value)
        ):
            labels.append(gt)
            values.append(value)

    labels = np.asarray(
        labels,
        dtype=int
    )

    values = np.asarray(
        values,
        dtype=float
    )

    values_0 = values[
        labels == 0
    ]

    values_1 = values[
        labels == 1
    ]

    if (
        len(values_0) == 0
        or len(values_1) == 0
    ):
        return None

    auc_raw = auc_binary(
        labels,
        values
    )

    if auc_raw >= 0.5:
        direction = "HIGHER_IS_1"
        auc_sep = auc_raw
    else:
        direction = "LOWER_IS_1"
        auc_sep = 1.0 - auc_raw

    delta = (
        2.0 * auc_raw - 1.0
    )

    return {
        "n0": len(values_0),
        "n1": len(values_1),

        "median_0": float(
            np.median(values_0)
        ),

        "median_1": float(
            np.median(values_1)
        ),

        "auc_raw": auc_raw,
        "auc_separation": auc_sep,
        "direction": direction,
        "cliffs_delta": delta,
    }


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    with args.input.open(
        encoding="utf-8",
        newline=""
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    subsets = sorted(
        {
            row["subset"]
            for row in rows
        }
    )

    groups = [
        ("ALL", rows)
    ]

    for subset in subsets:
        groups.append(
            (
                subset,
                [
                    row
                    for row in rows
                    if row["subset"]
                    == subset
                ]
            )
        )

    output_rows = []

    print(
        "=== MSHF — COMPARACIÓN "
        "DE MÉTRICAS DE CLARIDAD ==="
    )

    for group_name, group_rows in groups:
        print(
            "\n"
            + "=" * 72
        )

        print(
            f"GRUPO: {group_name}"
        )

        print(
            "=" * 72
        )

        for metric in METRICS:
            result = analyze(
                group_rows,
                metric
            )

            print(
                f"\n{metric}"
            )

            if result is None:
                print(
                    "  No calculable "
                    "(una sola clase)"
                )

                output_rows.append({
                    "group": group_name,
                    "metric": metric,
                    "n0": "",
                    "n1": "",
                    "median_0": "",
                    "median_1": "",
                    "auc_raw": "",
                    "auc_separation": "",
                    "direction": "UNDEFINED",
                    "cliffs_delta": "",
                })

                continue

            print(
                f"  n0={result['n0']} "
                f"| n1={result['n1']}"
            )

            print(
                "  GT=0 mediana="
                f"{result['median_0']:.8f}"
                " | GT=1 mediana="
                f"{result['median_1']:.8f}"
            )

            print(
                "  AUC separación="
                f"{result['auc_separation']:.4f}"
                " | dirección="
                f"{result['direction']}"
                " | delta="
                f"{result['cliffs_delta']:.4f}"
            )

            output_rows.append({
                "group": group_name,
                "metric": metric,
                "n0": result["n0"],
                "n1": result["n1"],
                "median_0":
                    f"{result['median_0']:.8f}",
                "median_1":
                    f"{result['median_1']:.8f}",
                "auc_raw":
                    f"{result['auc_raw']:.8f}",
                "auc_separation":
                    f"{result['auc_separation']:.8f}",
                "direction":
                    result["direction"],
                "cliffs_delta":
                    f"{result['cliffs_delta']:.8f}",
            })

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "group",
        "metric",
        "n0",
        "n1",
        "median_0",
        "median_1",
        "auc_raw",
        "auc_separation",
        "direction",
        "cliffs_delta",
    ]

    with args.output.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(
            output_rows
        )

    print()
    print(
        f"Resultado: {args.output}"
    )


if __name__ == "__main__":
    main()
