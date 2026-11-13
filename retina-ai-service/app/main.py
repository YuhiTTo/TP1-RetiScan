from fastapi import FastAPI, HTTPException, status

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ImageQualityChecks,
    ImageQualityMetrics,
    ImageQualityResponse,
    ModelResult,
)
from app.services.inference_service import (
    RetinalPreprocessingError,
    predict_retiscan,
)

from app.services.image_quality_service import (
    ImageQualityEvaluationError,
    assess_image_quality,
)

from app.services.storage_service import (
    StorageDownloadError,
    download_retinography,
)


app = FastAPI(
    title="RetiScan AI Service",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "RetiScan AI Service"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_retinography(
    request: AnalysisRequest
):
    try:
        content = download_retinography(
            request.ruta_s3
        )

        result = predict_retiscan(
            content
        )

    except StorageDownloadError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "No se pudo obtener la retinografía "
                "desde Amazon S3."
            )
        )

    except RetinalPreprocessingError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )

    rd_result = result[
        "diabetic_retinopathy"
    ]

    glaucoma_result = result[
        "glaucoma"
    ]

    return AnalysisResponse(
        id_evaluacion=request.id_evaluacion,
        estado=result["status"],
        retinopatia_diabetica=ModelResult(
            estado=rd_result["estado"],
            resultado=rd_result["label"],
            confianza=rd_result["confidence"],
            requiere_revision=rd_result[
                "requires_review"
            ],
            detalle_error=rd_result[
                "detail_error"
            ],
        ),
        glaucoma=ModelResult(
            estado=glaucoma_result["estado"],
            resultado=glaucoma_result["label"],
            confianza=glaucoma_result[
                "confidence"
            ],
            requiere_revision=glaucoma_result[
                "requires_review"
            ],
            detalle_error=glaucoma_result[
                "detail_error"
            ],
        ),
        requiere_revision=result[
            "requires_review"
        ],
    )

@app.post(
    "/api/v1/quality",
    response_model=ImageQualityResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_retinography_quality(
    request: AnalysisRequest
):
    try:
        content = download_retinography(
            request.ruta_s3
        )

    except StorageDownloadError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "No se pudo obtener la retinografía "
                "desde Amazon S3."
            )
        )

    try:
        result = assess_image_quality(
            content
        )

    except ImageQualityEvaluationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )

    checks = result["checks"]
    metrics = result["metrics"]

    return ImageQualityResponse(
        id_evaluacion=request.id_evaluacion,
        estado=result["status"],
        criterios_fallidos=result[
            "failed_criteria"
        ],
        criterios=ImageQualityChecks(
            claridad=checks["clarity"],
            iluminacion=checks["illumination"],
            contraste=checks["contrast"],
            fov=checks["fov"],
        ),
        metricas=ImageQualityMetrics(
            clarity_gradient_p90=metrics[
                "clarity_gradient_p90"
            ],
            dark_ratio_30=metrics[
                "dark_ratio_30"
            ],
            contrast_cv=metrics[
                "contrast_cv"
            ],
            fov_area_ratio=metrics[
                "fov_area_ratio"
            ],
            fov_width_ratio=metrics[
                "fov_width_ratio"
            ],
            fov_height_ratio=metrics[
                "fov_height_ratio"
            ],
            fov_center_offset=metrics[
                "fov_center_offset"
            ],
        ),
    )
