from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.account import Account
from app.schemas.admin_evaluations import (
    AdminEvaluationsPage,
    AdminEvaluationsSummary
)
from app.services.admin_evaluations_service import (
    list_admin_evaluations,
    summarize_admin_evaluations
)


router = APIRouter(
    prefix="/api/v1/admin/evaluations",
    tags=["Admin - Evaluations"]
)


@router.get(
    "",
    response_model=AdminEvaluationsPage
)
def get_evaluations(
    evaluation_id: int | None = Query(default=None, gt=0),
    establishment_id: int | None = Query(default=None, gt=0),
    estado: Literal["PENDIENTE", "FINALIZADA"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin)
):
    return list_admin_evaluations(
        db=db,
        evaluation_id=evaluation_id,
        establishment_id=establishment_id,
        estado=estado,
        page=page,
        page_size=page_size
    )


@router.get(
    "/summary",
    response_model=AdminEvaluationsSummary
)
def get_evaluations_summary(
    db: Session = Depends(get_db),
    admin: Account = Depends(require_admin)
):
    return summarize_admin_evaluations(db)
