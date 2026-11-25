from datetime import datetime

from pydantic import BaseModel


class ReportListResponse(BaseModel):
    id_evaluacion: int
    id_paciente: int

    nombres_paciente: str
    apellidos_paciente: str

    fecha_evaluacion: datetime
    ojo_evaluado: str

    medico_responsable: str

    tiene_reporte: bool
    id_reporte: int | None = None
    fecha_generacion: datetime | None = None
