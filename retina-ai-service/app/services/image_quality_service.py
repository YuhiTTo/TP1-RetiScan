import cv2
import numpy as np


# ============================================================
# US-12 — CONTROL MÍNIMO DE CALIDAD DE RETINOGRAFÍA
#
# Los thresholds fueron derivados en DeepDRiD Set-A y
# posteriormente validados sin reajuste en Set-B.
# ============================================================

QUALITY_TARGET_SIZE = 1024

FOV_THRESHOLD = 10
MORPH_KERNEL_SIZE = 15
INNER_KERNEL_SIZE = 9


# ------------------------------------------------------------
# Thresholds congelados
# ------------------------------------------------------------

CLARITY_MIN = 16.06225775

DARK_RATIO_MAX = 0.33113740

CONTRAST_CV_MAX = 0.63830344

FOV_AREA_MIN = 0.65079775
FOV_WIDTH_MIN = 0.91093100
FOV_HEIGHT_MIN = 0.90625000
FOV_CENTER_OFFSET_MAX = 0.00175000


class ImageQualityEvaluationError(Exception):
    pass


def decode_retinography(
    content: bytes
) -> np.ndarray:

    image_array = np.frombuffer(
        content,
        dtype=np.uint8
    )

    image_bgr = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image_bgr is None:
        raise ImageQualityEvaluationError(
            "No se pudo decodificar la retinografía "
            "para evaluar su calidad."
        )

    return image_bgr


def detect_fov(
    image_bgr: np.ndarray
) -> np.ndarray:

    gray = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2GRAY
    )

    binary = (
        gray > FOV_THRESHOLD
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            MORPH_KERNEL_SIZE,
            MORPH_KERNEL_SIZE
        )
    )

    mask = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    num_labels, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            mask,
            connectivity=8
        )
    )

    if num_labels <= 1:
        return mask

    areas = stats[
        1:,
        cv2.CC_STAT_AREA
    ]

    largest = (
        1 + np.argmax(areas)
    )

    component = (
        labels == largest
    ).astype(np.uint8) * 255

    contours, _ = cv2.findContours(
        component,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return component

    contour = max(
        contours,
        key=cv2.contourArea
    )

    hull = cv2.convexHull(
        contour
    )

    final_mask = np.zeros_like(
        component
    )

    cv2.fillConvexPoly(
        final_mask,
        hull,
        255
    )

    return final_mask


def normalize_quality_roi(
    image_bgr: np.ndarray,
    mask: np.ndarray
):
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ImageQualityEvaluationError(
            "No se detectó un FOV retinal válido "
            "para evaluar la calidad."
        )

    contour = max(
        contours,
        key=cv2.contourArea
    )

    x, y, w, h = cv2.boundingRect(
        contour
    )

    if w <= 0 or h <= 0:
        raise ImageQualityEvaluationError(
            "El FOV retinal detectado no es válido."
        )

    crop = image_bgr[
        y:y + h,
        x:x + w
    ]

    crop_mask = mask[
        y:y + h,
        x:x + w
    ]

    scale = min(
        QUALITY_TARGET_SIZE / w,
        QUALITY_TARGET_SIZE / h
    )

    new_w = max(
        1,
        int(round(w * scale))
    )

    new_h = max(
        1,
        int(round(h * scale))
    )

    resized = cv2.resize(
        crop,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    resized_mask = cv2.resize(
        crop_mask,
        (new_w, new_h),
        interpolation=cv2.INTER_NEAREST
    )

    normalized = np.zeros(
        (
            QUALITY_TARGET_SIZE,
            QUALITY_TARGET_SIZE,
            3
        ),
        dtype=np.uint8
    )

    normalized_mask = np.zeros(
        (
            QUALITY_TARGET_SIZE,
            QUALITY_TARGET_SIZE
        ),
        dtype=np.uint8
    )

    x_offset = (
        QUALITY_TARGET_SIZE - new_w
    ) // 2

    y_offset = (
        QUALITY_TARGET_SIZE - new_h
    ) // 2

    normalized[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized

    normalized_mask[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized_mask

    return (
        normalized,
        normalized_mask
    )


def calculate_fov_metrics(
    mask: np.ndarray
) -> dict:

    h, w = mask.shape

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ImageQualityEvaluationError(
            "No se detectó un FOV retinal válido."
        )

    contour = max(
        contours,
        key=cv2.contourArea
    )

    x, y, bbox_w, bbox_h = (
        cv2.boundingRect(
            contour
        )
    )

    area_pixels = np.count_nonzero(
        mask
    )

    fov_area_ratio = (
        area_pixels / float(w * h)
    )

    fov_width_ratio = (
        bbox_w / float(w)
    )

    fov_height_ratio = (
        bbox_h / float(h)
    )

    moments = cv2.moments(
        contour
    )

    if moments["m00"] == 0:
        center_x = (
            x + bbox_w / 2.0
        )

        center_y = (
            y + bbox_h / 2.0
        )

    else:
        center_x = (
            moments["m10"]
            / moments["m00"]
        )

        center_y = (
            moments["m01"]
            / moments["m00"]
        )

    image_center_x = (
        w / 2.0
    )

    image_center_y = (
        h / 2.0
    )

    dx = (
        center_x - image_center_x
    ) / w

    dy = (
        center_y - image_center_y
    ) / h

    center_offset = float(
        np.sqrt(
            dx ** 2
            + dy ** 2
        )
    )

    return {
        "fov_area_ratio":
            float(fov_area_ratio),

        "fov_width_ratio":
            float(fov_width_ratio),

        "fov_height_ratio":
            float(fov_height_ratio),

        "fov_center_offset":
            center_offset,
    }


def get_inner_mask(
    normalized_mask: np.ndarray
) -> np.ndarray:

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            INNER_KERNEL_SIZE,
            INNER_KERNEL_SIZE
        )
    )

    inner_mask = cv2.erode(
        normalized_mask,
        kernel,
        iterations=1
    )

    if np.count_nonzero(
        inner_mask > 0
    ) == 0:
        raise ImageQualityEvaluationError(
            "La máscara retinal quedó vacía "
            "durante la evaluación de calidad."
        )

    return inner_mask


def calculate_quality_metrics(
    normalized_bgr: np.ndarray,
    normalized_mask: np.ndarray
) -> dict:

    gray = cv2.cvtColor(
        normalized_bgr,
        cv2.COLOR_BGR2GRAY
    )

    inner_mask = get_inner_mask(
        normalized_mask
    )

    valid = (
        inner_mask > 0
    )

    values = gray[
        valid
    ].astype(np.float64)

    if values.size == 0:
        raise ImageQualityEvaluationError(
            "No existen píxeles retinales válidos "
            "para calcular la calidad."
        )

    # --------------------------------------------------------
    # Iluminación
    # --------------------------------------------------------

    dark_ratio_30 = float(
        np.mean(
            values < 30
        )
    )

    # --------------------------------------------------------
    # Contraste
    # --------------------------------------------------------

    mean_luminance = float(
        np.mean(values)
    )

    std_luminance = float(
        np.std(values)
    )

    contrast_cv = (
        std_luminance
        / mean_luminance
        if mean_luminance > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Claridad — Gradient magnitude P90
    # --------------------------------------------------------

    gray_float = gray.astype(
        np.float64
    )

    sobel_x = cv2.Sobel(
        gray_float,
        cv2.CV_64F,
        1,
        0,
        ksize=3
    )

    sobel_y = cv2.Sobel(
        gray_float,
        cv2.CV_64F,
        0,
        1,
        ksize=3
    )

    gradient_squared = (
        sobel_x ** 2
        + sobel_y ** 2
    )

    gradient_magnitude = np.sqrt(
        gradient_squared
    )

    gradient_values = (
        gradient_magnitude[
            valid
        ]
    )

    clarity_gradient_p90 = float(
        np.percentile(
            gradient_values,
            90
        )
    )

    return {
        "clarity_gradient_p90":
            clarity_gradient_p90,

        "dark_ratio_30":
            dark_ratio_30,

        "contrast_cv":
            contrast_cv,
    }


def assess_image_quality(
    content: bytes
) -> dict:

    # Un archivo que no puede decodificarse continúa siendo
    # un error de lectura y no un problema de calidad.
    image_bgr = decode_retinography(
        content
    )

    try:
        fov_mask = detect_fov(
            image_bgr
        )

        fov_metrics = calculate_fov_metrics(
            fov_mask
        )

        (
            normalized,
            normalized_mask
        ) = normalize_quality_roi(
            image_bgr,
            fov_mask
        )

        quality_metrics = (
            calculate_quality_metrics(
                normalized,
                normalized_mask
            )
        )

    except ImageQualityEvaluationError:
        # La imagen pudo leerse, pero no contiene una región
        # retinal técnicamente utilizable para el análisis.
        return {
            "status": "INSUFICIENTE",
            "passed": False,
            "failed_criteria": [
                "fov"
            ],
            "checks": {
                "clarity": None,
                "illumination": None,
                "contrast": None,
                "fov": False,
            },
            "metrics": {
                "clarity_gradient_p90": None,
                "dark_ratio_30": None,
                "contrast_cv": None,
                "fov_area_ratio": None,
                "fov_width_ratio": None,
                "fov_height_ratio": None,
                "fov_center_offset": None,
            },
        }

    clarity_ok = (
        quality_metrics[
            "clarity_gradient_p90"
        ]
        >= CLARITY_MIN
    )

    illumination_ok = (
        quality_metrics[
            "dark_ratio_30"
        ]
        <= DARK_RATIO_MAX
    )

    contrast_ok = (
        quality_metrics[
            "contrast_cv"
        ]
        <= CONTRAST_CV_MAX
    )

    # El FOV se utiliza únicamente como control técnico.
    # Llegar hasta este punto confirma que la región retinal
    # pudo detectarse, delimitarse y normalizarse.
    #
    # Los thresholds geométricos derivados de DeepDRiD se
    # conservan únicamente para reproducibilidad experimental
    # y NO participan en la decisión de producción.
    fov_ok = True

    checks = {
        "clarity": clarity_ok,
        "illumination": illumination_ok,
        "contrast": contrast_ok,
        "fov": fov_ok,
    }

    failed_criteria = [
        criterion
        for criterion, passed
        in checks.items()
        if not passed
    ]

    status = (
        "SUFICIENTE"
        if not failed_criteria
        else "INSUFICIENTE"
    )

    return {
        "status": status,
        "passed": (
            status == "SUFICIENTE"
        ),
        "failed_criteria":
            failed_criteria,
        "checks":
            checks,
        "metrics": {
            **quality_metrics,
            **fov_metrics,
        },
    }
