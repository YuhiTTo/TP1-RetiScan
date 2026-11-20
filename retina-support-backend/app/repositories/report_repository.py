from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.report import Report


def get_reports_by_establishment(
    db: Session,
    establishment_id: int
) -> list[tuple[RetinalEvaluation, Patient, Doctor, Report | None]]:

    statement = (
        select(
            RetinalEvaluation,
            Patient,
            Doctor,
            Report
        )
        .join(
            Patient,
            Patient.id_paciente == RetinalEvaluation.id_paciente
        )
        .join(
            Doctor,
            Doctor.id_medico == RetinalEvaluation.id_medico
        )
        .outerjoin(
            Report,
            Report.id_evaluacion == RetinalEvaluation.id_evaluacion
        )
        .where(
            RetinalEvaluation.id_establecimiento == establishment_id,
            RetinalEvaluation.estado == "FINALIZADA",
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
        (row[0], row[1], row[2], row[3])
        for row in result
    ]