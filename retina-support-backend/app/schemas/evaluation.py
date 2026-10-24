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