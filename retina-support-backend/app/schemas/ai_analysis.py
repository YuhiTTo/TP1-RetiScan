from pydantic import BaseModel, Field


class AIModelResultResponse(BaseModel):
    resultado: str
    confianza: float = Field(
        ge=0.0,
        le=1.0
    )
    requiere_revision: bool


class AIAnalysisResponse(BaseModel):
    id_analisis: int
    id_evaluacion: int
    estado: str

    retinopatia_diabetica: AIModelResultResponse
    glaucoma: AIModelResultResponse

    requiere_revision: bool