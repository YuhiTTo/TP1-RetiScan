from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import csv

import cv2
import numpy as np

from app.services.image_quality_service import (
    detect_fov,
    calculate_fov_metrics,
    FOV_AREA_MIN,
    FOV_WIDTH_MIN,
    FOV_HEIGHT_MIN,
    FOV_CENTER_OFFSET_MAX,
)


def percentile(values, q):
    return float(
        np.percentile(
            np.asarray(values, dtype=float),
            q
        )
    )


def summarize(name, rows):
    total = len(rows)

    failed = [
        row
        for row in rows
        if not row["fov_ok"]
    ]

    print()
    print("=" * 72)
    print(name)

    print(
        f"Imágenes: {total}"
    )

    print(
        f"FOV insuficiente: "
        f"{len(failed)}/{total} "
        f"({len(failed) / total * 100:.2f}%)"
    )

    for metric in [
        "fov_area_ratio",
        "fov_width_ratio",
        "fov_height_ratio",
        "fov_center_offset",
    ]:
        values = [
            row[metric]
            for row in rows
        ]

        print()
        print(metric)

        print(
            f"  min: "
            f"{min(values):.8f}"
        )

        print(
            f"  P1: "
            f"{percentile(values, 1):.8f}"
        )

        print(
            f"  P5: "
            f"{percentile(values, 5):.8f}"
        )

        print(
            f"  mediana: "
            f"{percentile(values, 50):.8f}"
        )

        print(
            f"  P95: "
            f"{percentile(values, 95):.8f}"
        )

        print(
            f"  P99: "
            f"{percentile(values, 99):.8f}"
        )

        print(
            f"  max: "
            f"{max(values):.8f}"
        )


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--root",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    raw_root = (
        args.root / "raw"
    )

    image_dirs = [
        raw_root / "train_images",
        raw_root / "test_images",
    ]

    results = []
    errors = 0

    for image_dir in image_dirs:
        if not image_dir.exists():
            continue

        split = image_dir.name

        image_paths = sorted([
            path
            for path in image_dir.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                }
            )
        ])

        for index, image_path in enumerate(
            image_paths,
            start=1
        ):
            try:
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

                area_ok = (
                    metrics[
                        "fov_area_ratio"
                    ]
                    >= FOV_AREA_MIN
                )

                width_ok = (
                    metrics[
                        "fov_width_ratio"
                    ]
                    >= FOV_WIDTH_MIN
                )

                height_ok = (
                    metrics[
                        "fov_height_ratio"
                    ]
                    >= FOV_HEIGHT_MIN
                )

                offset_ok = (
                    metrics[
                        "fov_center_offset"
                    ]
                    <= FOV_CENTER_OFFSET_MAX
                )

                fov_ok = (
                    area_ok
                    and width_ok
                    and height_ok
                    and offset_ok
                )

                results.append({
                    "split":
                        split,

                    "image_name":
                        image_path.name,

                    **metrics,

                    "area_ok":
                        area_ok,

                    "width_ok":
                        width_ok,

                    "height_ok":
                        height_ok,

                    "offset_ok":
                        offset_ok,

                    "fov_ok":
                        fov_ok,
                })

            except Exception as error:
                errors += 1

                print(
                    f"ERROR: {image_path} "
                    f"-> {error}"
                )

            if (
                index % 500 == 0
                or index == len(image_paths)
            ):
                print(
                    f"{split}: "
                    f"{index}/{len(image_paths)}"
                )

    print()
    print(
        "=== APTOS 2019 — TRANSFERENCIA "
        "DEL CONTROL FOV ==="
    )

    print()
    print(
        "Thresholds DeepDRiD congelados:"
    )

    print(
        f"area   >= {FOV_AREA_MIN:.8f}"
    )

    print(
        f"width  >= {FOV_WIDTH_MIN:.8f}"
    )

    print(
        f"height >= {FOV_HEIGHT_MIN:.8f}"
    )

    print(
        f"offset <= "
        f"{FOV_CENTER_OFFSET_MAX:.8f}"
    )

    print(
        f"\nErrores: {errors}"
    )

    summarize(
        "TODAS LAS IMÁGENES",
        results
    )

    by_split = defaultdict(list)

    for row in results:
        by_split[
            row["split"]
        ].append(row)

    print()
    print()
    print(
        "######## POR SPLIT ########"
    )

    for split in sorted(
        by_split
    ):
        summarize(
            split,
            by_split[split]
        )

    print()
    print(
        "=== FALLO POR COMPONENTE ==="
    )

    for name, field in [
        ("area", "area_ok"),
        ("width", "width_ok"),
        ("height", "height_ok"),
        ("offset", "offset_ok"),
    ]:
        failed = sum(
            not row[field]
            for row in results
        )

        print(
            f"{name}: "
            f"{failed}/{len(results)} "
            f"({failed / len(results) * 100:.2f}%)"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "split",
        "image_name",
        "fov_area_ratio",
        "fov_width_ratio",
        "fov_height_ratio",
        "fov_center_offset",
        "area_ok",
        "width_ok",
        "height_ok",
        "offset_ok",
        "fov_ok",
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
