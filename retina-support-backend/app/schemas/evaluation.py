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

    @field_validator(
        "medico_responsable",
        mode="before"
    )
    @classmethod
    def validate_doctor_name(cls, value):
        if not isinstance(value, str):
            raise ValueError(
                "Ingrese nombres y apellidos del medico."
            )

        value = " ".join(value.strip().split())

        if len(value.split()) < 2:
            raise ValueError(
                "Ingrese nombres y apellidos del medico."
            )

        return value


class EvaluationUpdate(EvaluationCreate):
    pass


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
    observacion_medica: str | None

    id_paciente: int
    numero_documento: str
    nombres_paciente: str
    apellidos_paciente: str
    fecha_nacimiento: date
    sexo: str

    id_medico: int
    medico_responsable: str

class EvaluationHistoryModelResult(BaseModel):
    resultado: str
    confianza: float = Field(ge=0, le=1)


class EvaluationListResponse(EvaluationResponse):
    medico_responsable: str
    retinopatia_diabetica: EvaluationHistoryModelResult | None = None
    glaucoma: EvaluationHistoryModelResult | None = None


class EvaluationSummaryResponse(BaseModel):
    id_evaluacion: int
    id_paciente: int

    nombres_paciente: str
    apellidos_paciente: str

    fecha_evaluacion: datetime
    ojo_evaluado: str

    medico_responsable: str
    estado: str


class MedicalObservationUpdate(BaseModel):
    observacion_medica: str = Field(
        min_length=1,
        max_length=1000
    )

    @field_validator("observacion_medica", mode="before")
    @classmethod
    def validate_observation(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class MedicalObservationResponse(BaseModel):
    id_evaluacion: int
    observacion_medica: str
    estado: str


class EvaluationFinalizeRequest(BaseModel):
    observacion_medica: str | None = Field(
        default=None,
        max_length=1000
    )

    @field_validator("observacion_medica", mode="before")
    @classmethod
    def normalize_observation(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class EvaluationFinalizeResponse(BaseModel):
    id_evaluacion: int
    estado: str
    observacion_medica: str | None
    fecha_finalizacion: datetime
