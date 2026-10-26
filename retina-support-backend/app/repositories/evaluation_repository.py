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

def get_evaluations_by_patient(
    db: Session,
    establishment_id: int,
    patient_id: int
) -> list[RetinalEvaluation]:

    statement = (
        select(RetinalEvaluation)
        .where(
            RetinalEvaluation.id_paciente == patient_id,
            RetinalEvaluation.id_establecimiento == establishment_id
        )
        .order_by(
            RetinalEvaluation.fecha_evaluacion.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )