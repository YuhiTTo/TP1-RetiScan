from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    id_evaluacion: int = Field(gt=0)
    ruta_s3: str = Field(min_length=1)


class ModelResult(BaseModel):
    estado: str

    resultado: str | None = None

    confianza: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    requiere_revision: bool = False

    detalle_error: str | None = None


class AnalysisResponse(BaseModel):
    id_evaluacion: int
    estado: str

    retinopatia_diabetica: ModelResult
    glaucoma: ModelResult

    requiere_revision: bool