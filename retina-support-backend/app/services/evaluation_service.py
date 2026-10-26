from datetime import datetime, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.repositories.doctor_repository import get_doctor_by_full_name
from app.repositories.patient_repository import get_patient_by_id
from app.repositories.evaluation_repository import get_evaluations_by_patient
from app.schemas.evaluation import EvaluationCreate


class EvaluationPatientNotFoundError(Exception):
    pass


class EvaluationDoctorNotFoundError(Exception):
    pass


def create_evaluation(
    db: Session,
    establishment_id: int,
    patient_id: int,
    data: EvaluationCreate
) -> RetinalEvaluation:

    # Verificar que el paciente exista
    # y pertenezca al establecimiento activo
    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )

    if patient is None:
        raise EvaluationPatientNotFoundError()

    # Buscar al médico responsable
    # dentro del mismo establecimiento
    doctor = get_doctor_by_full_name(
        db=db,
        establishment_id=establishment_id,
        full_name=data.medico_responsable
    )

    if doctor is None:
        raise EvaluationDoctorNotFoundError()

    evaluation = RetinalEvaluation(
        id_paciente=patient.id_paciente,
        id_medico=doctor.id_medico,
        id_establecimiento=establishment_id,
        fecha_evaluacion=datetime.combine(
            data.fecha_evaluacion,
            time.min
        ),
        ojo_evaluado=data.ojo_evaluado,
        estado="PENDIENTE"
    )

    try:
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        return evaluation

    except IntegrityError:
        db.rollback()
        raise

def get_patient_evaluations(
    db: Session,
    establishment_id: int,
    patient_id: int
) -> list[RetinalEvaluation]:

    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )

    if patient is None:
        raise EvaluationPatientNotFoundError()

    return get_evaluations_by_patient(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )