from datetime import datetime, time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.models.doctor import Doctor
from app.repositories.doctor_repository import find_doctors_by_full_name
from app.repositories.patient_repository import get_patient_by_id
from app.repositories.evaluation_repository import ( get_evaluations_by_patient, get_evaluation_by_id )
from app.schemas.evaluation import EvaluationCreate


class EvaluationPatientNotFoundError(Exception):
    pass


class EvaluationDoctorNotFoundError(Exception):
    pass


class EvaluationDoctorAmbiguousError(Exception):
    pass


class EvaluationDoctorInactiveError(Exception):
    pass


class EvaluationNotFoundError(Exception):
    pass

def create_evaluation(
    db: Session,
    establishment_id: int,
    patient_id: int,
    data: EvaluationCreate
) -> RetinalEvaluation:

    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=patient_id
    )

    if patient is None:
        raise EvaluationPatientNotFoundError()

    full_name = " ".join(
        data.medico_responsable.split()
    )

    parts = full_name.split()

    if len(parts) < 2:
        raise ValueError(
            "Ingrese nombres y apellidos del medico."
        )

    if len(parts) == 2:
        nombres = parts[0]
        apellidos = parts[1]
    else:
        nombres = " ".join(parts[:-2])
        apellidos = " ".join(parts[-2:])

    try:
        # Evitar registros simultaneos del mismo nombre
        # en el establecimiento.
        db.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtext(:lock_key))"
            ),
            {
                "lock_key": (
                    f"retiscan:medico:{establishment_id}:"
                    f"{full_name.lower()}"
                )
            }
        )

        doctors = find_doctors_by_full_name(
            db=db,
            establishment_id=establishment_id,
            full_name=full_name
        )

        if len(doctors) > 1:
            raise EvaluationDoctorAmbiguousError()

        if doctors:
            doctor = doctors[0]

            if not doctor.estado:
                raise EvaluationDoctorInactiveError()

        else:
            doctor = Doctor(
                id_establecimiento=establishment_id,
                nombres=nombres,
                apellidos=apellidos,
                estado=True
            )

            db.add(doctor)
            db.flush()

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

        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        return evaluation

    except Exception:
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

def get_evaluation_detail(
    db: Session,
    establishment_id: int,
    evaluation_id: int
):

    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise EvaluationNotFoundError()

    patient = get_patient_by_id(
        db=db,
        establishment_id=establishment_id,
        patient_id=evaluation.id_paciente
    )

    if patient is None:
        raise EvaluationPatientNotFoundError()

    doctor = db.get(
        Doctor,
        evaluation.id_medico
    )

    if doctor is None:
        raise EvaluationDoctorNotFoundError()

    return evaluation, patient, doctor