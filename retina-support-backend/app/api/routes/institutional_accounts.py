from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.account import Account
from app.schemas.institutional_account import (
    InstitutionalAccountCreate,
    InstitutionalAccountResponse
)
from app.services.institutional_account_service import (
    AccountEmailAlreadyExistsError,
    InstitutionalCodeAlreadyExistsError,
    create_institutional_account
)


router = APIRouter(
    prefix="/api/v1/institutional-accounts",
    tags=["Institutional Accounts"]
)


@router.post(
    "",
    response_model=InstitutionalAccountResponse,
    status_code=status.HTTP_201_CREATED
)
def register_institutional_account(
    data: InstitutionalAccountCreate,
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin)
):

    try:
        establishment, account = create_institutional_account(
            db=db,
            data=data
        )

    except InstitutionalCodeAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un establecimiento con ese "
                "código institucional."
            )
        )

    except AccountEmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe una cuenta con ese correo electrónico."
            )
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo completar el registro por datos duplicados."
        )

    return InstitutionalAccountResponse(
        message="Cuenta institucional registrada correctamente.",
        id_establecimiento=establishment.id_establecimiento,
        codigo_institucional=establishment.codigo_institucional,
        nombre_establecimiento=establishment.nombre,
        id_cuenta=account.id_cuenta,
        correo_electronico=account.correo_electronico,
        tipo_cuenta=account.tipo_cuenta
    )