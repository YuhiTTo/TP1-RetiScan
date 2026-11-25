from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np


TARGET_METRICS = {
    "illumination": [
        "luminance_mean",
        "luminance_median",
        "luminance_p05",
        "luminance_p95",
        "dark_ratio_30",
        "bright_ratio_225",
    ],
    "contrast": [
        "contrast_std",
        "contrast_iqr",
        "contrast_p90_range",
        "contrast_cv",
    ],
    "clarity": [
        "clarity_laplacian",
    ],
}


def average_ranks(values):
    values = np.asarray(
        values,
        dtype=float
    )

    order = np.argsort(
        values,
        kind="mergesort"
    )

    sorted_values = values[
        order
    ]

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


def auc_binary(
    labels,
    scores
):
    labels = np.asarray(
        labels,
        dtype=int
    )

    scores = np.asarray(
        scores,
        dtype=float
    )

    positive = (
        labels == 1
    )

    negative = (
        labels == 0
    )

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


def summarize_group(
    rows,
    target,
    metric
):
    clean = []

    for row in rows:
        try:
            gt = int(
                row[f"{target}_gt"]
            )

            value = float(
                row[metric]
            )

        except (
            ValueError,
            TypeError,
            KeyError
        ):
            continue

        if (
            gt in {0, 1}
            and np.isfinite(value)
        ):
            clean.append(
                (gt, value)
            )

    if not clean:
        return None

    labels = np.array(
        [
            item[0]
            for item in clean
        ],
        dtype=int
    )

    values = np.array(
        [
            item[1]
            for item in clean
        ],
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
        return {
            "n": len(values),
            "n0": len(values_0),
            "n1": len(values_1),
            "median_0": (
                float(
                    np.median(values_0)
                )
                if len(values_0)
                else None
            ),
            "median_1": (
                float(
                    np.median(values_1)
                )
                if len(values_1)
                else None
            ),
            "q25_0": None,
            "q75_0": None,
            "q25_1": None,
            "q75_1": None,
            "auc_raw": None,
            "auc_separation": None,
            "direction": "UNDEFINED",
            "cliffs_delta": None,
        }

    auc_raw = auc_binary(
        labels,
        values
    )

    if auc_raw >= 0.5:
        direction = "HIGHER_IS_1"
        auc_separation = auc_raw
    else:
        direction = "LOWER_IS_1"
        auc_separation = (
            1.0 - auc_raw
        )

    cliffs_delta = (
        2.0 * auc_raw - 1.0
    )

    return {
        "n": len(values),
        "n0": len(values_0),
        "n1": len(values_1),

        "median_0": float(
            np.median(values_0)
        ),
        "median_1": float(
            np.median(values_1)
        ),

        "q25_0": float(
            np.percentile(
                values_0,
                25
            )
        ),
        "q75_0": float(
            np.percentile(
                values_0,
                75
            )
        ),

        "q25_1": float(
            np.percentile(
                values_1,
                25
            )
        ),
        "q75_1": float(
            np.percentile(
                values_1,
                75
            )
        ),

        "auc_raw": auc_raw,
        "auc_separation":
            auc_separation,
        "direction": direction,
        "cliffs_delta":
            cliffs_delta,
    }


def fmt(value):
    if value is None:
        return "NA"

    return f"{value:.6f}"


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output-csv",
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

    analysis_groups = [
        ("ALL", rows)
    ]

    for subset in subsets:
        subset_rows = [
            row
            for row in rows
            if row["subset"]
            == subset
        ]

        analysis_groups.append(
            (
                subset,
                subset_rows
            )
        )

    output_rows = []

    print(
        "=== MSHF — ANÁLISIS DE "
        "MÉTRICAS DE CALIDAD ==="
    )

    for target, metrics in (
        TARGET_METRICS.items()
    ):
        print(
            "\n"
            + "=" * 72
        )
        print(
            f"TARGET: "
            f"{target.upper()}"
        )
        print(
            "=" * 72
        )

        for group_name, group_rows in (
            analysis_groups
        ):
            print(
                f"\n--- {group_name} ---"
            )

            for metric in metrics:
                summary = (
                    summarize_group(
                        group_rows,
                        target,
                        metric
                    )
                )

                if summary is None:
                    continue

                print(
                    f"\n{metric}"
                )

                print(
                    f"  n0={summary['n0']} "
                    f"| n1={summary['n1']}"
                )

                print(
                    "  GT=0 mediana="
                    f"{fmt(summary['median_0'])}"
                    " | GT=1 mediana="
                    f"{fmt(summary['median_1'])}"
                )

                if (
                    summary[
                        "auc_separation"
                    ]
                    is not None
                ):
                    print(
                        "  AUC separación="
                        f"{summary['auc_separation']:.4f}"
                        " | dirección="
                        f"{summary['direction']}"
                        " | delta="
                        f"{summary['cliffs_delta']:.4f}"
                    )

                else:
                    print(
                        "  AUC: no calculable "
                        "(una sola clase)"
                    )

                output_rows.append({
                    "target": target,
                    "group": group_name,
                    "metric": metric,
                    "n": summary["n"],
                    "n0": summary["n0"],
                    "n1": summary["n1"],
                    "median_0":
                        fmt(
                            summary[
                                "median_0"
                            ]
                        ),
                    "q25_0":
                        fmt(
                            summary[
                                "q25_0"
                            ]
                        ),
                    "q75_0":
                        fmt(
                            summary[
                                "q75_0"
                            ]
                        ),
                    "median_1":
                        fmt(
                            summary[
                                "median_1"
                            ]
                        ),
                    "q25_1":
                        fmt(
                            summary[
                                "q25_1"
                            ]
                        ),
                    "q75_1":
                        fmt(
                            summary[
                                "q75_1"
                            ]
                        ),
                    "auc_raw":
                        fmt(
                            summary[
                                "auc_raw"
                            ]
                        ),
                    "auc_separation":
                        fmt(
                            summary[
                                "auc_separation"
                            ]
                        ),
                    "direction":
                        summary[
                            "direction"
                        ],
                    "cliffs_delta":
                        fmt(
                            summary[
                                "cliffs_delta"
                            ]
                        ),
                })

    args.output_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "target",
        "group",
        "metric",
        "n",
        "n0",
        "n1",
        "median_0",
        "q25_0",
        "q75_0",
        "median_1",
        "q25_1",
        "q75_1",
        "auc_raw",
        "auc_separation",
        "direction",
        "cliffs_delta",
    ]

    with args.output_csv.open(
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
        f"Resultado: "
        f"{args.output_csv}"
    )


if __name__ == "__main__":
    main()
