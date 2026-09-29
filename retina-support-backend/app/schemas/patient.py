from datetime import date, datetime

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    numero_documento: str = Field(min_length=5, max_length=20)
    nombres: str = Field(min_length=2, max_length=150)
    apellidos: str = Field(min_length=2, max_length=150)
    fecha_nacimiento: date
    sexo: str = Field(min_length=1, max_length=20)

    telefono: str | None = Field(
        default=None,
        max_length=20
    )

    correo: str | None = Field(
        default=None,
        max_length=255
    )

    direccion: str | None = Field(
        default=None,
        max_length=200
    )


class PatientResponse(BaseModel):
    id_paciente: int
    id_establecimiento: int
    numero_documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    sexo: str
    telefono: str | None
    correo: str | None
    direccion: str | None
    estado: bool
    fecha_registro: datetime