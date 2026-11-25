from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.services.report_update_service import (
    ReportUpdateEvaluationNotFoundError,
    ReportUpdateNotFinalizedError,
    ReportUpdateResultsNotAvailableError,
    update_observation_and_report,
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
    observation: str,
) -> RetinalEvaluation:
    """Conserva la interfaz de US-17 e integra US-20."""

    try:
        return update_observation_and_report(
            db=db,
            establishment_id=establishment_id,
            evaluation_id=evaluation_id,
            observation=observation,
        )

    except ReportUpdateEvaluationNotFoundError as exc:
        raise MedicalObservationNotFoundError() from exc

    except ReportUpdateNotFinalizedError as exc:
        raise MedicalObservationNotFinalizedError() from exc

    except ReportUpdateResultsNotAvailableError as exc:
        raise MedicalObservationResultsNotAvailableError() from exc
