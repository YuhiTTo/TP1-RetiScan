from argparse import ArgumentParser
from pathlib import Path
import csv
import random
import shutil


def main() -> None:
    parser = ArgumentParser(
        description=(
            "Selecciona muestras reproducibles de DeepDRiD "
            "para inspección visual de calidad."
        )
    )

    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--metadata-output",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=5
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42
    )

    args = parser.parse_args()

    training = (
        args.dataset_root /
        "regular-fundus-training"
    )

    csv_path = (
        training /
        "regular-fundus-training.csv"
    )

    images_dir = training / "Images"

    with csv_path.open(
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    image_map = {
        path.stem: path
        for path in images_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {
            ".jpg",
            ".jpeg",
            ".png"
        }
    }

    random.seed(args.seed)

    selected = []

    for quality in ("0", "1"):

        candidates = [
            row for row in rows
            if row["Overall quality"] == quality
        ]

        random.shuffle(candidates)

        used_patients = set()
        class_selected = []

        for row in candidates:

            patient_id = row["patient_id"]

            if patient_id in used_patients:
                continue

            image_id = row["image_id"]

            if image_id not in image_map:
                continue

            class_selected.append(row)
            used_patients.add(patient_id)

            if len(class_selected) == args.samples_per_class:
                break

        selected.extend(class_selected)

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    for row in selected:

        quality = row["Overall quality"]

        class_name = (
            "INSUFICIENTE"
            if quality == "0"
            else "SUFICIENTE"
        )

        class_dir = (
            args.output_dir /
            class_name
        )

        class_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        source = image_map[
            row["image_id"]
        ]

        destination = (
            class_dir /
            source.name
        )

        shutil.copy2(
            source,
            destination
        )

    args.metadata_output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fields = [
        "patient_id",
        "image_id",
        "Overall quality",
        "Clarity",
        "Field definition",
        "Artifact",
    ]

    with args.metadata_output.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for row in selected:
            writer.writerow({
                field: row[field]
                for field in fields
            })

    print(
        f"Muestras seleccionadas: "
        f"{len(selected)}"
    )

    print(
        f"Imágenes copiadas en: "
        f"{args.output_dir}"
    )

    print(
        f"Metadatos guardados en: "
        f"{args.metadata_output}"
    )


if __name__ == "__main__":
    main()
