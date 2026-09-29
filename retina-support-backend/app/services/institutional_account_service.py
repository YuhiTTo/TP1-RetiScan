from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.account import Account
from app.models.establishment import Establishment
from app.repositories.account_repository import get_account_by_email
from app.repositories.establishment_repository import (
    get_establishment_by_code
)
from app.schemas.institutional_account import InstitutionalAccountCreate


class InstitutionalCodeAlreadyExistsError(Exception):
    pass


class AccountEmailAlreadyExistsError(Exception):
    pass


def create_institutional_account(
    db: Session,
    data: InstitutionalAccountCreate
) -> tuple[Establishment, Account]:

    codigo = (
        data.establecimiento.codigo_institucional
        .strip()
        .upper()
    )

    email = (
        data.cuenta.correo_electronico
        .strip()
        .lower()
    )

    existing_establishment = get_establishment_by_code(
        db=db,
        codigo_institucional=codigo
    )

    if existing_establishment is not None:
        raise InstitutionalCodeAlreadyExistsError()

    existing_account = get_account_by_email(
        db=db,
        email=email
    )

    if existing_account is not None:
        raise AccountEmailAlreadyExistsError()

    establishment = Establishment(
        codigo_institucional=codigo,
        nombre=data.establecimiento.nombre.strip(),
        ruc=(
            data.establecimiento.ruc.strip()
            if data.establecimiento.ruc
            else None
        ),
        direccion=data.establecimiento.direccion.strip(),
        distrito=data.establecimiento.distrito.strip(),
        telefono=data.establecimiento.telefono.strip(),
        estado=True
    )

    try:
        db.add(establishment)

        # Ejecuta el INSERT sin hacer todavía COMMIT.
        # Así obtenemos id_establecimiento.
        db.flush()

        account = Account(
            id_establecimiento=establishment.id_establecimiento,
            correo_electronico=email,
            password_hash=hash_password(
                data.cuenta.password
            ),
            tipo_cuenta="INSTITUTIONAL",
            nombre_mostrado=(
                data.cuenta.nombre_mostrado.strip()
                if data.cuenta.nombre_mostrado
                else establishment.nombre
            ),
            estado=True
        )

        db.add(account)

        # Las dos operaciones se confirman juntas.
        db.commit()

        db.refresh(establishment)
        db.refresh(account)

        return establishment, account

    except IntegrityError:
        db.rollback()
        raise