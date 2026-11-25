from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retinography import Retinography


def get_retinography_by_evaluation(
    db: Session,
    evaluation_id: int
) -> Retinography | None:

    statement = select(Retinography).where(
        Retinography.id_evaluacion == evaluation_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()