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

    image_dirs = [
        args.root / "raw" / "train_images",
        args.root / "raw" / "test_images",
    ]

    results = []

    status_counts = Counter()
    failure_counts = Counter()
    by_split = defaultdict(Counter)

    errors = 0
    processed = 0

    for image_dir in image_dirs:

        if not image_dir.exists():
            continue

        split = image_dir.name

        images = sorted([
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

                by_split[
                    split
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

                    "image_name":
                        image_path.name,

                    "status":
                        "ERROR",

                    "failed_criteria":
                        str(error),
                })

            if (
                processed % 500 == 0
            ):
                print(
                    f"Procesadas: {processed}"
                )

    total = len(results)

    print()
    print(
        "=== APTOS 2019 — QUALITY GATE "
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
        "=== POR SPLIT ==="
    )

    for split in sorted(
        by_split
    ):

        counts = by_split[
            split
        ]

        split_total = sum(
            counts.values()
        )

        sufficient = counts[
            "SUFICIENTE"
        ]

        insufficient = counts[
            "INSUFICIENTE"
        ]

        print()
        print(split)

        print(
            f"  SUFICIENTE: "
            f"{sufficient}/{split_total} "
            f"({sufficient / split_total * 100:.2f}%)"
        )

        print(
            f"  INSUFICIENTE: "
            f"{insufficient}/{split_total} "
            f"({insufficient / split_total * 100:.2f}%)"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "split",
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
