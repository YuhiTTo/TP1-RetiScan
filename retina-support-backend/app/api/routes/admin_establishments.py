from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import (get_db, require_admin)
from app.models.account import Account
from app.repositories.establishment_repository import (get_establishments, get_establishment_by_id)
from app.repositories.account_repository import (get_account_by_establishment_id)
from app.schemas.establishment import (EstablishmentAdminResponse, EstablishmentAdminDetailResponse, EstablishmentAdminUpdate)
from app.services.admin_establishment_service import (update_establishment_by_admin, EstablishmentNotFoundError, InstitutionalAccountNotFoundError,AccountEmailAlreadyExistsError)


router = APIRouter(
    prefix="/api/v1/admin/establishments",
    tags=["Admin - Establishments"]
)


@router.get(
    "",
    response_model=list[EstablishmentAdminResponse],
    status_code=status.HTTP_200_OK
)
def list_establishments(
    db: Session = Depends(get_db),
    admin_account: Account = Depends(require_admin)
):

    return get_establishments(
        db=db
    )

@router.get(
    "/{id_establecimiento}",
    response_model=EstablishmentAdminDetailResponse,
    status_code=status.HTTP_200_OK
)
def get_establishment_detail(
    id_establecimiento: int,
    db: Session = Depends(get_db),
    admin_account: Account = Depends(require_admin)
):

    establishment = get_establishment_by_id(
        db=db,
        id_establecimiento=id_establecimiento
    )

    if establishment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establecimiento no encontrado."
        )

    account = get_account_by_establishment_id(
        db=db,
        id_establecimiento=id_establecimiento
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta institucional no encontrada."
        )

    return EstablishmentAdminDetailResponse(
        id_establecimiento=establishment.id_establecimiento,
        codigo_institucional=establishment.codigo_institucional,
        nombre=establishment.nombre,
        ruc=establishment.ruc,
        direccion=establishment.direccion,
        distrito=establishment.distrito,
        telefono=establishment.telefono,
        estado=establishment.estado,
        fecha_registro=establishment.fecha_registro,
        correo_electronico=account.correo_electronico
    )

@router.patch(
    "/{id_establecimiento}",
    response_model=EstablishmentAdminResponse,
    status_code=status.HTTP_200_OK
)
def update_establishment(
    id_establecimiento: int,
    data: EstablishmentAdminUpdate,
    db: Session = Depends(get_db),
    admin_account: Account = Depends(require_admin)
):

    try:

        return update_establishment_by_admin(
            db=db,
            id_establecimiento=id_establecimiento,
            data=data
        )

    except EstablishmentNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establecimiento no encontrado."
        )

    except InstitutionalAccountNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La cuenta institucional del establecimiento no fue encontrada."
        )

    except AccountEmailAlreadyExistsError:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo institucional ya se encuentra registrado."
        )