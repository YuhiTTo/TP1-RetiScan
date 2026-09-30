from pydantic import BaseModel, EmailStr, Field

class EstablishmentCreate(BaseModel):
    codigo_institucional: str = Field(min_length=2, max_length=50)
    nombre: str = Field(min_length=2, max_length=150)
    ruc: str | None = Field(default=None, min_length=11, max_length=11)
    direccion: str = Field(min_length=2, max_length=200)
    distrito: str = Field(min_length=2, max_length=100)
    telefono: str = Field(min_length=5, max_length=20)


class InstitutionalAccountData(BaseModel):
    correo_electronico: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre_mostrado: str | None = Field(
        default=None,
        max_length=150
    )


class InstitutionalAccountCreate(BaseModel):
    establecimiento: EstablishmentCreate
    cuenta: InstitutionalAccountData


class InstitutionalAccountResponse(BaseModel):
    message: str
    id_establecimiento: int
    codigo_institucional: str
    nombre_establecimiento: str
    id_cuenta: int
    correo_electronico: str
    tipo_cuenta: str