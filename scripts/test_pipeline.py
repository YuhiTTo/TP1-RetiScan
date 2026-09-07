"""
=============================================================================
RETISCAN - SUITE DE PRUEBAS DEL PIPELINE DE PREPROCESAMIENTO (OE1)
=============================================================================
Verifica la integridad de las funciones de preprocesamiento, aumento y división.
"""

import sys
import unittest
import numpy as np
from pathlib import Path

# Añadir scripts al path
sys.path.insert(0, str(Path(__file__).parent))

from preprocess import crop_retina_roi, apply_clahe, resize_and_normalize, preprocess_fundus_image
from augment import apply_random_augmentation, rotate_image, horizontal_flip
from build_dataset import build_retiscan_dataset


class TestRetiScanDataPipeline(unittest.TestCase):

    def setUp(self):
        # Crear imagen sintética tipo retinografía (círculo rojo-naranja con fondo negro)
        self.dummy_img = np.zeros((300, 400, 3), dtype=np.uint8)
        # Dibujar disco simulando retina
        import cv2
        cv2.circle(self.dummy_img, (200, 150), 120, (30, 80, 200), -1)

    def test_crop_retina_roi(self):
        cropped = crop_retina_roi(self.dummy_img)
        self.assertIsNotNone(cropped)
        # Debe ser cuadrada
        h, w = cropped.shape[:2]
        self.assertEqual(h, w, f"El recorte no es cuadrado: {h} != {w}")

    def test_apply_clahe(self):
        clahe_img = apply_clahe(self.dummy_img)
        self.assertEqual(clahe_img.shape, self.dummy_img.shape)
        self.assertEqual(clahe_img.dtype, np.uint8)

    def test_resize_and_normalize(self):
        uint8_img, norm_img = resize_and_normalize(self.dummy_img, target_size=(224, 224))
        self.assertEqual(uint8_img.shape, (224, 224, 3))
        self.assertEqual(norm_img.shape, (224, 224, 3))
        self.assertTrue(0.0 <= norm_img.min() and norm_img.max() <= 1.0)

    def test_data_augmentation(self):
        aug = apply_random_augmentation(self.dummy_img)
        self.assertEqual(aug.shape, self.dummy_img.shape)
        self.assertEqual(aug.dtype, np.uint8)

    def test_end_to_end_pipeline(self):
        df = build_retiscan_dataset(
            raw_dir=Path("data/raw"),
            processed_dir=Path("data/processed"),
            target_train_per_class=3
        )
        self.assertFalse(df.empty, "El DataFrame del manifiesto no debe estar vacío")
        self.assertTrue(Path("data/dataset_manifest.csv").exists(), "El manifiesto CSV debe existir")


if __name__ == "__main__":
    unittest.main()
