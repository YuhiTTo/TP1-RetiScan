from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.establishment import Establishment
from app.repositories.account_repository import (
    get_account_by_email,
    get_account_by_establishment_id
)
from app.repositories.establishment_repository import (
    get_establishment_by_id
)
from app.schemas.establishment import EstablishmentAdminUpdate


class EstablishmentNotFoundError(Exception):
    pass


class InstitutionalAccountNotFoundError(Exception):
    pass


class AccountEmailAlreadyExistsError(Exception):
    pass


def update_establishment_by_admin(
    db: Session,
    id_establecimiento: int,
    data: EstablishmentAdminUpdate
) -> Establishment:

    # 1. Buscar el establecimiento.
    establishment = get_establishment_by_id(
        db=db,
        id_establecimiento=id_establecimiento
    )

    if establishment is None:
        raise EstablishmentNotFoundError()

    # 2. Buscar su cuenta institucional.
    account = get_account_by_establishment_id(
        db=db,
        id_establecimiento=id_establecimiento
    )

    if account is None:
        raise InstitutionalAccountNotFoundError()

    # 3. Validar que el nuevo correo no pertenezca
    # a otra cuenta.
    email = data.correo_electronico.strip().lower()

    existing_account = get_account_by_email(
        db=db,
        email=email
    )

    if (
        existing_account is not None
        and existing_account.id_cuenta != account.id_cuenta
    ):
        raise AccountEmailAlreadyExistsError()

    # 4. Actualizar establecimiento.
    establishment.nombre = data.nombre.strip()

    establishment.ruc = (
        data.ruc.strip()
        if data.ruc
        else None
    )

    establishment.direccion = data.direccion.strip()
    establishment.distrito = data.distrito.strip()
    establishment.telefono = data.telefono.strip()
    establishment.estado = data.estado

    # 5. Actualizar cuenta institucional.
    account.correo_electronico = email
    account.estado = data.estado
    account.nombre_mostrado = data.nombre.strip()

    # 6. Solo cambiar contraseña si el administrador
    # escribió una nueva.
    if data.nueva_password:
        account.password_hash = hash_password(
            data.nueva_password
        )

    try:
        db.commit()

        db.refresh(establishment)
        db.refresh(account)

        return establishment

    except Exception:
        db.rollback()
        raise