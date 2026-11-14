
from pydantic import BaseModel, Field


class StoredModelResultResponse(BaseModel):
    estado: str
    resultado: str
    confianza: float = Field(ge=0.0, le=1.0)
    requiere_revision: bool | None = None


class StoredRetinographyResponse(BaseModel):
    id_retinografia: int
    nombre_archivo: str
    formato: str
    ancho_px: int
    alto_px: int


class AIEvaluationResultsResponse(BaseModel):
    id_evaluacion: int
    id_analisis: int
    estado: str

    retinografia: StoredRetinographyResponse

    retinopatia_diabetica: StoredModelResultResponse
    glaucoma: StoredModelResultResponse

    requiere_revision: bool | None = None
    prioridad_sugerida: str | None = None

    resumen: str | None = None
    aviso_soporte_clinico: str
