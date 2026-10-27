from pathlib import Path
import json

import numpy as np
import tensorflow as tf

from app.services.preprocessing_service import prepare_rd_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RD_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "RD"
    / "efficientnetb3_se"
    / "efficientnetb3_se_finetune_best.keras"
)

RD_CALIBRATION_PATH = (
    PROJECT_ROOT
    / "results"
    / "calibration"
    / "rd_temperature_scaling.json"
)

REVIEW_POLICY_PATH = (
    PROJECT_ROOT
    / "results"
    / "calibration"
    / "review_policy.json"
)


RD_LABELS = {
    0: "Sin indicios de Retinopatía Diabética",
    1: "Leve",
    2: "Moderada",
    3: "Severa",
    4: "Proliferativa",
}


rd_model = tf.keras.models.load_model(
    RD_MODEL_PATH,
    compile=False
)


with open(
    RD_CALIBRATION_PATH,
    "r",
    encoding="utf-8"
) as file:
    rd_calibration = json.load(file)


with open(
    REVIEW_POLICY_PATH,
    "r",
    encoding="utf-8"
) as file:
    review_policy = json.load(file)


RD_TEMPERATURE = float(
    rd_calibration["temperature"]
)

RD_REVIEW_THRESHOLD = float(
    review_policy[
        "diabetic_retinopathy"
    ]["review_threshold"]
)


def calibrate_rd_scores(
    raw_scores: np.ndarray
) -> np.ndarray:

    eps = 1e-7

    raw_scores = np.clip(
        raw_scores,
        eps,
        1.0
    )

    logits = np.log(
        raw_scores
    )

    logits = (
        logits
        / RD_TEMPERATURE
    )

    logits = (
        logits
        - np.max(logits)
    )

    exp_logits = np.exp(
        logits
    )

    return (
        exp_logits
        / exp_logits.sum()
    )


def predict_rd(
    processed_rgb: np.ndarray
) -> dict:

    model_input = prepare_rd_input(
        processed_rgb
    )

    raw_scores = rd_model.predict(
        model_input,
        verbose=0
    )[0]

    calibrated_scores = (
        calibrate_rd_scores(
            raw_scores
        )
    )

    predicted_class = int(
        np.argmax(
            calibrated_scores
        )
    )

    confidence = float(
        calibrated_scores[
            predicted_class
        ]
    )

    requires_review = bool(
        confidence
        < RD_REVIEW_THRESHOLD
    )

    return {
        "class_id": predicted_class,
        "label": RD_LABELS[
            predicted_class
        ],
        "confidence": confidence,
        "requires_review": requires_review,
    }
