from sqlalchemy.orm import Session

from app.repositories.admin_evaluations_repository import (
    find_admin_evaluations,
    get_admin_evaluations_summary
)
from app.schemas.admin_evaluations import (
    AdminEvaluationItem,
    AdminEvaluationsPage,
    AdminEvaluationsSummary
)


def list_admin_evaluations(
    db: Session,
    evaluation_id: int | None,
    establishment_id: int | None,
    estado: str | None,
    page: int,
    page_size: int
) -> AdminEvaluationsPage:

    total, rows = find_admin_evaluations(
        db=db,
        evaluation_id=evaluation_id,
        establishment_id=establishment_id,
        estado=estado,
        page=page,
        page_size=page_size
    )

    return AdminEvaluationsPage(
        items=[
            AdminEvaluationItem(**row)
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


def summarize_admin_evaluations(
    db: Session
) -> AdminEvaluationsSummary:

    return AdminEvaluationsSummary(
        **get_admin_evaluations_summary(db)
    )
