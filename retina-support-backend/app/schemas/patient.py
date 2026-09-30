from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


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

    correo: EmailStr | None = None

    direccion: str | None = Field(
        default=None,
        max_length=200
    )

    @field_validator("fecha_nacimiento")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError(
                "La fecha de nacimiento no puede ser futura."
            )

        return value


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