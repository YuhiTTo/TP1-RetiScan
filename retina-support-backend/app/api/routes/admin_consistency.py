from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.account import Account
from app.schemas.admin_consistency import (
    AdminConsistencyPage,
    AdminConsistencySummary,
)
from app.services.admin_consistency_service import (
    list_admin_consistency,
    summarize_admin_consistency,
)


router = APIRouter(
    prefix="/api/v1/admin/consistency",
    tags=["Admin - Consistency"],
)


@router.get(
    "",
    response_model=AdminConsistencyPage,
)
def get_consistency(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    return list_admin_consistency(
        db=db,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/summary",
    response_model=AdminConsistencySummary,
)
def get_consistency_summary(
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    return summarize_admin_consistency(db)
