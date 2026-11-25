from argparse import ArgumentParser
from pathlib import Path
from collections import Counter
import csv


CLARITY_MIN = 16.06225775

DARK_RATIO_MAX = 0.33113740

CONTRAST_CV_MAX = 0.63830344

FOV_AREA_MIN = 0.65079775
FOV_WIDTH_MIN = 0.91093100
FOV_HEIGHT_MIN = 0.90625000
FOV_CENTER_OFFSET_MAX = 0.00175000


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--quality-metrics",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--fov-metrics",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    with args.quality_metrics.open(
        encoding="utf-8",
        newline=""
    ) as file:
        quality_rows = list(
            csv.DictReader(file)
        )

    with args.fov_metrics.open(
        encoding="utf-8",
        newline=""
    ) as file:
        fov_rows = list(
            csv.DictReader(file)
        )

    fov_map = {}

    for row in fov_rows:
        key = (
            row["patient_id"],
            row["image_id"],
        )

        if key in fov_map:
            raise ValueError(
                f"FOV duplicado: {key}"
            )

        fov_map[key] = row

    tp = 0
    fn = 0
    tn = 0
    fp = 0

    criterion_failures = Counter()
    failure_combinations = Counter()

    criterion_failures_gt0 = Counter()
    criterion_failures_gt1 = Counter()

    results = []

    for row in quality_rows:
        if row.get(
            "error",
            ""
        ).strip():
            continue

        key = (
            row["patient_id"],
            row["image_id"],
        )

        if key not in fov_map:
            raise KeyError(
                f"Sin métricas FOV: {key}"
            )

        fov = fov_map[key]

        if fov.get(
            "error",
            ""
        ).strip():
            raise ValueError(
                f"Error FOV en {key}: "
                f"{fov['error']}"
            )

        overall_gt = int(
            row["overall_quality"]
        )

        clarity = float(
            row["clarity_gradient_p90"]
        )

        dark_ratio = float(
            row["dark_ratio_30"]
        )

        contrast_cv = float(
            row["contrast_cv"]
        )

        fov_area = float(
            fov["fov_area_ratio"]
        )

        fov_width = float(
            fov["fov_width_ratio"]
        )

        fov_height = float(
            fov["fov_height_ratio"]
        )

        fov_offset = float(
            fov["fov_center_offset"]
        )

        clarity_ok = (
            clarity >= CLARITY_MIN
        )

        illumination_ok = (
            dark_ratio <= DARK_RATIO_MAX
        )

        contrast_ok = (
            contrast_cv <= CONTRAST_CV_MAX
        )

        fov_ok = (
            fov_area >= FOV_AREA_MIN
            and fov_width >= FOV_WIDTH_MIN
            and fov_height >= FOV_HEIGHT_MIN
            and fov_offset
            <= FOV_CENTER_OFFSET_MAX
        )

        checks = {
            "clarity":
                clarity_ok,

            "illumination":
                illumination_ok,

            "contrast":
                contrast_ok,

            "fov":
                fov_ok,
        }

        failed = [
            name
            for name, passed
            in checks.items()
            if not passed
        ]

        for name in failed:
            criterion_failures[
                name
            ] += 1

            if overall_gt == 0:
                criterion_failures_gt0[
                    name
                ] += 1
            else:
                criterion_failures_gt1[
                    name
                ] += 1

        if failed:
            combination = "+".join(
                sorted(failed)
            )

            failure_combinations[
                combination
            ] += 1

        predicted = (
            1 if not failed else 0
        )

        if (
            overall_gt == 1
            and predicted == 1
        ):
            tp += 1

        elif (
            overall_gt == 1
            and predicted == 0
        ):
            fn += 1

        elif (
            overall_gt == 0
            and predicted == 0
        ):
            tn += 1

        elif (
            overall_gt == 0
            and predicted == 1
        ):
            fp += 1

        results.append({
            "patient_id":
                row["patient_id"],

            "image_id":
                row["image_id"],

            "overall_gt":
                overall_gt,

            "predicted_quality":
                predicted,

            "clarity_ok":
                int(clarity_ok),

            "illumination_ok":
                int(illumination_ok),

            "contrast_ok":
                int(contrast_ok),

            "fov_ok":
                int(fov_ok),

            "failed_criteria":
                ",".join(failed),
        })

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
    ) / (
        n0 + n1
    )

    false_accept_rate = (
        fp / n0
    )

    false_reject_rate = (
        fn / n1
    )

    print(
        "=== DeepDRiD Set-A — "
        "QUALITY GATE COMPLETO ==="
    )

    print(
        f"Observaciones: "
        f"{len(results)}"
    )

    print()

    print(
        "=== THRESHOLDS ==="
    )

    print(
        "clarity_gradient_p90 "
        f">= {CLARITY_MIN:.8f}"
    )

    print(
        "dark_ratio_30 "
        f"<= {DARK_RATIO_MAX:.8f}"
    )

    print(
        "contrast_cv "
        f"<= {CONTRAST_CV_MAX:.8f}"
    )

    print(
        "fov_area_ratio "
        f">= {FOV_AREA_MIN:.8f}"
    )

    print(
        "fov_width_ratio "
        f">= {FOV_WIDTH_MIN:.8f}"
    )

    print(
        "fov_height_ratio "
        f">= {FOV_HEIGHT_MIN:.8f}"
    )

    print(
        "fov_center_offset "
        f"<= {FOV_CENTER_OFFSET_MAX:.8f}"
    )

    print()

    print(
        "=== RESULTADO GLOBAL ==="
    )

    print(
        f"Accuracy: "
        f"{accuracy:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{balanced_accuracy:.4f}"
    )

    print(
        f"Recall SUFICIENTE: "
        f"{recall_sufficient:.4f}"
    )

    print(
        f"Recall INSUFICIENTE: "
        f"{recall_insufficient:.4f}"
    )

    print(
        f"False Accept Rate: "
        f"{false_accept_rate:.4f}"
    )

    print(
        f"False Reject Rate: "
        f"{false_reject_rate:.4f}"
    )

    print()

    print(
        "Matriz:"
    )

    print(
        f"TP={tp} | FN={fn} "
        f"| TN={tn} | FP={fp}"
    )

    print()

    print(
        "=== RECHAZOS POR CRITERIO ==="
    )

    for criterion in [
        "clarity",
        "illumination",
        "contrast",
        "fov",
    ]:
        print(
            f"{criterion}: "
            f"{criterion_failures[criterion]} "
            f"| GT=0: "
            f"{criterion_failures_gt0[criterion]} "
            f"| GT=1: "
            f"{criterion_failures_gt1[criterion]}"
        )

    print()

    print(
        "=== COMBINACIONES DE FALLO ==="
    )

    for combination, count in (
        failure_combinations.most_common()
    ):
        print(
            f"{combination}: {count}"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "patient_id",
        "image_id",
        "overall_gt",
        "predicted_quality",
        "clarity_ok",
        "illumination_ok",
        "contrast_ok",
        "fov_ok",
        "failed_criteria",
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
            results
        )

    print()

    print(
        f"Resultado: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
