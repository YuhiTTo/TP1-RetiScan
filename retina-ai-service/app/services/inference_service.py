from app.services.preprocessing_service import preprocess_retinal_fov
from app.services.rd_inference_service import predict_rd
from app.services.glaucoma_inference_service import predict_glaucoma


def predict_retiscan(
    content: bytes
) -> dict:

    processed_rgb = preprocess_retinal_fov(
        content
    )

    rd_result = predict_rd(
        processed_rgb
    )

    glaucoma_result = predict_glaucoma(
        processed_rgb
    )

    requires_review = bool(
        rd_result["requires_review"]
        or glaucoma_result["requires_review"]
    )

    return {
        "diabetic_retinopathy": rd_result,
        "glaucoma": glaucoma_result,
        "requires_review": requires_review,
    }
