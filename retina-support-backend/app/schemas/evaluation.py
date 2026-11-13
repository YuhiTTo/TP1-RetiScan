from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class EvaluationCreate(BaseModel):
    fecha_evaluacion: date

    ojo_evaluado: str = Field(
        min_length=2,
        max_length=2
    )

    medico_responsable: str = Field(
        min_length=3,
        max_length=150
    )

    @field_validator("ojo_evaluado")
    @classmethod
    def validate_eye(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in {"OD", "OI"}:
            raise ValueError(
                "El ojo evaluado debe ser OD u OI."
            )

        return value


class EvaluationResponse(BaseModel):
    id_evaluacion: int
    id_paciente: int
    id_medico: int
    id_establecimiento: int

    fecha_evaluacion: datetime
    ojo_evaluado: str

    observacion_medica: str | None
    prioridad_sugerida: str | None

    estado: str
    fecha_creacion: datetime
    fecha_finalizacion: datetime | None

class EvaluationDetailResponse(BaseModel):
    id_evaluacion: int

    fecha_evaluacion: datetime
    ojo_evaluado: str
    estado: str

    id_paciente: int
    numero_documento: str
    nombres_paciente: str
    apellidos_paciente: str
    fecha_nacimiento: date
    sexo: str

    id_medico: int
    medico_responsable: str

class EvaluationListResponse(EvaluationResponse):
    medico_responsable: str