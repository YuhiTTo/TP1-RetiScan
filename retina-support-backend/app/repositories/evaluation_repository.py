from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation


def get_evaluation_by_id(
    db: Session,
    establishment_id: int,
    evaluation_id: int
) -> RetinalEvaluation | None:

    statement = select(RetinalEvaluation).where(
        RetinalEvaluation.id_evaluacion == evaluation_id,
        RetinalEvaluation.id_establecimiento == establishment_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()