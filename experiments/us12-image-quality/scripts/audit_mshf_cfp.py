from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import csv

from openpyxl import load_workbook


SUBSETS = [
    "DR-XJU",
    "DR-ZJU",
    "Glaucoma",
    "Healthy",
]

METRICS = [
    "illumination",
    "clarity",
    "contrast",
    "overall",
]


def collect_images(root):
    images = {}

    for subset in SUBSETS:
        subset_dir = root / subset

        for path in subset_dir.iterdir():
            if (
                path.is_file()
                and path.suffix.lower()
                in {".jpg", ".jpeg", ".png"}
            ):
                images[(subset, path.name)] = path

    return images


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--cfp-root",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--scores",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    images = collect_images(args.cfp_root)

    wb = load_workbook(
        args.scores,
        read_only=True,
        data_only=True
    )

    rows_output = []
    matched_images = set()
    problems = []

    distributions = {
        subset: {
            metric: Counter()
            for metric in METRICS
        }
        for subset in SUBSETS
    }

    for subset in SUBSETS:
        ws = wb[subset]

        subset_images = {
            name: path
            for (image_subset, name), path
            in images.items()
            if image_subset == subset
        }

        by_stem = {
            path.stem: name
            for name, path
            in subset_images.items()
        }

        for row_idx, row in enumerate(
            ws.iter_rows(values_only=True),
            start=1
        ):
            if not row:
                continue

            label_name = row[0]

            if not isinstance(label_name, str):
                continue

            label_name = label_name.strip()

            if not label_name.startswith(
                subset + "-"
            ):
                continue

            # Coincidencia exacta
            if label_name in subset_images:
                image_name = label_name
                match_method = "exact"

            # Casos como DR-XJU-30 -> DR-XJU-30.png
            elif label_name in by_stem:
                image_name = by_stem[label_name]
                match_method = "stem_without_extension"

            else:
                problems.append(
                    f"Etiqueta sin imagen: "
                    f"{subset} | {label_name} "
                    f"| fila {row_idx}"
                )
                continue

            try:
                values = tuple(
                    int(v)
                    for v in row[1:5]
                )
            except (TypeError, ValueError):
                problems.append(
                    f"Valores inválidos: "
                    f"{subset} | {label_name} "
                    f"| fila {row_idx}"
                )
                continue

            if (
                len(values) != 4
                or not all(
                    value in {0, 1}
                    for value in values
                )
            ):
                problems.append(
                    f"Valores no binarios: "
                    f"{subset} | {label_name}"
                )
                continue

            key = (
                subset,
                image_name
            )

            matched_images.add(key)

            for metric, value in zip(
                METRICS,
                values
            ):
                distributions[
                    subset
                ][metric][value] += 1

            rows_output.append({
                "image_name": image_name,
                "subset": subset,
                "illumination": values[0],
                "clarity": values[1],
                "contrast": values[2],
                "overall": values[3],
                "source_version": "MSHF_v1",
                "source_sheet": subset,
                "source_row": row_idx,
                "match_method": match_method,
            })

    missing = sorted(
        set(images) - matched_images
    )

    print("=== MSHF CFP — AUDITORÍA DEFINITIVA ===")
    print(f"Imágenes CFP: {len(images)}")
    print(
        f"Imágenes con ground truth: "
        f"{len(rows_output)}"
    )
    print(
        f"Imágenes sin ground truth: "
        f"{len(missing)}"
    )

    print("\n=== SIN GROUND TRUTH ===")

    for subset, image_name in missing:
        print(
            f"{subset}: {image_name}"
        )

    print("\n=== DISTRIBUCIONES USADAS ===")

    totals = {
        metric: Counter()
        for metric in METRICS
    }

    for subset in SUBSETS:
        print(f"\n{subset}")

        for metric in METRICS:
            counter = distributions[
                subset
            ][metric]

            totals[metric].update(
                counter
            )

            print(
                f"  {metric}: "
                f"0={counter[0]} | "
                f"1={counter[1]}"
            )

    print("\n=== TOTAL 499 ETIQUETADAS ===")

    for metric in METRICS:
        counter = totals[metric]

        print(
            f"{metric}: "
            f"0={counter[0]} | "
            f"1={counter[1]}"
        )

    stem_matches = [
        row
        for row in rows_output
        if row["match_method"]
        == "stem_without_extension"
    ]

    print(
        "\nCoincidencias recuperadas "
        "sin extensión: "
        f"{len(stem_matches)}"
    )

    for row in stem_matches:
        print(
            f"  {row['source_sheet']} "
            f"fila {row['source_row']} "
            f"-> {row['image_name']}"
        )

    print("\n=== DECISIÓN METODOLÓGICA ===")

    if (
        len(images) == 500
        and len(rows_output) == 499
        and missing
        == [("DR-ZJU", "DR-ZJU-23.jpg")]
    ):
        print("RESULTADO: DATASET VERIFICADO ✅")
        print(
            "MSHF contiene 500 CFP; "
            "499 disponen de ground truth "
            "individual verificable en v1."
        )
        print(
            "DR-ZJU-23.jpg se excluye de "
            "la evaluación supervisada por "
            "inconsistencia de anotación entre "
            "versiones."
        )
    else:
        print(
            "RESULTADO: REVISIÓN NECESARIA ❌"
        )

    if problems:
        print("\n=== OTROS PROBLEMAS ===")
        for problem in problems:
            print(problem)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with args.output.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                rows_output[0].keys()
            )
        )

        writer.writeheader()
        writer.writerows(
            rows_output
        )

    print(
        f"\nCSV generado: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
