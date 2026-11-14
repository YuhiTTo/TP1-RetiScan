from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import csv

from PIL import Image


QUALITY_COLUMNS = [
    "Overall quality",
    "Clarity",
    "Field definition",
    "Artifact",
]

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def inspect_split(name: str, folder: Path, csv_path: Path) -> None:
    print(f"\n{'=' * 60}")
    print(name)
    print("=" * 60)

    image_files = sorted(
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in VALID_EXTENSIONS
    )

    formats = Counter()
    modes = Counter()
    resolutions = Counter()
    unreadable = []

    for path in image_files:
        try:
            with Image.open(path) as image:
                formats[image.format or "UNKNOWN"] += 1
                modes[image.mode] += 1
                resolutions[image.size] += 1

        except Exception as error:
            unreadable.append(
                (str(path), str(error))
            )

    with csv_path.open(
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    print(f"Imágenes encontradas: {len(image_files)}")
    print(f"Registros CSV:       {len(rows)}")
    print(f"Errores de lectura:  {len(unreadable)}")

    print("\nFormatos:")
    for value, count in sorted(formats.items()):
        print(f"  {value}: {count}")

    print("\nModos de color:")
    for value, count in sorted(modes.items()):
        print(f"  {value}: {count}")

    print(
        f"\nResoluciones distintas: "
        f"{len(resolutions)}"
    )

    print("Resoluciones más frecuentes:")
    for size, count in resolutions.most_common(10):
        print(f"  {size}: {count}")

    print("\nDistribución de etiquetas:")

    for column in QUALITY_COLUMNS:
        counts = Counter(
            row[column]
            for row in rows
        )

        print(f"  {column}:")
        for value, count in sorted(
            counts.items(),
            key=lambda item: float(item[0])
        ):
            print(f"    {value}: {count}")

    image_names = {
        path.stem
        for path in image_files
    }

    csv_image_ids = {
        row["image_id"]
        for row in rows
    }

    missing_images = sorted(
        csv_image_ids - image_names
    )

    images_without_label = sorted(
        image_names - csv_image_ids
    )

    print("\nConsistencia imagen ↔ CSV:")
    print(
        "  Registros sin imagen: "
        f"{len(missing_images)}"
    )
    print(
        "  Imágenes sin etiqueta: "
        f"{len(images_without_label)}"
    )

    if unreadable:
        print("\nArchivos con error:")
        for path, error in unreadable[:10]:
            print(f"  {path}: {error}")


def main() -> None:
    parser = ArgumentParser(
        description=(
            "Inspección inicial del dataset "
            "DeepDRiD para el experimento US-12."
        )
    )

    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help=(
            "Ruta a regular_fundus_images "
            "del dataset DeepDRiD."
        ),
    )

    args = parser.parse_args()

    root = args.dataset_root.resolve()

    training = root / "regular-fundus-training"
    validation = root / "regular-fundus-validation"

    inspect_split(
        name="DEEPDRID TRAINING / SET-A",
        folder=training / "Images",
        csv_path=(
            training /
            "regular-fundus-training.csv"
        ),
    )

    inspect_split(
        name="DEEPDRID VALIDATION / SET-B",
        folder=validation / "Images",
        csv_path=(
            validation /
            "regular-fundus-validation.csv"
        ),
    )


if __name__ == "__main__":
    main()
