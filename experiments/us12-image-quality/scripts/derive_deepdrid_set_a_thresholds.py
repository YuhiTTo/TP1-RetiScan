from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np


METRICS = {
    "clarity_gradient_p90": "HIGHER_IS_1",
    "dark_ratio_30": "LOWER_IS_1",
    "contrast_cv": "LOWER_IS_1",
}


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

        ranks[
            order[i:j]
        ] = (
            (i + 1) + j
        ) / 2.0

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

    n1 = int(
        np.sum(labels == 1)
    )

    n0 = int(
        np.sum(labels == 0)
    )

    ranks = average_ranks(
        scores
    )

    rank_sum_positive = float(
        np.sum(
            ranks[labels == 1]
        )
    )

    u = (
        rank_sum_positive
        - n1 * (n1 + 1) / 2
    )

    return float(
        u / (n0 * n1)
    )


def candidate_thresholds(values):
    unique = np.unique(
        np.asarray(
            values,
            dtype=float
        )
    )

    if len(unique) == 1:
        return unique

    midpoints = (
        unique[:-1]
        + unique[1:]
    ) / 2.0

    lower = np.nextafter(
        unique[0],
        -np.inf
    )

    upper = np.nextafter(
        unique[-1],
        np.inf
    )

    return np.concatenate(
        (
            [lower],
            midpoints,
            [upper],
        )
    )


def evaluate_threshold(
    labels,
    values,
    threshold,
    direction
):
    labels = np.asarray(
        labels,
        dtype=int
    )

    values = np.asarray(
        values,
        dtype=float
    )

    if direction == "HIGHER_IS_1":
        prediction = (
            values >= threshold
        ).astype(int)

    elif direction == "LOWER_IS_1":
        prediction = (
            values <= threshold
        ).astype(int)

    else:
        raise ValueError(
            f"Dirección desconocida: "
            f"{direction}"
        )

    actual_sufficient = (
        labels == 1
    )

    actual_insufficient = (
        labels == 0
    )

    predicted_sufficient = (
        prediction == 1
    )

    predicted_insufficient = (
        prediction == 0
    )

    tp = int(
        np.sum(
            actual_sufficient
            & predicted_sufficient
        )
    )

    fn = int(
        np.sum(
            actual_sufficient
            & predicted_insufficient
        )
    )

    tn = int(
        np.sum(
            actual_insufficient
            & predicted_insufficient
        )
    )

    fp = int(
        np.sum(
            actual_insufficient
            & predicted_sufficient
        )
    )

    n1 = tp + fn
    n0 = tn + fp

    recall_sufficient = (
        tp / n1
    )

    recall_insufficient = (
        tn / n0
    )

    balanced_accuracy = (
        recall_sufficient
        + recall_insufficient
    ) / 2.0

    accuracy = (
        tp + tn
    ) / len(labels)

    false_accept_rate = (
        fp / n0
    )

    false_reject_rate = (
        fn / n1
    )

    return {
        "threshold": float(
            threshold
        ),
        "tp": tp,
        "fn": fn,
        "tn": tn,
        "fp": fp,
        "recall_sufficient":
            recall_sufficient,
        "recall_insufficient":
            recall_insufficient,
        "balanced_accuracy":
            balanced_accuracy,
        "accuracy":
            accuracy,
        "false_accept_rate":
            false_accept_rate,
        "false_reject_rate":
            false_reject_rate,
    }


def choose_best(
    labels,
    values,
    direction
):
    best = None

    for threshold in (
        candidate_thresholds(values)
    ):
        result = evaluate_threshold(
            labels,
            values,
            threshold,
            direction
        )

        if best is None:
            best = result
            continue

        # Criterio principal:
        # máxima Balanced Accuracy.
        #
        # En caso de empate numérico:
        # 1. menor aceptación errónea
        #    de imágenes insuficientes;
        # 2. menor rechazo erróneo
        #    de imágenes suficientes.
        current_key = (
            round(
                result[
                    "balanced_accuracy"
                ],
                12
            ),
            -result[
                "false_accept_rate"
            ],
            -result[
                "false_reject_rate"
            ],
        )

        best_key = (
            round(
                best[
                    "balanced_accuracy"
                ],
                12
            ),
            -best[
                "false_accept_rate"
            ],
            -best[
                "false_reject_rate"
            ],
        )

        if current_key > best_key:
            best = result

    return best


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

    valid_rows = [
        row
        for row in rows
        if not row.get(
            "error",
            ""
        ).strip()
    ]

    labels = np.asarray(
        [
            int(
                row["overall_quality"]
            )
            for row in valid_rows
        ],
        dtype=int
    )

    n0 = int(
        np.sum(labels == 0)
    )

    n1 = int(
        np.sum(labels == 1)
    )

    print(
        "=== DeepDRiD Set-A — "
        "DERIVACIÓN DE THRESHOLDS ==="
    )

    print(
        f"Observaciones válidas: "
        f"{len(labels)}"
    )

    print(
        f"Overall=0 INSUFICIENTE: {n0}"
    )

    print(
        f"Overall=1 SUFICIENTE: {n1}"
    )

    output_rows = []

    for metric, direction in (
        METRICS.items()
    ):
        values = np.asarray(
            [
                float(
                    row[metric]
                )
                for row in valid_rows
            ],
            dtype=float
        )

        raw_auc = auc_binary(
            labels,
            values
        )

        separation_auc = max(
            raw_auc,
            1.0 - raw_auc
        )

        values_0 = values[
            labels == 0
        ]

        values_1 = values[
            labels == 1
        ]

        best = choose_best(
            labels,
            values,
            direction
        )

        print()
        print(
            "=" * 72
        )

        print(
            f"MÉTRICA: {metric}"
        )

        print(
            f"Dirección: {direction}"
        )

        print(
            f"GT=0 mediana: "
            f"{np.median(values_0):.8f}"
        )

        print(
            f"GT=1 mediana: "
            f"{np.median(values_1):.8f}"
        )

        print(
            f"AUC separación: "
            f"{separation_auc:.4f}"
        )

        print(
            f"Threshold candidato: "
            f"{best['threshold']:.8f}"
        )

        print(
            f"Balanced Accuracy: "
            f"{best['balanced_accuracy']:.4f}"
        )

        print(
            f"Recall SUFICIENTE: "
            f"{best['recall_sufficient']:.4f}"
        )

        print(
            f"Recall INSUFICIENTE: "
            f"{best['recall_insufficient']:.4f}"
        )

        print(
            f"False Accept Rate: "
            f"{best['false_accept_rate']:.4f}"
        )

        print(
            f"False Reject Rate: "
            f"{best['false_reject_rate']:.4f}"
        )

        print(
            "Matriz "
            "[GT suficiente / insuficiente]:"
        )

        print(
            f"  TP={best['tp']} "
            f"| FN={best['fn']} "
            f"| TN={best['tn']} "
            f"| FP={best['fp']}"
        )

        output_rows.append({
            "metric":
                metric,

            "direction":
                direction,

            "n_insufficient":
                n0,

            "n_sufficient":
                n1,

            "median_insufficient":
                f"{np.median(values_0):.8f}",

            "median_sufficient":
                f"{np.median(values_1):.8f}",

            "auc_raw":
                f"{raw_auc:.8f}",

            "auc_separation":
                f"{separation_auc:.8f}",

            "threshold_candidate":
                f"{best['threshold']:.8f}",

            "balanced_accuracy":
                f"{best['balanced_accuracy']:.8f}",

            "recall_sufficient":
                f"{best['recall_sufficient']:.8f}",

            "recall_insufficient":
                f"{best['recall_insufficient']:.8f}",

            "false_accept_rate":
                f"{best['false_accept_rate']:.8f}",

            "false_reject_rate":
                f"{best['false_reject_rate']:.8f}",

            "tp":
                best["tp"],

            "fn":
                best["fn"],

            "tn":
                best["tn"],

            "fp":
                best["fp"],
        })

    args.output_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "metric",
        "direction",
        "n_insufficient",
        "n_sufficient",
        "median_insufficient",
        "median_sufficient",
        "auc_raw",
        "auc_separation",
        "threshold_candidate",
        "balanced_accuracy",
        "recall_sufficient",
        "recall_insufficient",
        "false_accept_rate",
        "false_reject_rate",
        "tp",
        "fn",
        "tn",
        "fp",
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
        "IMPORTANTE: estos thresholds "
        "son candidatos derivados de Set-A; "
        "todavía NO son thresholds finales."
    )

    print(
        f"Resultado: "
        f"{args.output_csv}"
    )


if __name__ == "__main__":
    main()
