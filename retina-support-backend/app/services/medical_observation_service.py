from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.repositories.evaluation_repository import get_evaluation_by_id
from app.services.ai_results_service import (
    AIResultsNotAvailableError,
    get_ai_evaluation_results,
)


class MedicalObservationNotFoundError(Exception):
    pass


class MedicalObservationResultsNotAvailableError(Exception):
    pass


class MedicalObservationNotFinalizedError(Exception):
    pass


def save_medical_observation(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    observation: str
) -> RetinalEvaluation:

    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise MedicalObservationNotFoundError()

    if evaluation.estado != "FINALIZADA":
        raise MedicalObservationNotFinalizedError()

    try:
        get_ai_evaluation_results(
            db=db,
            establishment_id=establishment_id,
            evaluation_id=evaluation_id
        )
    except AIResultsNotAvailableError as exc:
        raise MedicalObservationResultsNotAvailableError() from exc

    evaluation.observacion_medica = observation

    try:
        db.commit()
        db.refresh(evaluation)
    except Exception:
        db.rollback()
        raise

    return evaluation
