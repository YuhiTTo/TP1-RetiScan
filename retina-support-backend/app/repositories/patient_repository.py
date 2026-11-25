from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.evaluation import RetinalEvaluation


def get_patient_by_document(
    db: Session,
    establishment_id: int,
    document_number: str
) -> Patient | None:

    statement = select(Patient).where(
        Patient.id_establecimiento == establishment_id,
        Patient.numero_documento == document_number.strip()
    )

    return db.execute(
        statement
    ).scalar_one_or_none()

def get_patient_by_id(
    db: Session,
    establishment_id: int,
    patient_id: int
) -> Patient | None:

    statement = select(Patient).where(
        Patient.id_paciente == patient_id,
        Patient.id_establecimiento == establishment_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def search_patients(
    db: Session,
    establishment_id: int,
    search: str
) -> list[dict]:

    search_value = search.strip()

    # Obtener la fecha de la evaluación más reciente
    # de cada paciente del establecimiento.
    latest_evaluation = (
        select(
            RetinalEvaluation.id_paciente.label("id_paciente"),
            func.max(
                RetinalEvaluation.fecha_evaluacion
            ).label("ultima_evaluacion")
        )
        .where(
            RetinalEvaluation.id_establecimiento == establishment_id
        )
        .group_by(
            RetinalEvaluation.id_paciente
        )
        .subquery()
    )

    statement = (
        select(
            Patient,
            latest_evaluation.c.ultima_evaluacion
        )
        .outerjoin(
            latest_evaluation,
            latest_evaluation.c.id_paciente == Patient.id_paciente
        )
        .where(
            Patient.id_establecimiento == establishment_id,
            or_(
                Patient.numero_documento.ilike(f"%{search_value}%"),
                Patient.nombres.ilike(f"%{search_value}%"),
                Patient.apellidos.ilike(f"%{search_value}%")
            )
        )
        .order_by(
            Patient.fecha_registro.desc(),
            Patient.id_paciente.desc()
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "id_paciente": patient.id_paciente,
            "id_establecimiento": patient.id_establecimiento,
            "numero_documento": patient.numero_documento,
            "nombres": patient.nombres,
            "apellidos": patient.apellidos,
            "fecha_nacimiento": patient.fecha_nacimiento,
            "sexo": patient.sexo,
            "telefono": patient.telefono,
            "correo": patient.correo,
            "direccion": patient.direccion,
            "estado": patient.estado,
            "fecha_registro": patient.fecha_registro,
            "ultima_evaluacion": ultima_evaluacion
        }
        for patient, ultima_evaluacion in rows
    ]
