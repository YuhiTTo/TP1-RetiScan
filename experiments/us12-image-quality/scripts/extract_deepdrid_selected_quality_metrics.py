from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2

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

    training = (
        args.dataset_root
        / "regular-fundus-training"
    )

    images_dir = (
        training
        / "Images"
    )

    csv_path = (
        training
        / "regular-fundus-training.csv"
    )

    image_map = {
        path.stem: path
        for path in images_dir.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in {".jpg", ".jpeg", ".png"}
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

        metrics = None
        clarity_metrics = None
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

            clarity_metrics = (
                calculate_clarity_candidates(
                    normalized,
                    normalized_mask
                )
            )

        except Exception as error:
            errors += 1
            error_message = str(error)

        results.append({
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

            "clarity_gradient_p90":
                (
                    f"{clarity_metrics['clarity_gradient_p90']:.8f}"
                    if clarity_metrics is not None
                    else ""
                ),

            "dark_ratio_30":
                (
                    f"{metrics['dark_ratio_30']:.8f}"
                    if metrics is not None
                    else ""
                ),

            "contrast_cv":
                (
                    f"{metrics['contrast_cv']:.8f}"
                    if metrics is not None
                    else ""
                ),

            "error":
                error_message,
        })

        if (
            index % 100 == 0
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
