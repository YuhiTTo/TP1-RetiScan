import cv2
import numpy as np
import tensorflow as tf

IMAGE_SIZE = 384


def preprocess_retinal_fov(
    content: bytes,
    output_size: int = IMAGE_SIZE,
    threshold: int = 10,
    margin_ratio: float = 0.02,
    morph_kernel_size: int = 15,
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
        raise ValueError(
            "No se pudo decodificar la retinografía."
        )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB
    )

    gray = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2GRAY
    )

    binary_mask = (
        gray > threshold
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            morph_kernel_size,
            morph_kernel_size
        )
    )

    morph_mask = cv2.morphologyEx(
        binary_mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    num_labels, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            morph_mask,
            connectivity=8
        )
    )

    h_img, w_img = image_rgb.shape[:2]

    if num_labels <= 1:
        mask = morph_mask
        x, y, w, h = 0, 0, w_img, h_img

    else:
        areas = stats[
            1:,
            cv2.CC_STAT_AREA
        ]

        largest_component = (
            1 + np.argmax(areas)
        )

        component_mask = (
            labels == largest_component
        ).astype(np.uint8) * 255

        contours, _ = cv2.findContours(
            component_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            mask = component_mask
            x, y, w, h = 0, 0, w_img, h_img

        else:
            largest_contour = max(
                contours,
                key=cv2.contourArea
            )

            hull = cv2.convexHull(
                largest_contour
            )

            mask = np.zeros_like(
                component_mask
            )

            cv2.fillConvexPoly(
                mask,
                hull,
                255
            )

            x, y, w, h = cv2.boundingRect(
                hull
            )

    margin_x = int(w * margin_ratio)
    margin_y = int(h * margin_ratio)

    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)
    x2 = min(w_img, x + w + margin_x)
    y2 = min(h_img, y + h + margin_y)

    masked_rgb = cv2.bitwise_and(
        image_rgb,
        image_rgb,
        mask=mask
    )

    crop = masked_rgb[
        y1:y2,
        x1:x2
    ]

    crop_h, crop_w = crop.shape[:2]
    max_dim = max(crop_h, crop_w)

    padded = np.zeros(
        (max_dim, max_dim, 3),
        dtype=crop.dtype
    )

    y_offset = (max_dim - crop_h) // 2
    x_offset = (max_dim - crop_w) // 2

    padded[
        y_offset:y_offset + crop_h,
        x_offset:x_offset + crop_w
    ] = crop

    processed = cv2.resize(
        padded,
        (output_size, output_size),
        interpolation=cv2.INTER_AREA
    )

    return processed


def prepare_rd_input(
    processed_rgb: np.ndarray
) -> np.ndarray:

    image = processed_rgb.astype(
        np.float32
    )

    image = np.expand_dims(
        image,
        axis=0
    )

    return image


def prepare_glaucoma_input(
    processed_rgb: np.ndarray
) -> np.ndarray:

    image = processed_rgb.astype(
        np.float32
    )

    image = (
        tf.keras.applications
        .resnet_v2
        .preprocess_input(
            image
        )
    )

    image = np.expand_dims(
        image,
        axis=0
    )

    return image
