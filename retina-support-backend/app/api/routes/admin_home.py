from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.account import Account
from app.repositories.admin_home_repository import (
    get_admin_home_summary
)
from app.schemas.admin_home import AdminHomeSummary


router = APIRouter(
    prefix="/api/v1/admin/home",
    tags=["Admin - Home"]
)


@router.get(
    "/summary",
    response_model=AdminHomeSummary,
    status_code=status.HTTP_200_OK
)
def read_admin_home_summary(
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin)
):
    """Consulta el resumen administrativo de RetiScan."""

    return get_admin_home_summary(db)
