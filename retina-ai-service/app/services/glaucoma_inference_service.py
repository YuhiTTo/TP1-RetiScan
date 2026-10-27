from pathlib import Path
import json

import numpy as np
import tensorflow as tf

from app.services.preprocessing_service import prepare_glaucoma_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]

GLAUCOMA_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "glaucoma"
    / "resnet50v2"
    / "resnet50v2_finetune_best.keras"
)

GLAUCOMA_CALIBRATION_PATH = (
    PROJECT_ROOT
    / "results"
    / "calibration"
    / "glaucoma_platt_scaling.json"
)

REVIEW_POLICY_PATH = (
    PROJECT_ROOT
    / "results"
    / "calibration"
    / "review_policy.json"
)


GLAUCOMA_LABELS = {
    0: "Bajo riesgo de Glaucoma",
    1: "Alto riesgo de Glaucoma",
}


glaucoma_model = tf.keras.models.load_model(
    GLAUCOMA_MODEL_PATH,
    compile=False
)


with open(
    GLAUCOMA_CALIBRATION_PATH,
    "r",
    encoding="utf-8"
) as file:
    glaucoma_calibration = json.load(file)


with open(
    REVIEW_POLICY_PATH,
    "r",
    encoding="utf-8"
) as file:
    review_policy = json.load(file)


GLAUCOMA_A = float(
    glaucoma_calibration["a"]
)

GLAUCOMA_B = float(
    glaucoma_calibration["b"]
)

GLAUCOMA_RAW_THRESHOLD = float(
    glaucoma_calibration[
        "raw_threshold"
    ]
)

GLAUCOMA_CALIBRATED_THRESHOLD = float(
    glaucoma_calibration[
        "calibrated_threshold"
    ]
)

GLAUCOMA_REVIEW_THRESHOLD = float(
    review_policy[
        "glaucoma"
    ]["review_threshold"]
)


def calibrate_glaucoma_score(
    raw_score: float
) -> float:

    eps = 1e-7

    raw_score = np.clip(
        raw_score,
        eps,
        1.0 - eps
    )

    raw_logit = np.log(
        raw_score
        /
        (1.0 - raw_score)
    )

    calibrated_probability = (
        1.0
        /
        (
            1.0
            + np.exp(
                -(
                    GLAUCOMA_A
                    * raw_logit
                    + GLAUCOMA_B
                )
            )
        )
    )

    return float(
        calibrated_probability
    )


def predict_glaucoma(
    processed_rgb: np.ndarray
) -> dict:

    model_input = prepare_glaucoma_input(
        processed_rgb
    )

    raw_score = float(
        glaucoma_model.predict(
            model_input,
            verbose=0
        )[0][0]
    )

    predicted_class = int(
        raw_score
        >= GLAUCOMA_RAW_THRESHOLD
    )

    calibrated_probability = (
        calibrate_glaucoma_score(
            raw_score
        )
    )

    if (
        calibrated_probability
        >= GLAUCOMA_CALIBRATED_THRESHOLD
    ):
        confidence = (
            calibrated_probability
            - GLAUCOMA_CALIBRATED_THRESHOLD
        ) / (
            1.0
            - GLAUCOMA_CALIBRATED_THRESHOLD
        )

    else:
        confidence = (
            GLAUCOMA_CALIBRATED_THRESHOLD
            - calibrated_probability
        ) / (
            GLAUCOMA_CALIBRATED_THRESHOLD
        )

    confidence = float(
        np.clip(
            confidence,
            0.0,
            1.0
        )
    )

    requires_review = bool(
        confidence
        < GLAUCOMA_REVIEW_THRESHOLD
    )

    return {
        "class_id": predicted_class,
        "label": GLAUCOMA_LABELS[
            predicted_class
        ],
        "confidence": confidence,
        "requires_review": requires_review,
        "raw_score": raw_score,
        "calibrated_probability": (
            calibrated_probability
        ),
    }
