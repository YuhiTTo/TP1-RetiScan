from datetime import datetime

from pydantic import BaseModel, Field


class AdminHomeEstablishmentActivity(BaseModel):
    id_establecimiento: int
    establecimiento: str
    evaluaciones_ultimos_7_dias: int = Field(ge=0)
    ultima_evaluacion: datetime | None


class AdminHomeSummary(BaseModel):
    total_establecimientos: int = Field(ge=0)
    establecimientos_con_actividad_reciente: int = Field(ge=0)
    actividad_establecimientos: list[
        AdminHomeEstablishmentActivity
    ]
