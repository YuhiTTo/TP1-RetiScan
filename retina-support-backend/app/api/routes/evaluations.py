from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sqlalchemy.exc import SQLAlchemyError

from app.services.report_update_service import (
    ReportUpdateCommitUncertainError,
    ReportUpdateCleanupFailedError,
)
from app.services.report_data_service import (
    ReportDataIncompleteError,
)
from app.services.storage_service import (
    StorageConfigurationError,
    StorageUploadError,
    StorageDownloadError,
)

from app.api.dependencies import ( get_db, require_institutional_account )
from app.models.account import Account
from app.models.doctor import Doctor
from app.schemas.evaluation import (
    MedicalObservationUpdate,
    MedicalObservationResponse
)
from app.services.medical_observation_service import (
    MedicalObservationNotFoundError,
    MedicalObservationResultsNotAvailableError,
    MedicalObservationNotFinalizedError,
    save_medical_observation
)
from app.schemas.evaluation import (
    EvaluationCreate, EvaluationUpdate, EvaluationResponse,
    EvaluationListResponse, EvaluationDetailResponse
)
from app.services.evaluation_service import (
    EvaluationDoctorAmbiguousError,
    EvaluationDoctorInactiveError,
    EvaluationDoctorNotFoundError,
    EvaluationPatientNotFoundError,
    EvaluationNotEditableError,
    EvaluationEyeChangeNotAllowedError,
    EvaluationNotFoundError,
    get_patient_evaluations,
    get_evaluation_detail,
    create_evaluation,
    update_evaluation
)


from app.schemas.evaluation import (
    EvaluationFinalizeRequest,
    EvaluationFinalizeResponse,
)
from app.services.evaluation_finalization_service import (
    EvaluationFinalizationNotFoundError,
    EvaluationAlreadyFinalizedError,
    EvaluationInvalidStateError,
    EvaluationFinalizationResultsNotAvailableError,
    finalize_evaluation,
)

from app.services.ai_results_service import (
    AIResultsNotAvailableError,
    get_ai_evaluation_results,
)

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

    except EvaluationDoctorAmbiguousError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Existen varios registros con el mismo "
                "nombre de médico. Verifique su identidad."
            )
        )

    except EvaluationDoctorInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El médico está inactivo en el establecimiento."
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

            rd_history = None
            glaucoma_history = None

            try:
                stored = get_ai_evaluation_results(
                    db=db,
                    establishment_id=current_account.id_establecimiento,
                    evaluation_id=evaluation.id_evaluacion
                )

                rd_history = {
                    "resultado": stored[
                        "retinopatia_diabetica"
                    ]["resultado"],
                    "confianza": stored[
                        "retinopatia_diabetica"
                    ]["confianza"]
                }

                glaucoma_history = {
                    "resultado": stored["glaucoma"]["resultado"],
                    "confianza": stored["glaucoma"]["confianza"]
                }

            except AIResultsNotAvailableError:
                pass

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
                ),
                "retinopatia_diabetica": rd_history,
                "glaucoma": glaucoma_history
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
        observacion_medica=evaluation.observacion_medica,

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


@detail_router.patch(
    "/{evaluation_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK
)
def edit_retinal_evaluation(
    evaluation_id: int,
    data: EvaluationUpdate,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):
    try:
        return update_evaluation(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            evaluation_id=evaluation_id,
            data=data
        )

    except EvaluationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada."
        )

    except EvaluationNotEditableError:
        raise HTTPException(
            status_code=409,
            detail=(
                "La evaluación ya inició el análisis de IA "
                "o no se encuentra pendiente."
            )
        )

    except EvaluationEyeChangeNotAllowedError:
        raise HTTPException(
            status_code=409,
            detail=(
                "No se puede cambiar el ojo evaluado "
                "porque ya existe una retinografía cargada."
            )
        )

    except EvaluationDoctorAmbiguousError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Existen varios registros con el mismo "
                "nombre de médico. Verifique su identidad."
            )
        )

    except EvaluationDoctorInactiveError:
        raise HTTPException(
            status_code=409,
            detail=(
                "El médico está inactivo en el establecimiento."
            )
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar la evaluación."
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo acceder a PostgreSQL."
        )


@detail_router.patch(
    "/{evaluation_id}/medical-observation",
    response_model=MedicalObservationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Cuenta sin permisos"},
        404: {"description": "Evaluación no encontrada"},
        409: {
            "description": (
                "Evaluación sin resultados IA completos "
                "o evaluación no finalizada"
            )
        },
        422: {"description": "Observación inválida"}
    }
)
def update_medical_observation(
    evaluation_id: int,
    data: MedicalObservationUpdate,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):
    try:
        evaluation = save_medical_observation(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            evaluation_id=evaluation_id,
            observation=data.observacion_medica
        )

    except MedicalObservationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La evaluación retiniana no fue encontrada."
        )

    except MedicalObservationResultsNotAvailableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La evaluación todavía no tiene resultados "
                "de inteligencia artificial completos."
            )
        )

    except MedicalObservationNotFinalizedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Solo se puede modificar la observación de una evaluación finalizada."
            )
        )

    except ReportDataIncompleteError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Faltan datos clinicos para actualizar "
                "el reporte PDF."
            ),
        )

    except ReportUpdateCommitUncertainError:
        raise HTTPException(
            status_code=503,
            detail=(
                "No se pudo confirmar la actualizacion. "
                "Consulte el estado antes de reintentar."
            ),
        )

    except ReportUpdateCleanupFailedError:
        raise HTTPException(
            status_code=503,
            detail=(
                "La actualizacion fallo y no se pudo "
                "completar la limpieza del PDF."
            ),
        )

    except StorageConfigurationError:
        raise HTTPException(
            status_code=503,
            detail="Amazon S3 no esta configurado.",
        )

    except (StorageUploadError, StorageDownloadError):
        raise HTTPException(
            status_code=502,
            detail=(
                "No se pudo actualizar el archivo "
                "del reporte en Amazon S3."
            ),
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo acceder a PostgreSQL.",
        )

    return MedicalObservationResponse(
        id_evaluacion=evaluation.id_evaluacion,
        observacion_medica=evaluation.observacion_medica,
        estado=evaluation.estado
    )


@detail_router.post(
    "/{evaluation_id}/finalize",
    response_model=EvaluationFinalizeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Cuenta sin permisos"},
        404: {"description": "Evaluación no encontrada"},
        409: {
            "description": (
                "Evaluación ya finalizada, estado inválido "
                "o resultados IA incompletos"
            )
        },
        422: {"description": "Datos de finalización inválidos"},
    },
)
def finalize_retinal_evaluation(
    evaluation_id: int,
    data: EvaluationFinalizeRequest,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    ),
):
    try:
        evaluation = finalize_evaluation(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            evaluation_id=evaluation_id,
            observation=data.observacion_medica,
        )

    except EvaluationFinalizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La evaluación retiniana no fue encontrada.",
        )

    except EvaluationAlreadyFinalizedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La evaluación ya se encuentra finalizada.",
        )

    except EvaluationInvalidStateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El estado de la evaluación no permite finalizarla.",
        )

    except EvaluationFinalizationResultsNotAvailableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La evaluación todavía no tiene resultados "
                "de inteligencia artificial completos."
            ),
        )

    return EvaluationFinalizeResponse(
        id_evaluacion=evaluation.id_evaluacion,
        estado=evaluation.estado,
        observacion_medica=evaluation.observacion_medica,
        fecha_finalizacion=evaluation.fecha_finalizacion,
    )
