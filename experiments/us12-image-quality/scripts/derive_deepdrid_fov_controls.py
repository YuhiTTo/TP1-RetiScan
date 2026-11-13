from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np


LOWER_METRICS = [
    "fov_area_ratio",
    "fov_width_ratio",
    "fov_height_ratio",
]

UPPER_METRIC = "fov_center_offset"

QUANTILES = [
    0.5,
    1.0,
    2.5,
    5.0,
]


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
        rows = [
            row
            for row in csv.DictReader(file)
            if not row.get(
                "error",
                ""
            ).strip()
        ]

    sufficient = [
        row
        for row in rows
        if int(
            row["overall_quality"]
        ) == 1
    ]

    insufficient = [
        row
        for row in rows
        if int(
            row["overall_quality"]
        ) == 0
    ]

    print(
        "=== DeepDRiD Set-A — "
        "CONTROLES TÉCNICOS FOV ==="
    )

    print(
        f"Observaciones válidas: "
        f"{len(rows)}"
    )

    print(
        f"Overall suficiente: "
        f"{len(sufficient)}"
    )

    print(
        f"Overall insuficiente: "
        f"{len(insufficient)}"
    )

    def values(data, metric):
        return np.asarray(
            [
                float(row[metric])
                for row in data
            ],
            dtype=float
        )

    print(
        "\n=== DISTRIBUCIÓN EN "
        "IMÁGENES SUFICIENTES ==="
    )

    for metric in (
        LOWER_METRICS
        + [UPPER_METRIC]
    ):
        data = values(
            sufficient,
            metric
        )

        print()
        print(metric)

        print(
            f"  min={np.min(data):.8f}"
        )

        print(
            f"  P0.5="
            f"{np.percentile(data, 0.5):.8f}"
        )

        print(
            f"  P1="
            f"{np.percentile(data, 1):.8f}"
        )

        print(
            f"  P2.5="
            f"{np.percentile(data, 2.5):.8f}"
        )

        print(
            f"  P5="
            f"{np.percentile(data, 5):.8f}"
        )

        print(
            f"  mediana="
            f"{np.median(data):.8f}"
        )

        print(
            f"  P95="
            f"{np.percentile(data, 95):.8f}"
        )

        print(
            f"  P97.5="
            f"{np.percentile(data, 97.5):.8f}"
        )

        print(
            f"  P99="
            f"{np.percentile(data, 99):.8f}"
        )

        print(
            f"  P99.5="
            f"{np.percentile(data, 99.5):.8f}"
        )

        print(
            f"  max={np.max(data):.8f}"
        )

    output_rows = []

    print(
        "\n=== REGLAS FOV CONJUNTAS ==="
    )

    for q in QUANTILES:
        thresholds = {}

        for metric in LOWER_METRICS:
            thresholds[metric] = float(
                np.percentile(
                    values(
                        sufficient,
                        metric
                    ),
                    q
                )
            )

        thresholds[
            UPPER_METRIC
        ] = float(
            np.percentile(
                values(
                    sufficient,
                    UPPER_METRIC
                ),
                100.0 - q
            )
        )

        def fails_fov(row):
            for metric in LOWER_METRICS:
                if (
                    float(row[metric])
                    < thresholds[metric]
                ):
                    return True

            if (
                float(
                    row[UPPER_METRIC]
                )
                > thresholds[
                    UPPER_METRIC
                ]
            ):
                return True

            return False

        sufficient_rejected = sum(
            fails_fov(row)
            for row in sufficient
        )

        insufficient_rejected = sum(
            fails_fov(row)
            for row in insufficient
        )

        sufficient_rate = (
            sufficient_rejected
            / len(sufficient)
        )

        insufficient_rate = (
            insufficient_rejected
            / len(insufficient)
        )

        print()
        print(
            f"Nivel extremo: {q:g}%"
        )

        for metric in LOWER_METRICS:
            print(
                f"  {metric} >= "
                f"{thresholds[metric]:.8f}"
            )

        print(
            f"  {UPPER_METRIC} <= "
            f"{thresholds[UPPER_METRIC]:.8f}"
        )

        print(
            f"  Rechazo Overall=1: "
            f"{sufficient_rejected}/"
            f"{len(sufficient)} "
            f"({sufficient_rate*100:.2f}%)"
        )

        print(
            f"  Rechazo Overall=0: "
            f"{insufficient_rejected}/"
            f"{len(insufficient)} "
            f"({insufficient_rate*100:.2f}%)"
        )

        output_rows.append({
            "extreme_percent":
                q,

            "fov_area_ratio_min":
                f"{thresholds['fov_area_ratio']:.8f}",

            "fov_width_ratio_min":
                f"{thresholds['fov_width_ratio']:.8f}",

            "fov_height_ratio_min":
                f"{thresholds['fov_height_ratio']:.8f}",

            "fov_center_offset_max":
                f"{thresholds['fov_center_offset']:.8f}",

            "sufficient_rejected":
                sufficient_rejected,

            "sufficient_reject_rate":
                f"{sufficient_rate:.8f}",

            "insufficient_rejected":
                insufficient_rejected,

            "insufficient_reject_rate":
                f"{insufficient_rate:.8f}",
        })

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "extreme_percent",
        "fov_area_ratio_min",
        "fov_width_ratio_min",
        "fov_height_ratio_min",
        "fov_center_offset_max",
        "sufficient_rejected",
        "sufficient_reject_rate",
        "insufficient_rejected",
        "insufficient_reject_rate",
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
