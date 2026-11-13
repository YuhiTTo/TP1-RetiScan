from argparse import ArgumentParser
from pathlib import Path
import csv

import cv2

from extract_fov_metrics import (
    detect_fov,
    calculate_fov_metrics,
)


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--images-dir",
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

    image_map = {
        path.stem: path
        for path in args.images_dir.rglob("*")
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

    errors = 0

    for index, row in enumerate(
        rows,
        start=1
    ):
        image_id = row["image_id"]

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

            row["fov_area_ratio"] = (
                f"{metrics['fov_area_ratio']:.8f}"
            )

            row["fov_width_ratio"] = (
                f"{metrics['fov_width_ratio']:.8f}"
            )

            row["fov_height_ratio"] = (
                f"{metrics['fov_height_ratio']:.8f}"
            )

            row["fov_center_offset"] = (
                f"{metrics['fov_center_offset']:.8f}"
            )

        except Exception as error:
            errors += 1

            row["error"] = (
                f"FOV correction: {error}"
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

    fields = list(
        rows[0].keys()
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
        writer.writerows(
            rows
        )

    print()
    print(
        f"Imágenes procesadas: "
        f"{len(rows)}"
    )

    print(
        f"Errores: {errors}"
    )

    print(
        f"Resultado: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
