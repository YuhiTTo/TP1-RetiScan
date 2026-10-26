from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account
)
from app.models.account import Account
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse
)
from app.services.evaluation_service import (
    EvaluationDoctorNotFoundError,
    EvaluationPatientNotFoundError,
    get_patient_evaluations,
    create_evaluation
)


router = APIRouter(
    prefix="/api/v1/patients",
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
    response_model=list[EvaluationResponse],
    status_code=status.HTTP_200_OK
)
def list_patient_evaluations(
    patient_id: int,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_institutional_account)
):
    try:
        return get_patient_evaluations(
            db=db,
            establishment_id=current_account.id_establecimiento,
            patient_id=patient_id
        )

    except EvaluationPatientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado."
        )