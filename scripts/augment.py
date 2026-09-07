"""
=============================================================================
RETISCAN - MÓDULO DE DATA AUGMENTATION Y BALANCEO (OE1)
Sistema de Soporte Clínico CAD - Centro Oftalmológico V.E.R.
=============================================================================
Este módulo implementa transformaciones controladas de aumento de datos
clínicamente seguras para mitigar el desbalance de clases (Glaucoma, Retinopatía
Diabética y Ojo Sano), sin alterar la anatomía diagnóstica retiniana.
"""

import cv2
import numpy as np
import random
from typing import List, Tuple


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Aplica rotación controlada respecto al centro óptico de la retina."""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return rotated


def horizontal_flip(image: np.ndarray) -> np.ndarray:
    """Aplica inversión horizontal (simula ojo contralateral sin alterar patología)."""
    return cv2.flip(image, 1)


def vertical_flip(image: np.ndarray) -> np.ndarray:
    """Aplica inversión vertical."""
    return cv2.flip(image, 0)


def adjust_brightness_contrast(image: np.ndarray, alpha: float = 1.0, beta: int = 0) -> np.ndarray:
    """
    Modifica sutilmente el contraste (alpha) y el brillo (beta).
    alpha: 0.9 a 1.15
    beta: -15 a 15
    """
    adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return adjusted


def random_zoom(image: np.ndarray, zoom_factor: float = 1.05) -> np.ndarray:
    """Aplica un zoom sutil (95% a 105%) conservando el centrado del disco óptico."""
    h, w = image.shape[:2]
    if zoom_factor == 1.0:
        return image

    if zoom_factor > 1.0:
        # Acercamiento: recortar centro y redimensionar
        new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
        top = (h - new_h) // 2
        left = (w - new_w) // 2
        cropped = image[top:top + new_h, left:left + new_w]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    else:
        # Alejamiento: redimensionar y rellenar con borde reflectivo
        new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        pad_top = (h - new_h) // 2
        pad_bottom = h - new_h - pad_top
        pad_left = (w - new_w) // 2
        pad_right = w - new_w - pad_left
        padded = cv2.copyMakeBorder(resized, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REFLECT)
        return padded


def apply_random_augmentation(image: np.ndarray) -> np.ndarray:
    """
    Aplica una combinación estocástica de transformaciones permitidas
    manteniendo la validez clínica de la imagen.
    """
    aug = image.copy()

    # 1. Rotación aleatoria en [-25, 25] grados
    angle = random.uniform(-25.0, 25.0)
    aug = rotate_image(aug, angle)

    # 2. Inversión horizontal con 50% de probabilidad
    if random.random() > 0.5:
        aug = horizontal_flip(aug)

    # 3. Inversión vertical con 25% de probabilidad
    if random.random() > 0.75:
        aug = vertical_flip(aug)

    # 4. Variación de brillo y contraste sutil
    alpha = random.uniform(0.90, 1.12)
    beta = random.randint(-12, 12)
    aug = adjust_brightness_contrast(aug, alpha=alpha, beta=beta)

    # 5. Zoom sutil
    zoom = random.uniform(0.96, 1.06)
    aug = random_zoom(aug, zoom)

    return aug


def generate_augmented_batch(image: np.ndarray, count: int) -> List[np.ndarray]:
    """Genera 'count' variaciones sintéticas a partir de una única imagen retiniana."""
    results = []
    for _ in range(count):
        results.append(apply_random_augmentation(image))
    return results
