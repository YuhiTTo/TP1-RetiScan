from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2
import numpy as np

from extract_clarity_metrics import (
    detect_fov,
    normalize_roi,
)

from extract_mshf_quality_metrics import (
    calculate_quality_candidates,
)

from extract_mshf_clarity_candidates import (
    calculate_clarity_candidates,
)


def calculate_fov_metrics(
    image_bgr,
    mask
):
    height, width = mask.shape

    valid = mask > 0

    if np.count_nonzero(valid) == 0:
        raise ValueError(
            "No se detectó un FOV válido."
        )

    ys, xs = np.where(valid)

    x_min = int(xs.min())
    x_max = int(xs.max())

    y_min = int(ys.min())
    y_max = int(ys.max())

    fov_width = (
        x_max - x_min + 1
    )

    fov_height = (
        y_max - y_min + 1
    )

    fov_area_ratio = (
        np.count_nonzero(valid)
        / (height * width)
    )

    fov_width_ratio = (
        fov_width / width
    )

    fov_height_ratio = (
        fov_height / height
    )

    center_x = (
        x_min + x_max
    ) / 2.0

    center_y = (
        y_min + y_max
    ) / 2.0

    image_center_x = (
        width - 1
    ) / 2.0

    image_center_y = (
        height - 1
    ) / 2.0

    dx = (
        center_x
        - image_center_x
    )

    dy = (
        center_y
        - image_center_y
    )

    diagonal = np.sqrt(
        width ** 2
        + height ** 2
    )

    center_offset = (
        np.sqrt(
            dx ** 2
            + dy ** 2
        )
        / diagonal
    )

    return {
        "fov_area_ratio":
            float(fov_area_ratio),

        "fov_width_ratio":
            float(fov_width_ratio),

        "fov_height_ratio":
            float(fov_height_ratio),

        "fov_center_offset":
            float(center_offset),
    }


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    validation = (
        args.dataset_root
        / "regular-fundus-validation"
    )

    images_dir = (
        validation
        / "Images"
    )

    csv_path = (
        validation
        / "regular-fundus-validation.csv"
    )

    image_map = {
        path.stem: path
        for path in images_dir.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in {
                ".jpg",
                ".jpeg",
                ".png",
            }
        )
    }

    with csv_path.open(
        encoding="utf-8-sig",
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
        image_id = row["image_id"]

        image_path = image_map.get(
            image_id
        )

        quality_metrics = None
        clarity_metrics = None
        fov_metrics = None

        error_message = ""

        try:
            if image_path is None:
                raise FileNotFoundError(
                    "Imagen no encontrada."
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

            fov_metrics = (
                calculate_fov_metrics(
                    image,
                    fov_mask
                )
            )

            (
                normalized,
                normalized_mask
            ) = normalize_roi(
                image,
                fov_mask
            )

            quality_metrics = (
                calculate_quality_candidates(
                    normalized,
                    normalized_mask
                )
            )

            clarity_metrics = (
                calculate_clarity_candidates(
                    normalized,
                    normalized_mask
                )
            )

        except Exception as error:
            errors += 1
            error_message = str(error)

        result = {
            "patient_id":
                row["patient_id"],

            "image_id":
                image_id,

            "overall_quality":
                row["Overall quality"],

            "clarity_gt":
                row["Clarity"],

            "field_definition_gt":
                row["Field definition"],

            "artifact_gt":
                row["Artifact"],

            "error":
                error_message,
        }

        if (
            quality_metrics is not None
            and clarity_metrics is not None
            and fov_metrics is not None
        ):
            result.update({
                "clarity_gradient_p90":
                    f"{clarity_metrics['clarity_gradient_p90']:.8f}",

                "dark_ratio_30":
                    f"{quality_metrics['dark_ratio_30']:.8f}",

                "contrast_cv":
                    f"{quality_metrics['contrast_cv']:.8f}",

                "fov_area_ratio":
                    f"{fov_metrics['fov_area_ratio']:.8f}",

                "fov_width_ratio":
                    f"{fov_metrics['fov_width_ratio']:.8f}",

                "fov_height_ratio":
                    f"{fov_metrics['fov_height_ratio']:.8f}",

                "fov_center_offset":
                    f"{fov_metrics['fov_center_offset']:.8f}",
            })

        else:
            result.update({
                "clarity_gradient_p90": "",
                "dark_ratio_30": "",
                "contrast_cv": "",
                "fov_area_ratio": "",
                "fov_width_ratio": "",
                "fov_height_ratio": "",
                "fov_center_offset": "",
            })

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
        "patient_id",
        "image_id",
        "overall_quality",
        "clarity_gt",
        "field_definition_gt",
        "artifact_gt",
        "clarity_gradient_p90",
        "dark_ratio_30",
        "contrast_cv",
        "fov_area_ratio",
        "fov_width_ratio",
        "fov_height_ratio",
        "fov_center_offset",
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
