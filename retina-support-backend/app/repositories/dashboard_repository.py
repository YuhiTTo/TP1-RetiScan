from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.evaluation import RetinalEvaluation
from app.models.report import Report


def count_patients_by_establishment(
    db: Session,
    establishment_id: int
) -> int:

    statement = select(
        func.count(Patient.id_paciente)
    ).where(
        Patient.id_establecimiento == establishment_id
    )

    return db.execute(statement).scalar_one()


def count_evaluations_by_status(
    db: Session,
    establishment_id: int
) -> dict[str, int]:

    statement = select(
        func.count(
            case(
                (RetinalEvaluation.estado == "FINALIZADA", 1)
            )
        ).label("evaluaciones_realizadas"),

        func.count(
            case(
                (RetinalEvaluation.estado == "PENDIENTE", 1)
            )
        ).label("evaluaciones_pendientes")

    ).where(
        RetinalEvaluation.id_establecimiento == establishment_id
    )

    result = db.execute(statement).one()

    return {
        "evaluaciones_realizadas": result.evaluaciones_realizadas,
        "evaluaciones_pendientes": result.evaluaciones_pendientes
    }


def count_reports_by_establishment(
    db: Session,
    establishment_id: int
) -> int:

    statement = (
        select(func.count(Report.id_reporte))
        .join(
            RetinalEvaluation,
            Report.id_evaluacion == RetinalEvaluation.id_evaluacion
        )
        .where(
            RetinalEvaluation.id_establecimiento == establishment_id
        )
    )

    return db.execute(statement).scalar_one()


def get_recent_evaluations(
    db: Session,
    establishment_id: int
):

    statement = (
        select(RetinalEvaluation, Patient)
        .join(
            Patient,
            Patient.id_paciente == RetinalEvaluation.id_paciente
        )
        .where(
            RetinalEvaluation.id_establecimiento == establishment_id,
            Patient.id_establecimiento == establishment_id
        )
        .order_by(
            RetinalEvaluation.fecha_evaluacion.desc(),
            RetinalEvaluation.id_evaluacion.desc()
        )
        .limit(7)
    )

    return db.execute(statement).all()