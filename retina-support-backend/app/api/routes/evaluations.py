from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import ( get_db, require_institutional_account )
from app.models.account import Account
from app.models.doctor import Doctor
from app.schemas.evaluation import ( EvaluationCreate, EvaluationResponse, EvaluationListResponse, EvaluationDetailResponse )
from app.services.evaluation_service import ( EvaluationDoctorNotFoundError, EvaluationPatientNotFoundError, EvaluationNotFoundError, get_patient_evaluations, get_evaluation_detail, create_evaluation )


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Evaluations"]
)

detail_router = APIRouter(
    prefix="/api/v1/evaluations",
    tags=["Evaluations"]
)


@router.post(
    "/{patient_id}/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED
)
def register_evaluation(
    patient_id: int,
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        evaluation = create_evaluation(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            patient_id=patient_id,
            data=data
        )

    except EvaluationPatientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El paciente no fue encontrado."
        )

    except EvaluationDoctorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "El médico responsable no se encuentra "
                "registrado en el establecimiento."
            )
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar la evaluación retiniana."
        )

    return evaluation

@router.get(
    "/{patient_id}/evaluations",
    response_model=list[EvaluationListResponse],
    status_code=status.HTTP_200_OK
)
def list_patient_evaluations(
    patient_id: int,
    db: Session = Depends(get_db),
    current_account: Account = Depends(
        require_institutional_account
    )
):
    try:

        evaluations = get_patient_evaluations(
            db=db,
            establishment_id=current_account.id_establecimiento,
            patient_id=patient_id
        )

        response = []

        for evaluation in evaluations:

            doctor = db.get(
                Doctor,
                evaluation.id_medico
            )

            medico_responsable = (
                f"{doctor.nombres} {doctor.apellidos}"
                if doctor
                else "Médico no disponible"
            )

            response.append({
                "id_evaluacion": evaluation.id_evaluacion,
                "id_paciente": evaluation.id_paciente,
                "id_medico": evaluation.id_medico,
                "id_establecimiento": (
                    evaluation.id_establecimiento
                ),
                "fecha_evaluacion": (
                    evaluation.fecha_evaluacion
                ),
                "ojo_evaluado": (
                    evaluation.ojo_evaluado
                ),
                "observacion_medica": (
                    evaluation.observacion_medica
                ),
                "prioridad_sugerida": (
                    evaluation.prioridad_sugerida
                ),
                "estado": evaluation.estado,
                "fecha_creacion": (
                    evaluation.fecha_creacion
                ),
                "fecha_finalizacion": (
                    evaluation.fecha_finalizacion
                ),
                "medico_responsable": (
                    medico_responsable
                )
            })

        return response

    except EvaluationPatientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado."
        )

@detail_router.get(
    "/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    status_code=status.HTTP_200_OK
)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_account: Account = Depends(
        require_institutional_account
    )
):

    try:

        evaluation, patient, doctor = (
            get_evaluation_detail(
                db=db,
                establishment_id=(
                    current_account.id_establecimiento
                ),
                evaluation_id=evaluation_id
            )
        )

    except EvaluationNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación no encontrada."
        )

    except EvaluationPatientNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado."
        )

    except EvaluationDoctorNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico responsable no encontrado."
        )

    return EvaluationDetailResponse(
        id_evaluacion=evaluation.id_evaluacion,

        fecha_evaluacion=evaluation.fecha_evaluacion,
        ojo_evaluado=evaluation.ojo_evaluado,
        estado=evaluation.estado,

        id_paciente=patient.id_paciente,
        numero_documento=patient.numero_documento,
        nombres_paciente=patient.nombres,
        apellidos_paciente=patient.apellidos,
        fecha_nacimiento=patient.fecha_nacimiento,
        sexo=patient.sexo,

        id_medico=doctor.id_medico,

        medico_responsable=(
            f"{doctor.nombres} {doctor.apellidos}"
        )
    )