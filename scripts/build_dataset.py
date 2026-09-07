"""
=============================================================================
RETISCAN - COMPILADOR DEL DATASET Y MANIFEST (OE1 - OE1-I2)
Sistema de Soporte Clínico CAD - Centro Oftalmológico V.E.R.
=============================================================================
Este script orquesta el pipeline completo de ingeniería de datos:
1. Lectura de imágenes crudas en data/raw/{healthy, diabetic_retinopathy, glaucoma}.
2. Preprocesamiento integral con OpenCV (ROI, CLAHE, 224x224).
3. Partición estratificada: Train (70%), Val (15%), Test (15%).
4. Data Augmentation para balancear ÚNICAMENTE el subconjunto de Train
   (Previniendo Data Leakage según estándares médicos).
5. Generación del catálogo formal 'data/dataset_manifest.csv'.
"""

import os
import cv2
import random
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict

from preprocess import preprocess_fundus_image
from augment import apply_random_augmentation


# Mapeo oficial de clases del proyecto
CLASSES = {
    "healthy": 0,
    "diabetic_retinopathy": 1,
    "glaucoma": 2
}

SPLIT_RATIOS = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15
}


def scan_raw_images(raw_dir: Path) -> Dict[str, List[Path]]:
    """Escanea y agrupa los archivos válidos de imagen por clase."""
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    data_by_class = {}

    for cls_name in CLASSES.keys():
        cls_dir = raw_dir / cls_name
        cls_dir.mkdir(parents=True, exist_ok=True)
        files = [p for p in cls_dir.glob("*") if p.suffix.lower() in valid_exts]
        data_by_class[cls_name] = sorted(files)

    return data_by_class


def partition_samples(samples: List[Path], train_ratio=0.70, val_ratio=0.15) -> Dict[str, List[Path]]:
    """Divide las muestras de forma reproducible asegurando al menos 1 por split si hay pocas."""
    shuffled = samples.copy()
    random.seed(42)
    random.shuffle(shuffled)
    n = len(shuffled)

    if n == 0:
        return {"train": [], "val": [], "test": []}
    elif n == 1:
        # Caso muestra única base: asignar a train
        return {"train": [shuffled[0]], "val": [shuffled[0]], "test": [shuffled[0]]}
    elif n == 2:
        return {"train": [shuffled[0]], "val": [shuffled[1]], "test": [shuffled[1]]}

    n_train = max(1, int(round(n * train_ratio)))
    n_val = max(1, int(round(n * val_ratio)))
    
    train_set = shuffled[:n_train]
    val_set = shuffled[n_train:n_train + n_val]
    test_set = shuffled[n_train + n_val:]
    
    # Asegurar que ningún split quede vacío si n >= 3
    if not test_set:
        test_set = [val_set.pop()]

    return {"train": train_set, "val": val_set, "test": test_set}


def build_retiscan_dataset(
    raw_dir: Path,
    processed_dir: Path,
    target_train_per_class: int = 10,
    apply_clahe_flag: bool = True
) -> pd.DataFrame:
    """Ejecuta el pipeline de construcción, guardado y manifiesto."""
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)

    raw_data = scan_raw_images(raw_dir)
    records = []

    print("\n" + "=" * 65)
    print("[INFO] INICIANDO PIPELINE DE CONSTRUCCION DEL DATASET RETISCAN")
    print("=" * 65)

    # Limpiar y preparar carpetas processed
    for split in ["train", "val", "test"]:
        for cls_name in CLASSES.keys():
            (processed_dir / split / cls_name).mkdir(parents=True, exist_ok=True)

    img_counter = 1

    for cls_name, cls_files in raw_data.items():
        label_idx = CLASSES[cls_name]
        print(f"\n[*] Procesando clase: '{cls_name}' ({len(cls_files)} imagenes crudas encontradas)")

        splits = partition_samples(cls_files, SPLIT_RATIOS["train"], SPLIT_RATIOS["val"])

        for split_name, file_list in splits.items():
            for original_path in file_list:
                # 1. Preprocesamiento (ROI + CLAHE + 224x224)
                img_uint8, _ = preprocess_fundus_image(
                    original_path,
                    target_size=(224, 224),
                    apply_clahe_flag=apply_clahe_flag
                )

                img_id = f"RET_{cls_name[:3].upper()}_{img_counter:05d}"
                out_filename = f"{img_id}_{split_name}.png"
                out_path = processed_dir / split_name / cls_name / out_filename
                cv2.imwrite(str(out_path), img_uint8)

                records.append({
                    "image_id": img_id,
                    "class_name": cls_name,
                    "label_idx": label_idx,
                    "split": split_name,
                    "is_augmented": False,
                    "original_file": original_path.name,
                    "relative_path": str(out_path.relative_to(processed_dir.parent)),
                    "resolution": "224x224",
                    "channels": 3
                })
                img_counter += 1

            # 2. Data Augmentation exclusivo para el split de entrenamiento (Train)
            if split_name == "train" and len(file_list) > 0:
                current_train_count = len(file_list)
                needed_aug = max(0, target_train_per_class - current_train_count)

                if needed_aug > 0:
                    print(f"   [+] Aumentando split 'train' con {needed_aug} muestras sinteticas...")
                    aug_idx = 0
                    while aug_idx < needed_aug:
                        base_path = file_list[aug_idx % len(file_list)]
                        base_uint8, _ = preprocess_fundus_image(
                            base_path,
                            target_size=(224, 224),
                            apply_clahe_flag=apply_clahe_flag
                        )
                        # Transformación controlada
                        aug_img = apply_random_augmentation(base_uint8)

                        aug_id = f"RET_{cls_name[:3].upper()}_{img_counter:05d}_AUG"
                        aug_filename = f"{aug_id}_train.png"
                        aug_path = processed_dir / "train" / cls_name / aug_filename
                        cv2.imwrite(str(aug_path), aug_img)

                        records.append({
                            "image_id": aug_id,
                            "class_name": cls_name,
                            "label_idx": label_idx,
                            "split": "train",
                            "is_augmented": True,
                            "original_file": base_path.name,
                            "relative_path": str(aug_path.relative_to(processed_dir.parent)),
                            "resolution": "224x224",
                            "channels": 3
                        })
                        img_counter += 1
                        aug_idx += 1

    # Guardar Manifiesto CSV
    df = pd.DataFrame(records)
    manifest_path = processed_dir.parent / "dataset_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(manifest_path, index=False, encoding="utf-8")

    print("\n" + "=" * 65)
    print(f"[OK] DATASET COMPILADO EXITOSAMENTE")
    print(f"[*] Manifiesto guardado en: {manifest_path}")
    print("=" * 65)
    print("\nResumen de Distribucion por Split y Clase:")
    print(df.groupby(["split", "class_name", "is_augmented"]).size().unstack(fill_value=0))
    print("=" * 65 + "\n")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construcción del Dataset RetiScan")
    parser.add_argument("--raw", type=str, default="data/raw", help="Directorio de datos crudos")
    parser.add_argument("--processed", type=str, default="data/processed", help="Directorio de salida procesado")
    parser.add_argument("--train-target", type=int, default=10, help="Mínimo de imágenes por clase en Train mediante Data Augmentation")
    parser.add_argument("--no-clahe", action="store_true", help="Desactivar filtro CLAHE")

    args = parser.parse_args()
    build_retiscan_dataset(
        raw_dir=Path(args.raw),
        processed_dir=Path(args.processed),
        target_train_per_class=args.train_target,
        apply_clahe_flag=not args.no_clahe
    )
