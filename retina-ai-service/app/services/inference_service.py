import tensorflow as tf

# Configurar memoria de la GPU antes de cargar los modelos
physical_gpus = tf.config.list_physical_devices("GPU")

for gpu in physical_gpus:
    try:
        tf.config.experimental.set_memory_growth(gpu, True)
        print(f"[GPU] Memory growth habilitado: {gpu.name}")
    except RuntimeError as error:
        raise RuntimeError(
            "No se pudo configurar memory_growth antes "
            "de inicializar la GPU."
        ) from error

# Importar servicios después de configurar la GPU
from app.services.preprocessing_service import preprocess_retinal_fov
from app.services.rd_inference_service import predict_rd
from app.services.glaucoma_inference_service import predict_glaucoma

class RetinalPreprocessingError(Exception):
    pass

def predict_retiscan(
    content: bytes
) -> dict:

    try:
        processed_rgb = preprocess_retinal_fov(
            content
        )

    except Exception as error:
        raise RetinalPreprocessingError(
            "No se pudo preparar la retinografía "
            "para el análisis."
        ) from error

    try:
        rd_data = predict_rd(
            processed_rgb
        )

        rd_result = {
            "estado": "COMPLETADO",
            "label": rd_data["label"],
            "confidence": rd_data["confidence"],
            "requires_review": rd_data[
                "requires_review"
            ],
            "tiempo_inferencia_ms": rd_data[
                "tiempo_inferencia_ms"
            ],
            "detail_error": None
        }

    except Exception:
        rd_result = {
            "estado": "ERROR",
            "label": None,
            "confidence": None,
            "requires_review": False,
            "tiempo_inferencia_ms": None,
            "detail_error": (
                "No se pudo completar el análisis "
                "de Retinopatía Diabética."
            )
        }

    try:
        glaucoma_data = predict_glaucoma(
            processed_rgb
        )

        glaucoma_result = {
            "estado": "COMPLETADO",
            "label": glaucoma_data["label"],
            "confidence": glaucoma_data[
                "confidence"
            ],
            "requires_review": glaucoma_data[
                "requires_review"
            ],
            "tiempo_inferencia_ms": glaucoma_data[
                "tiempo_inferencia_ms"
            ],
            "detail_error": None
        }

    except Exception:
        glaucoma_result = {
            "estado": "ERROR",
            "label": None,
            "confidence": None,
            "requires_review": False,
            "tiempo_inferencia_ms": None,
            "detail_error": (
                "No se pudo completar el análisis "
                "de Glaucoma."
            )
        }

    successful_models = sum([
        rd_result["estado"] == "COMPLETADO",
        glaucoma_result["estado"] == "COMPLETADO"
    ])

    if successful_models == 2:
        status = "COMPLETADO"

    elif successful_models == 1:
        status = "PARCIAL"

    else:
        status = "ERROR"

    requires_review = bool(
        rd_result["requires_review"]
        or glaucoma_result["requires_review"]
    )

    return {
        "status": status,
        "diabetic_retinopathy": rd_result,
        "glaucoma": glaucoma_result,
        "requires_review": requires_review
    }