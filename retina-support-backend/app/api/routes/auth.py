from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate_account


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    account = authenticate_account(
        db=db,
        email=data.email,
        password=data.password
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales no válidas."
        )

    token = create_access_token(
        subject=str(account.id_cuenta),
        account_type=account.tipo_cuenta,
        establishment_id=account.id_establecimiento
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        account_type=account.tipo_cuenta,
        establishment_id=account.id_establecimiento,
        display_name=account.nombre_mostrado
    )