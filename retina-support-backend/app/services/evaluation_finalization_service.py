from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.services.ai_results_service import (
    AIResultsNotAvailableError,
    get_ai_evaluation_results,
)


class EvaluationFinalizationNotFoundError(Exception):
    pass


class EvaluationAlreadyFinalizedError(Exception):
    pass


class EvaluationInvalidStateError(Exception):
    pass


class EvaluationFinalizationResultsNotAvailableError(Exception):
    pass


def finalize_evaluation(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    observation: str | None
) -> RetinalEvaluation:

    try:
        statement = (
            select(RetinalEvaluation)
            .where(
                RetinalEvaluation.id_evaluacion == evaluation_id,
                RetinalEvaluation.id_establecimiento == establishment_id
            )
            .with_for_update()
        )

        evaluation = db.execute(
            statement
        ).scalar_one_or_none()

        if evaluation is None:
            raise EvaluationFinalizationNotFoundError()

        if evaluation.estado == "FINALIZADA":
            raise EvaluationAlreadyFinalizedError()

        if evaluation.estado != "PENDIENTE":
            raise EvaluationInvalidStateError()

        try:
            get_ai_evaluation_results(
                db=db,
                establishment_id=establishment_id,
                evaluation_id=evaluation_id
            )
        except AIResultsNotAvailableError as exc:
            raise (
                EvaluationFinalizationResultsNotAvailableError()
            ) from exc

        evaluation.observacion_medica = observation
        evaluation.estado = "FINALIZADA"
        evaluation.fecha_finalizacion = datetime.now()

        db.commit()
        db.refresh(evaluation)

        return evaluation

    except Exception:
        db.rollback()
        raise
