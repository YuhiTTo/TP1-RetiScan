from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import csv


# ============================================================
# THRESHOLDS CONGELADOS EN SET-A
# NO MODIFICAR UTILIZANDO SET-B
# ============================================================

CLARITY_MIN = 16.06225775

DARK_RATIO_MAX = 0.33113740
CONTRAST_CV_MAX = 0.63830344

FOV_AREA_MIN = 0.65079775
FOV_WIDTH_MIN = 0.91093100
FOV_HEIGHT_MIN = 0.90625000
FOV_CENTER_OFFSET_MAX = 0.00175000

CLARITY_GT_MIN = 8


def calculate_metrics(tp, fn, tn, fp):
    positive = tp + fn
    negative = tn + fp

    recall_positive = (
        tp / positive
        if positive
        else 0.0
    )

    recall_negative = (
        tn / negative
        if negative
        else 0.0
    )

    balanced_accuracy = (
        recall_positive
        + recall_negative
    ) / 2.0

    accuracy = (
        (tp + tn)
        / (positive + negative)
    )

    false_accept_rate = (
        fp / negative
        if negative
        else 0.0
    )

    false_reject_rate = (
        fn / positive
        if positive
        else 0.0
    )

    return {
        "accuracy":
            accuracy,

        "balanced_accuracy":
            balanced_accuracy,

        "recall_positive":
            recall_positive,

        "recall_negative":
            recall_negative,

        "false_accept_rate":
            false_accept_rate,

        "false_reject_rate":
            false_reject_rate,
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
        rows = [
            row
            for row in csv.DictReader(file)
            if not row.get(
                "error",
                ""
            ).strip()
        ]

    # ========================================================
    # 1. VALIDACIÓN ESPECÍFICA DEL CRITERIO DE CLARIDAD
    # ========================================================

    clarity_tp = 0
    clarity_fn = 0
    clarity_tn = 0
    clarity_fp = 0

    # ========================================================
    # 2. VALIDACIÓN DEL GATE COMPLETO CONTRA OVERALL
    # ========================================================

    tp = 0
    fn = 0
    tn = 0
    fp = 0

    criterion_failures = Counter()
    failure_combinations = Counter()

    failures_gt0 = Counter()
    failures_gt1 = Counter()

    results = []

    for row in rows:
        overall_gt = int(
            row["overall_quality"]
        )

        clarity_gt = int(
            float(
                row["clarity_gt"]
            )
        )

        clarity_value = float(
            row["clarity_gradient_p90"]
        )

        dark_ratio = float(
            row["dark_ratio_30"]
        )

        contrast_cv = float(
            row["contrast_cv"]
        )

        fov_area = float(
            row["fov_area_ratio"]
        )

        fov_width = float(
            row["fov_width_ratio"]
        )

        fov_height = float(
            row["fov_height_ratio"]
        )

        fov_offset = float(
            row["fov_center_offset"]
        )

        # ----------------------------------------------------
        # CLARIDAD
        # ----------------------------------------------------

        clarity_gt_binary = (
            1
            if clarity_gt >= CLARITY_GT_MIN
            else 0
        )

        clarity_ok = (
            clarity_value >= CLARITY_MIN
        )

        clarity_prediction = (
            1 if clarity_ok else 0
        )

        if (
            clarity_gt_binary == 1
            and clarity_prediction == 1
        ):
            clarity_tp += 1

        elif (
            clarity_gt_binary == 1
            and clarity_prediction == 0
        ):
            clarity_fn += 1

        elif (
            clarity_gt_binary == 0
            and clarity_prediction == 0
        ):
            clarity_tn += 1

        else:
            clarity_fp += 1

        # ----------------------------------------------------
        # CONTROLES TÉCNICOS
        # ----------------------------------------------------

        illumination_ok = (
            dark_ratio <= DARK_RATIO_MAX
        )

        contrast_ok = (
            contrast_cv <= CONTRAST_CV_MAX
        )

        fov_ok = (
            fov_area >= FOV_AREA_MIN
            and
            fov_width >= FOV_WIDTH_MIN
            and
            fov_height >= FOV_HEIGHT_MIN
            and
            fov_offset
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
            criterion
            for criterion, passed
            in checks.items()
            if not passed
        ]

        predicted_quality = (
            0 if failed else 1
        )

        for criterion in failed:
            criterion_failures[
                criterion
            ] += 1

            if overall_gt == 0:
                failures_gt0[
                    criterion
                ] += 1
            else:
                failures_gt1[
                    criterion
                ] += 1

        if failed:
            combination = "+".join(
                sorted(failed)
            )

            failure_combinations[
                combination
            ] += 1

        if (
            overall_gt == 1
            and predicted_quality == 1
        ):
            tp += 1

        elif (
            overall_gt == 1
            and predicted_quality == 0
        ):
            fn += 1

        elif (
            overall_gt == 0
            and predicted_quality == 0
        ):
            tn += 1

        else:
            fp += 1

        results.append({
            "patient_id":
                row["patient_id"],

            "image_id":
                row["image_id"],

            "overall_gt":
                overall_gt,

            "clarity_gt":
                clarity_gt,

            "clarity_gt_binary":
                clarity_gt_binary,

            "clarity_ok":
                int(clarity_ok),

            "illumination_ok":
                int(illumination_ok),

            "contrast_ok":
                int(contrast_ok),

            "fov_ok":
                int(fov_ok),

            "predicted_quality":
                predicted_quality,

            "failed_criteria":
                ",".join(failed),
        })

    clarity_metrics = calculate_metrics(
        clarity_tp,
        clarity_fn,
        clarity_tn,
        clarity_fp
    )

    gate_metrics = calculate_metrics(
        tp,
        fn,
        tn,
        fp
    )

    print(
        "=== DeepDRiD Set-B — "
        "VALIDACIÓN SIN REAJUSTE ==="
    )

    print(
        f"Observaciones: {len(rows)}"
    )

    print()
    print(
        "=== THRESHOLDS CONGELADOS "
        "DESDE SET-A ==="
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

    # ========================================================
    # RESULTADO DE CLARIDAD
    # ========================================================

    print()
    print(
        "=== VALIDACIÓN DE CLARIDAD ==="
    )

    print(
        f"Ground truth: "
        f"Clarity >= {CLARITY_GT_MIN}"
    )

    print(
        f"Accuracy: "
        f"{clarity_metrics['accuracy']:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{clarity_metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"Recall claridad suficiente: "
        f"{clarity_metrics['recall_positive']:.4f}"
    )

    print(
        f"Recall claridad insuficiente: "
        f"{clarity_metrics['recall_negative']:.4f}"
    )

    print(
        f"False Accept Rate: "
        f"{clarity_metrics['false_accept_rate']:.4f}"
    )

    print(
        f"False Reject Rate: "
        f"{clarity_metrics['false_reject_rate']:.4f}"
    )

    print(
        f"TP={clarity_tp} "
        f"| FN={clarity_fn} "
        f"| TN={clarity_tn} "
        f"| FP={clarity_fp}"
    )

    # ========================================================
    # RESULTADO GLOBAL
    # ========================================================

    print()
    print(
        "=== QUALITY GATE COMPLETO "
        "VS OVERALL ==="
    )

    print(
        f"Accuracy: "
        f"{gate_metrics['accuracy']:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{gate_metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"Recall SUFICIENTE: "
        f"{gate_metrics['recall_positive']:.4f}"
    )

    print(
        f"Recall INSUFICIENTE: "
        f"{gate_metrics['recall_negative']:.4f}"
    )

    print(
        f"False Accept Rate: "
        f"{gate_metrics['false_accept_rate']:.4f}"
    )

    print(
        f"False Reject Rate: "
        f"{gate_metrics['false_reject_rate']:.4f}"
    )

    print(
        f"TP={tp} "
        f"| FN={fn} "
        f"| TN={tn} "
        f"| FP={fp}"
    )

    # ========================================================
    # DESGLOSE
    # ========================================================

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
            f"| GT Overall=0: "
            f"{failures_gt0[criterion]} "
            f"| GT Overall=1: "
            f"{failures_gt1[criterion]}"
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

    # ========================================================
    # CSV
    # ========================================================

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "patient_id",
        "image_id",
        "overall_gt",
        "clarity_gt",
        "clarity_gt_binary",
        "clarity_ok",
        "illumination_ok",
        "contrast_ok",
        "fov_ok",
        "predicted_quality",
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
        f"Resultado: {args.output}"
    )


if __name__ == "__main__":
    main()
