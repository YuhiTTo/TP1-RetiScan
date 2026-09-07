"""
=============================================================================
RETISCAN - MÓDULO DE PREPROCESAMIENTO DE RETINOGRAFÍAS (OE1 / OE2)
Sistema de Soporte Clínico CAD - Centro Oftalmológico V.E.R.
=============================================================================
Este módulo implementa el pipeline de preparación de imágenes de fondo de ojo:
1. Detección y recorte de la Región de Interés (ROI) eliminando bordes negros.
2. Ecualización adaptativa de histograma limitada por contraste (CLAHE).
3. Redimensionamiento bicúbico a 224x224 (requerido por DenseNet121).
4. Normalización de tensores en rango [0.0, 1.0].
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Union, Optional


def crop_retina_roi(image: np.ndarray, tolerance: int = 15) -> np.ndarray:
    """
    Detecta automáticamente la región circular de la retina (ROI) y recorta
    los márgenes negros o artefactos externos no informativos.
    
    Args:
        image: Imagen en formato BGR o RGB (numpy array).
        tolerance: Umbral de intensidad mínima para considerar fondo negro.
        
    Returns:
        Imagen recortada en forma cuadrada conteniendo la retina centrada.
    """
    if image is None or image.size == 0:
        raise ValueError("La imagen proporcionada está vacía o es inválida.")

    # Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Máscara binaria para umbralizar el fondo negro
    mask = gray > tolerance

    # Si la máscara detecta píxeles suficientes
    if not np.any(mask):
        return image

    # Obtener coordenadas de los píxeles activos
    coords = np.argwhere(mask)
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    # Recorte inicial
    cropped = image[y_min:y_max + 1, x_min:x_max + 1]

    # Convertir a cuadrado mediante padding reflectivo para evitar distorsión
    h, w = cropped.shape[:2]
    if h == w:
        return cropped

    diff = abs(h - w)
    pad_before = diff // 2
    pad_after = diff - pad_before

    if h < w:
        # Altura menor: agregar padding vertical
        pad_width = ((pad_before, pad_after), (0, 0), (0, 0)) if cropped.ndim == 3 else ((pad_before, pad_after), (0, 0))
    else:
        # Ancho menor: agregar padding horizontal
        pad_width = ((0, 0), (pad_before, pad_after), (0, 0)) if cropped.ndim == 3 else ((0, 0), (pad_before, pad_after))

    square_cropped = np.pad(cropped, pad_width, mode='constant', constant_values=0)
    return square_cropped


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Aplica el algoritmo CLAHE (Contrast Limited Adaptive Histogram Equalization)
    sobre el canal de luminosidad (L en espacio CIE LAB).
    
    Este filtro atenúa las variaciones de iluminación entre cuadrantes,
    reduce el impacto del sesgo demográfico de pigmentación retiniana
    y resalta microaneurismas, exudados duros y bordes del disco óptico.
    
    Args:
        image: Imagen BGR (numpy array uint8).
        clip_limit: Límite de amplificación de contraste (evita sobre-ruido).
        tile_grid_size: Tamaño de las teselas locales (rejilla de ecualización).
        
    Returns:
        Imagen BGR con contraste y luminosidad ecualizados.
    """
    if len(image.shape) != 3:
        raise ValueError("Se requiere una imagen en formato color de 3 canales.")

    # Convertir a espacio LAB
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Crear y aplicar CLAHE en el canal L
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l_channel)

    # Recombinar canales y retornar a BGR
    merged_lab = cv2.merge((cl, a_channel, b_channel))
    enhanced_bgr = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)
    return enhanced_bgr


def resize_and_normalize(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> Tuple[np.ndarray, np.ndarray]:
    """
    Redimensiona la imagen a la resolución de entrada requerida por DenseNet121
    y genera la versión normalizada [0.0, 1.0].
    
    Args:
        image: Imagen en uint8.
        target_size: Tupla (ancho, alto), por defecto (224, 224).
        
    Returns:
        Tuple de (image_uint8, image_normalized_float32):
        - image_uint8: Adecuada para visualización y guardado en disco.
        - image_normalized_float32: Tensor normalizado para alimentar la CNN.
    """
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_CUBIC)
    normalized = (resized.astype(np.float32) / 255.0)
    return resized, normalized


def preprocess_fundus_image(
    input_path_or_array: Union[str, Path, np.ndarray],
    target_size: Tuple[int, int] = (224, 224),
    apply_clahe_flag: bool = True,
    clip_limit: float = 2.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ejecuta el flujo integral de preprocesamiento sobre una retinografía:
    Carga -> Recorte ROI -> CLAHE -> Redimensión 224x224 -> Normalización.
    
    Args:
        input_path_or_array: Ruta del archivo de imagen o array BGR.
        target_size: Dimensión de salida (224, 224).
        apply_clahe_flag: Booleano para activar el filtro CLAHE.
        clip_limit: Umbral de contraste para CLAHE.
        
    Returns:
        (image_uint8, image_float32)
    """
    if isinstance(input_path_or_array, (str, Path)):
        img = cv2.imread(str(input_path_or_array))
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen desde: {input_path_or_array}")
    else:
        img = input_path_or_array.copy()

    # 1. Recorte de ROI
    roi = crop_retina_roi(img)

    # 2. Ecualización adaptativa CLAHE
    if apply_clahe_flag:
        enhanced = apply_clahe(roi, clip_limit=clip_limit)
    else:
        enhanced = roi

    # 3. Redimensión y normalización
    img_uint8, img_float = resize_and_normalize(enhanced, target_size=target_size)
    return img_uint8, img_float


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Preprocesamiento de Retinografías - RetiScan")
    parser.add_argument("--input", type=str, required=True, help="Ruta de imagen de entrada")
    parser.add_argument("--output", type=str, required=True, help="Ruta de guardado de imagen preprocesada")
    parser.add_argument("--clahe", action="store_true", default=True, help="Aplicar filtro CLAHE")
    args = parser.parse_args()

    uint8_img, _ = preprocess_fundus_image(args.input, apply_clahe_flag=args.clahe)
    cv2.imwrite(args.output, uint8_img)
    print(f"Imagen procesada exitosamente guardada en: {args.output}")
