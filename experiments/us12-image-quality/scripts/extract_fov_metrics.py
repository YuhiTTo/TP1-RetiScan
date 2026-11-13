from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2
import numpy as np


FOV_THRESHOLD = 10
MORPH_KERNEL_SIZE = 15


def detect_fov(image_bgr: np.ndarray) -> np.ndarray:
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


def calculate_fov_metrics(
    mask: np.ndarray
) -> dict:

    h, w = mask.shape

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

    x, y, bbox_w, bbox_h = (
        cv2.boundingRect(contour)
    )

    area_pixels = np.count_nonzero(
        mask
    )

    fov_area_ratio = (
        area_pixels / float(w * h)
    )

    fov_width_ratio = (
        bbox_w / float(w)
    )

    fov_height_ratio = (
        bbox_h / float(h)
    )

    moments = cv2.moments(
        contour
    )

    if moments["m00"] == 0:
        center_x = (
            x + bbox_w / 2.0
        )

        center_y = (
            y + bbox_h / 2.0
        )

    else:
        center_x = (
            moments["m10"] /
            moments["m00"]
        )

        center_y = (
            moments["m01"] /
            moments["m00"]
        )

    image_center_x = w / 2.0
    image_center_y = h / 2.0

    dx = (
        center_x - image_center_x
    ) / w

    dy = (
        center_y - image_center_y
    ) / h

    center_offset = float(
        np.sqrt(
            dx ** 2 +
            dy ** 2
        )
    )

    return {
        "fov_area_ratio": fov_area_ratio,
        "fov_width_ratio": fov_width_ratio,
        "fov_height_ratio": fov_height_ratio,
        "fov_center_offset": center_offset,
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
        image_id = row["image_id"]

        error_message = ""

        metrics = {
            "fov_area_ratio": None,
            "fov_width_ratio": None,
            "fov_height_ratio": None,
            "fov_center_offset": None,
        }

        try:
            image_path = image_map.get(
                image_id
            )

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

            mask = detect_fov(
                image
            )

            metrics = calculate_fov_metrics(
                mask
            )

        except Exception as error:
            errors += 1
            error_message = str(error)

        results.append({
            "patient_id": row["patient_id"],
            "image_id": image_id,
            "overall_quality": row[
                "Overall quality"
            ],
            "field_definition_gt": row[
                "Field definition"
            ],
            "fov_area_ratio": (
                f"{metrics['fov_area_ratio']:.6f}"
                if metrics["fov_area_ratio"]
                is not None
                else ""
            ),
            "fov_width_ratio": (
                f"{metrics['fov_width_ratio']:.6f}"
                if metrics["fov_width_ratio"]
                is not None
                else ""
            ),
            "fov_height_ratio": (
                f"{metrics['fov_height_ratio']:.6f}"
                if metrics["fov_height_ratio"]
                is not None
                else ""
            ),
            "fov_center_offset": (
                f"{metrics['fov_center_offset']:.6f}"
                if metrics["fov_center_offset"]
                is not None
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

    fields = list(
        results[0].keys()
    )

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
