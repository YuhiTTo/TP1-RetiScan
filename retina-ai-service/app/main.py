from fastapi import FastAPI, HTTPException, status

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ModelResult,
)
from app.services.inference_service import predict_retiscan
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

    except ValueError as error:
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
        estado="COMPLETADO",
        retinopatia_diabetica=ModelResult(
            resultado=rd_result["label"],
            confianza=rd_result["confidence"],
        ),
        glaucoma=ModelResult(
            resultado=glaucoma_result["label"],
            confianza=glaucoma_result["confidence"],
        ),
        requiere_revision=result[
            "requires_review"
        ],
    )