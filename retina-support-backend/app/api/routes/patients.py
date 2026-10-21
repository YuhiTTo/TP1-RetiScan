from fastapi import (APIRouter,Depends,HTTPException,Query,status)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account
)
from app.models.account import Account
from app.schemas.patient import (PatientCreate, PatientResponse, PatientUpdate)
from app.services.patient_service import (PatientAlreadyExistsError, PatientNotFoundError, create_patient, find_patients, get_patient, update_patient)


router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"]
)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED
)
def register_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        patient = create_patient(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            data=data
        )

    except PatientAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El paciente ya se encuentra registrado "
                "en el establecimiento."
            )
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo completar el registro del paciente."
        )

    return patient

@router.get(
    "",
    response_model=list[PatientResponse],
    status_code=status.HTTP_200_OK
)
def search_registered_patients(
    search: str = Query(
        ...,
        min_length=1,
        max_length=150
    ),
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    patients = find_patients(
        db=db,
        establishment_id=(
            institutional_account.id_establecimiento
        ),
        search=search
    )

    return patients

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK
)
def get_registered_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        patient = get_patient(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            patient_id=patient_id
        )

    except PatientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El paciente no fue encontrado."
        )

    return patient

@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK
)
def update_registered_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        patient = update_patient(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            patient_id=patient_id,
            data=data
        )

    except PatientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El paciente no fue encontrado."
        )

    except PatientAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe otro paciente con ese número "
                "de documento en el establecimiento."
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo actualizar la información del paciente."
        )

    return patient