from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.models.patient import Patient
from app.models.doctor import Doctor


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

def get_evaluations_by_establishment(
    db: Session,
    establishment_id: int
) -> list[tuple[RetinalEvaluation, Patient, Doctor]]:

    statement = (
        select(
            RetinalEvaluation,
            Patient,
            Doctor
        )
        .join(
            Patient,
            Patient.id_paciente == RetinalEvaluation.id_paciente
        )
        .join(
            Doctor,
            Doctor.id_medico == RetinalEvaluation.id_medico
        )
        .where(
            RetinalEvaluation.id_establecimiento == establishment_id,
            Patient.id_establecimiento == establishment_id,
            Doctor.id_establecimiento == establishment_id
        )
        .order_by(
            RetinalEvaluation.fecha_evaluacion.desc(),
            RetinalEvaluation.id_evaluacion.desc()
        )
    )

    result = db.execute(statement).all()

    return [
        (row[0], row[1], row[2])
        for row in result
    ]