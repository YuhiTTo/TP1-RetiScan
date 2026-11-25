from argparse import ArgumentParser
from collections import Counter, defaultdict
from pathlib import Path
import csv

from app.services.image_quality_service import (
    assess_image_quality,
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

    directories = sorted(
        args.root.glob(
            "raw/*/1.0_Original_Fundus_Images/*"
        )
    )

    results = []

    status_counts = Counter()
    failure_counts = Counter()

    by_camera = defaultdict(
        Counter
    )

    by_split_camera = defaultdict(
        Counter
    )

    errors = 0
    processed = 0

    for directory in directories:

        if not directory.is_dir():
            continue

        split = directory.parents[1].name
        camera = directory.name

        images = sorted([
            path
            for path in directory.iterdir()
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

        for image_path in images:

            processed += 1

            try:
                content = (
                    image_path.read_bytes()
                )

                result = (
                    assess_image_quality(
                        content
                    )
                )

                status = result[
                    "status"
                ]

                failed = result[
                    "failed_criteria"
                ]

                status_counts[
                    status
                ] += 1

                by_camera[
                    camera
                ][status] += 1

                by_split_camera[
                    (
                        split,
                        camera
                    )
                ][status] += 1

                for criterion in failed:
                    failure_counts[
                        criterion
                    ] += 1

                metrics = result[
                    "metrics"
                ]

                results.append({
                    "split":
                        split,

                    "camera":
                        camera,

                    "image_name":
                        image_path.name,

                    "status":
                        status,

                    "failed_criteria":
                        ",".join(failed),

                    **metrics,
                })

            except Exception as error:
                errors += 1

                results.append({
                    "split":
                        split,

                    "camera":
                        camera,

                    "image_name":
                        image_path.name,

                    "status":
                        "ERROR",

                    "failed_criteria":
                        str(error),
                })

            if (
                processed % 100 == 0
            ):
                print(
                    f"Procesadas: {processed}"
                )

    total = len(results)

    print()
    print(
        "=== CHAKSU — QUALITY GATE "
        "CORREGIDO ==="
    )

    print(
        f"Total: {total}"
    )

    print(
        f"Errores: {errors}"
    )

    print()

    for status in [
        "SUFICIENTE",
        "INSUFICIENTE",
    ]:
        count = status_counts[
            status
        ]

        print(
            f"{status}: "
            f"{count}/{total} "
            f"({count / total * 100:.2f}%)"
        )

    print()
    print(
        "=== FALLOS POR CRITERIO ==="
    )

    for criterion in [
        "clarity",
        "illumination",
        "contrast",
        "fov",
    ]:
        count = failure_counts[
            criterion
        ]

        print(
            f"{criterion}: "
            f"{count}/{total} "
            f"({count / total * 100:.2f}%)"
        )

    print()
    print(
        "=== POR CÁMARA ==="
    )

    for camera in sorted(
        by_camera
    ):
        counts = by_camera[
            camera
        ]

        camera_total = sum(
            counts.values()
        )

        sufficient = counts[
            "SUFICIENTE"
        ]

        insufficient = counts[
            "INSUFICIENTE"
        ]

        print()
        print(camera)

        print(
            f"  SUFICIENTE: "
            f"{sufficient}/{camera_total} "
            f"({sufficient / camera_total * 100:.2f}%)"
        )

        print(
            f"  INSUFICIENTE: "
            f"{insufficient}/{camera_total} "
            f"({insufficient / camera_total * 100:.2f}%)"
        )

    print()
    print(
        "=== POR SPLIT + CÁMARA ==="
    )

    for key in sorted(
        by_split_camera
    ):

        split, camera = key

        counts = (
            by_split_camera[
                key
            ]
        )

        subset_total = sum(
            counts.values()
        )

        sufficient = counts[
            "SUFICIENTE"
        ]

        insufficient = counts[
            "INSUFICIENTE"
        ]

        print()
        print(
            f"{split} / {camera}"
        )

        print(
            f"  SUFICIENTE: "
            f"{sufficient}/{subset_total} "
            f"({sufficient / subset_total * 100:.2f}%)"
        )

        print(
            f"  INSUFICIENTE: "
            f"{insufficient}/{subset_total} "
            f"({insufficient / subset_total * 100:.2f}%)"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "split",
        "camera",
        "image_name",
        "status",
        "failed_criteria",
        "clarity_gradient_p90",
        "dark_ratio_30",
        "contrast_cv",
        "fov_area_ratio",
        "fov_width_ratio",
        "fov_height_ratio",
        "fov_center_offset",
    ]

    with args.output.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
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
