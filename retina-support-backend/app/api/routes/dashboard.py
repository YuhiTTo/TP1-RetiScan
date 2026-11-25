from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account
)

from app.models.account import Account

from app.schemas.dashboard import DashboardSummaryResponse

from app.services.dashboard_service import get_dashboard_summary


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK
)
def read_dashboard_summary(
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):
    return get_dashboard_summary(
        db=db,
        establishment_id=(
            institutional_account.id_establecimiento
        )
    )