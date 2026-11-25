from datetime import datetime

from pydantic import BaseModel


class DashboardRecentEvaluationResponse(BaseModel):
    id_evaluacion: int
    nombres_paciente: str
    apellidos_paciente: str
    fecha_evaluacion: datetime
    ojo_evaluado: str
    estado: str


class DashboardSummaryResponse(BaseModel):
    total_pacientes: int
    evaluaciones_realizadas: int
    evaluaciones_pendientes: int
    reportes_generados: int
    evaluaciones_recientes: list[
        DashboardRecentEvaluationResponse
    ]