from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2
import numpy as np

from extract_clarity_metrics import (
    detect_fov,
    normalize_roi,
    calculate_clarity,
)


INNER_KERNEL_SIZE = 9


def get_inner_mask(
    normalized_mask: np.ndarray
) -> np.ndarray:

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            INNER_KERNEL_SIZE,
            INNER_KERNEL_SIZE
        )
    )

    inner_mask = cv2.erode(
        normalized_mask,
        kernel,
        iterations=1
    )

    if np.count_nonzero(
        inner_mask > 0
    ) == 0:
        raise ValueError(
            "La máscara retinal quedó vacía."
        )

    return inner_mask


def calculate_quality_candidates(
    normalized_bgr: np.ndarray,
    normalized_mask: np.ndarray
):
    gray = cv2.cvtColor(
        normalized_bgr,
        cv2.COLOR_BGR2GRAY
    )

    inner_mask = get_inner_mask(
        normalized_mask
    )

    valid_pixels = (
        inner_mask > 0
    )

    values = gray[
        valid_pixels
    ].astype(np.float64)

    if values.size == 0:
        raise ValueError(
            "No existen píxeles válidos "
            "para calcular las métricas."
        )

    p05 = float(
        np.percentile(values, 5)
    )

    p25 = float(
        np.percentile(values, 25)
    )

    p50 = float(
        np.percentile(values, 50)
    )

    p75 = float(
        np.percentile(values, 75)
    )

    p95 = float(
        np.percentile(values, 95)
    )

    mean = float(
        np.mean(values)
    )

    std = float(
        np.std(values)
    )

    dark_ratio = float(
        np.mean(values < 30)
    )

    bright_ratio = float(
        np.mean(values > 225)
    )

    contrast_iqr = (
        p75 - p25
    )

    contrast_p90_range = (
        p95 - p05
    )

    contrast_cv = (
        std / mean
        if mean > 0
        else 0.0
    )

    clarity_laplacian = (
        calculate_clarity(
            normalized_bgr,
            normalized_mask
        )
    )

    return {
        "luminance_mean": mean,
        "luminance_median": p50,
        "luminance_p05": p05,
        "luminance_p95": p95,
        "dark_ratio_30": dark_ratio,
        "bright_ratio_225": bright_ratio,
        "contrast_std": std,
        "contrast_iqr": contrast_iqr,
        "contrast_p90_range":
            contrast_p90_range,
        "contrast_cv": contrast_cv,
        "clarity_laplacian":
            clarity_laplacian,
    }


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--cfp-root",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--labels",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    with args.labels.open(
        encoding="utf-8",
        newline=""
    ) as file:
        labels = list(
            csv.DictReader(file)
        )

    results = []
    errors = 0

    for index, row in enumerate(
        labels,
        start=1
    ):
        subset = row["subset"]
        image_name = row[
            "image_name"
        ]

        image_path = (
            args.cfp_root /
            subset /
            image_name
        )

        metrics = None
        error_message = ""

        try:
            if not image_path.exists():
                raise FileNotFoundError(
                    f"Imagen no encontrada: "
                    f"{image_path}"
                )

            image = cv2.imread(
                str(image_path),
                cv2.IMREAD_COLOR
            )

            if image is None:
                raise ValueError(
                    "No se pudo leer la imagen."
                )

            fov_mask = detect_fov(
                image
            )

            (
                normalized,
                normalized_mask
            ) = normalize_roi(
                image,
                fov_mask
            )

            metrics = (
                calculate_quality_candidates(
                    normalized,
                    normalized_mask
                )
            )

        except Exception as error:
            errors += 1
            error_message = str(error)

        result = {
            "image_name": image_name,
            "subset": subset,
            "illumination_gt":
                row["illumination"],
            "clarity_gt":
                row["clarity"],
            "contrast_gt":
                row["contrast"],
            "overall_gt":
                row["overall"],
        }

        metric_names = [
            "luminance_mean",
            "luminance_median",
            "luminance_p05",
            "luminance_p95",
            "dark_ratio_30",
            "bright_ratio_225",
            "contrast_std",
            "contrast_iqr",
            "contrast_p90_range",
            "contrast_cv",
            "clarity_laplacian",
        ]

        for metric_name in metric_names:
            if metrics is not None:
                result[
                    metric_name
                ] = (
                    f"{metrics[metric_name]:.6f}"
                )
            else:
                result[
                    metric_name
                ] = ""

        result["error"] = (
            error_message
        )

        results.append(
            result
        )

        if (
            index % 50 == 0
            or index == len(labels)
        ):
            print(
                f"Procesadas "
                f"{index}/{len(labels)}"
            )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "image_name",
        "subset",
        "illumination_gt",
        "clarity_gt",
        "contrast_gt",
        "overall_gt",
        "luminance_mean",
        "luminance_median",
        "luminance_p05",
        "luminance_p95",
        "dark_ratio_30",
        "bright_ratio_225",
        "contrast_std",
        "contrast_iqr",
        "contrast_p90_range",
        "contrast_cv",
        "clarity_laplacian",
        "error",
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
        f"Imágenes procesadas: "
        f"{len(results)}"
    )
    print(
        f"Errores: {errors}"
    )
    print(
        f"Resultado: {args.output}"
    )


if __name__ == "__main__":
    main()
