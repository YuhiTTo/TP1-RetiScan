from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class EstablishmentAdminResponse(BaseModel):
    id_establecimiento: int
    codigo_institucional: str
    nombre: str
    ruc: str | None
    direccion: str
    distrito: str
    telefono: str
    estado: bool
    fecha_registro: datetime

    model_config = {
        "from_attributes": True
    }

class EstablishmentAdminUpdate(BaseModel):

    nombre: str = Field(
        min_length=2,
        max_length=150
    )

    ruc: str | None = Field(
        default=None,
        min_length=11,
        max_length=11
    )

    direccion: str = Field(
        min_length=2,
        max_length=200
    )

    distrito: str = Field(
        min_length=2,
        max_length=100
    )

    telefono: str = Field(
        min_length=5,
        max_length=20
    )

    estado: bool

    correo_electronico: EmailStr

    nueva_password: str | None = Field(
        default=None,
        min_length=8
    )

class EstablishmentAdminDetailResponse(BaseModel):
    id_establecimiento: int
    codigo_institucional: str
    nombre: str
    ruc: str | None
    direccion: str
    distrito: str
    telefono: str
    estado: bool
    fecha_registro: datetime
    correo_electronico: str