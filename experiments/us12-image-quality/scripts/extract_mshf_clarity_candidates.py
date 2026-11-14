from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2
import numpy as np

from extract_clarity_metrics import (
    detect_fov,
    normalize_roi,
)


INNER_KERNEL_SIZE = 9
EPSILON = 1e-8


def calculate_clarity_candidates(
    normalized_bgr,
    normalized_mask
):
    gray = cv2.cvtColor(
        normalized_bgr,
        cv2.COLOR_BGR2GRAY
    ).astype(np.float64)

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

    valid = inner_mask > 0

    if np.count_nonzero(valid) == 0:
        raise ValueError(
            "La máscara retinal quedó vacía."
        )

    intensity = gray[valid]

    mean_luminance = float(
        np.mean(intensity)
    )

    # -------------------------------------------------
    # Laplaciano
    # -------------------------------------------------

    laplacian = cv2.Laplacian(
        gray,
        cv2.CV_64F,
        ksize=3
    )

    lap_values = laplacian[
        valid
    ]

    laplacian_variance = float(
        np.var(lap_values)
    )

    laplacian_normalized = (
        laplacian_variance
        / (
            mean_luminance ** 2
            + EPSILON
        )
    )

    # -------------------------------------------------
    # Tenengrad / Sobel
    # -------------------------------------------------

    sobel_x = cv2.Sobel(
        gray,
        cv2.CV_64F,
        1,
        0,
        ksize=3
    )

    sobel_y = cv2.Sobel(
        gray,
        cv2.CV_64F,
        0,
        1,
        ksize=3
    )

    gradient_squared = (
        sobel_x ** 2
        + sobel_y ** 2
    )

    tenengrad = float(
        np.mean(
            gradient_squared[
                valid
            ]
        )
    )

    tenengrad_normalized = (
        tenengrad
        / (
            mean_luminance ** 2
            + EPSILON
        )
    )

    # -------------------------------------------------
    # Magnitud de gradiente
    # -------------------------------------------------

    gradient_magnitude = np.sqrt(
        gradient_squared
    )

    gradient_values = (
        gradient_magnitude[
            valid
        ]
    )

    gradient_p90 = float(
        np.percentile(
            gradient_values,
            90
        )
    )

    gradient_p90_normalized = (
        gradient_p90
        / (
            mean_luminance
            + EPSILON
        )
    )

    return {
        "clarity_laplacian":
            laplacian_variance,

        "clarity_laplacian_norm":
            laplacian_normalized,

        "clarity_tenengrad":
            tenengrad,

        "clarity_tenengrad_norm":
            tenengrad_normalized,

        "clarity_gradient_p90":
            gradient_p90,

        "clarity_gradient_p90_norm":
            gradient_p90_normalized,
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
        rows = list(
            csv.DictReader(file)
        )

    results = []
    errors = 0

    for index, row in enumerate(
        rows,
        start=1
    ):
        subset = row["subset"]
        image_name = row[
            "image_name"
        ]

        image_path = (
            args.cfp_root
            / subset
            / image_name
        )

        metrics = None
        error_message = ""

        try:
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
                calculate_clarity_candidates(
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
            "clarity_gt":
                row["clarity"],
            "overall_gt":
                row["overall"],
        }

        metric_names = [
            "clarity_laplacian",
            "clarity_laplacian_norm",
            "clarity_tenengrad",
            "clarity_tenengrad_norm",
            "clarity_gradient_p90",
            "clarity_gradient_p90_norm",
        ]

        for metric_name in metric_names:
            result[metric_name] = (
                f"{metrics[metric_name]:.8f}"
                if metrics is not None
                else ""
            )

        result["error"] = (
            error_message
        )

        results.append(
            result
        )

        if (
            index % 50 == 0
            or index == len(rows)
        ):
            print(
                f"Procesadas "
                f"{index}/{len(rows)}"
            )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "image_name",
        "subset",
        "clarity_gt",
        "overall_gt",
        "clarity_laplacian",
        "clarity_laplacian_norm",
        "clarity_tenengrad",
        "clarity_tenengrad_norm",
        "clarity_gradient_p90",
        "clarity_gradient_p90_norm",
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
