from datetime import datetime
from pydantic import BaseModel


class AdminEvaluationItem(BaseModel):
    id_evaluacion: int
    id_establecimiento: int
    establecimiento: str
    fecha_evaluacion: datetime
    ojo_evaluado: str
    estado: str


class AdminEvaluationsPage(BaseModel):
    items: list[AdminEvaluationItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminEvaluationsSummary(BaseModel):
    total_evaluaciones: int
    evaluaciones_pendientes: int
    evaluaciones_finalizadas: int
    establecimientos_con_evaluaciones: int
