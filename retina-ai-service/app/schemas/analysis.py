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

class ImageQualityChecks(BaseModel):
    claridad: bool | None
    iluminacion: bool | None
    contraste: bool | None
    fov: bool


class ImageQualityMetrics(BaseModel):
    clarity_gradient_p90: float | None
    dark_ratio_30: float | None
    contrast_cv: float | None
    fov_area_ratio: float | None
    fov_width_ratio: float | None
    fov_height_ratio: float | None
    fov_center_offset: float | None


class ImageQualityResponse(BaseModel):
    id_evaluacion: int
    estado: str

    criterios_fallidos: list[str]

    criterios: ImageQualityChecks

    metricas: ImageQualityMetrics
