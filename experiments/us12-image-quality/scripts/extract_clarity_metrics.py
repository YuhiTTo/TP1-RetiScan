from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2
import numpy as np


TARGET_SIZE = 1024
FOV_THRESHOLD = 10
MORPH_KERNEL_SIZE = 15


def detect_fov(image_bgr: np.ndarray):
    gray = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2GRAY
    )

    binary = (
        gray > FOV_THRESHOLD
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE)
    )

    mask = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    num_labels, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            mask,
            connectivity=8
        )
    )

    if num_labels <= 1:
        return mask

    areas = stats[
        1:,
        cv2.CC_STAT_AREA
    ]

    largest = 1 + np.argmax(areas)

    component = (
        labels == largest
    ).astype(np.uint8) * 255

    contours, _ = cv2.findContours(
        component,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return component

    contour = max(
        contours,
        key=cv2.contourArea
    )

    hull = cv2.convexHull(contour)

    final_mask = np.zeros_like(component)

    cv2.fillConvexPoly(
        final_mask,
        hull,
        255
    )

    return final_mask


def normalize_roi(
    image_bgr: np.ndarray,
    mask: np.ndarray
):
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ValueError(
            "No se detectó un FOV retinal válido."
        )

    contour = max(
        contours,
        key=cv2.contourArea
    )

    x, y, w, h = cv2.boundingRect(contour)

    crop = image_bgr[
        y:y + h,
        x:x + w
    ]

    crop_mask = mask[
        y:y + h,
        x:x + w
    ]

    scale = min(
        TARGET_SIZE / w,
        TARGET_SIZE / h
    )

    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(
        crop,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    resized_mask = cv2.resize(
        crop_mask,
        (new_w, new_h),
        interpolation=cv2.INTER_NEAREST
    )

    normalized = np.zeros(
        (TARGET_SIZE, TARGET_SIZE, 3),
        dtype=np.uint8
    )

    normalized_mask = np.zeros(
        (TARGET_SIZE, TARGET_SIZE),
        dtype=np.uint8
    )

    x_offset = (
        TARGET_SIZE - new_w
    ) // 2

    y_offset = (
        TARGET_SIZE - new_h
    ) // 2

    normalized[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized

    normalized_mask[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized_mask

    return normalized, normalized_mask


def calculate_clarity(
    normalized_bgr: np.ndarray,
    normalized_mask: np.ndarray
) -> float:

    gray = cv2.cvtColor(
        normalized_bgr,
        cv2.COLOR_BGR2GRAY
    )

    # Erosión ligera para evitar que el borde retina/fondo
    # influya artificialmente en la medida de nitidez.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (9, 9)
    )

    inner_mask = cv2.erode(
        normalized_mask,
        kernel,
        iterations=1
    )

    valid_pixels = (
        inner_mask > 0
    )

    if np.count_nonzero(valid_pixels) == 0:
        raise ValueError(
            "La máscara retinal quedó vacía."
        )

    laplacian = cv2.Laplacian(
        gray,
        cv2.CV_64F,
        ksize=3
    )

    values = laplacian[
        valid_pixels
    ]

    return float(
        np.var(values)
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
        args.dataset_root /
        "regular-fundus-training"
    )

    images_dir = (
        training /
        "Images"
    )

    csv_path = (
        training /
        "regular-fundus-training.csv"
    )

    image_map = {
        path.stem: path
        for path in images_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in {".jpg", ".jpeg", ".png"}
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
        image_id = row[
            "image_id"
        ]

        image_path = image_map.get(
            image_id
        )

        metric = None
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

            normalized, normalized_mask = (
                normalize_roi(
                    image,
                    fov_mask
                )
            )

            metric = calculate_clarity(
                normalized,
                normalized_mask
            )

        except Exception as error:
            errors += 1
            error_message = str(error)

        results.append({
            "patient_id": row[
                "patient_id"
            ],
            "image_id": image_id,
            "overall_quality": row[
                "Overall quality"
            ],
            "clarity_gt": row[
                "Clarity"
            ],
            "field_definition_gt": row[
                "Field definition"
            ],
            "artifact_gt": row[
                "Artifact"
            ],
            "clarity_laplacian": (
                f"{metric:.6f}"
                if metric is not None
                else ""
            ),
            "error": error_message
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
        "clarity_laplacian",
        "error"
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
        writer.writerows(results)

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
