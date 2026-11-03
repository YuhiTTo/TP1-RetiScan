from pydantic import BaseModel, Field


class AIModelResultResponse(BaseModel):
    estado: str

    resultado: str | None = None

    confianza: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    requiere_revision: bool = False

    detalle_error: str | None = None


class AIAnalysisResponse(BaseModel):
    id_analisis: int
    id_evaluacion: int
    estado: str

    retinopatia_diabetica: AIModelResultResponse
    glaucoma: AIModelResultResponse

    requiere_revision: bool