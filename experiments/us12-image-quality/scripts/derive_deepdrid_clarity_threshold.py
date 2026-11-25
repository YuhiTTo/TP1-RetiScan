from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np

from derive_deepdrid_set_a_thresholds import (
    auc_binary,
    choose_best,
)


CLARITY_MIN_SCORE = 8


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

    clarity_scores = []
    values = []

    for row in rows:
        try:
            clarity = int(
                float(row["clarity_gt"])
            )

            value = float(
                row["clarity_gradient_p90"]
            )

        except (
            ValueError,
            TypeError,
            KeyError
        ):
            continue

        clarity_scores.append(
            clarity
        )

        values.append(
            value
        )

    clarity_scores = np.asarray(
        clarity_scores,
        dtype=int
    )

    values = np.asarray(
        values,
        dtype=float
    )

    # Ground truth operacional:
    # 0 = claridad insuficiente: 1, 4, 6
    # 1 = claridad suficiente: 8, 10
    labels = (
        clarity_scores
        >= CLARITY_MIN_SCORE
    ).astype(int)

    n0 = int(
        np.sum(labels == 0)
    )

    n1 = int(
        np.sum(labels == 1)
    )

    raw_auc = auc_binary(
        labels,
        values
    )

    best = choose_best(
        labels,
        values,
        "HIGHER_IS_1"
    )

    values_0 = values[
        labels == 0
    ]

    values_1 = values[
        labels == 1
    ]

    print(
        "=== DeepDRiD Set-A — "
        "THRESHOLD DE CLARIDAD ==="
    )

    print(
        f"Criterio experto: "
        f"Clarity >= {CLARITY_MIN_SCORE}"
    )

    print(
        f"Claridad insuficiente: {n0}"
    )

    print(
        f"Claridad suficiente: {n1}"
    )

    print()

    print(
        "Mediana Gradient P90 "
        f"insuficiente: "
        f"{np.median(values_0):.8f}"
    )

    print(
        "Mediana Gradient P90 "
        f"suficiente: "
        f"{np.median(values_1):.8f}"
    )

    print(
        f"AUC: {raw_auc:.4f}"
    )

    print()

    print(
        f"Threshold candidato: "
        f"{best['threshold']:.8f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{best['balanced_accuracy']:.4f}"
    )

    print(
        f"Recall claridad suficiente: "
        f"{best['recall_sufficient']:.4f}"
    )

    print(
        f"Recall claridad insuficiente: "
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

    print()

    print(
        f"TP={best['tp']} "
        f"| FN={best['fn']} "
        f"| TN={best['tn']} "
        f"| FP={best['fp']}"
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "clarity_min_score",
        "metric",
        "direction",
        "n_insufficient",
        "n_sufficient",
        "auc",
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

    result = {
        "clarity_min_score":
            CLARITY_MIN_SCORE,

        "metric":
            "clarity_gradient_p90",

        "direction":
            "HIGHER_IS_1",

        "n_insufficient":
            n0,

        "n_sufficient":
            n1,

        "auc":
            f"{raw_auc:.8f}",

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
    }

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
        writer.writerow(
            result
        )

    print()
    print(
        f"Resultado: {args.output}"
    )


if __name__ == "__main__":
    main()
