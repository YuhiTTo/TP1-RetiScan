import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.models.report import Report
from app.services.ai_results_service import (
    AIResultsNotAvailableError,
    get_ai_evaluation_results,
)
from app.services.report_data_service import prepare_report_data
from app.services.report_pdf_service import generate_report_pdf
from app.services.report_storage_service import (
    upload_report_pdf,
    delete_report_pdf,
    StorageDeleteError,
)
from app.services.report_reconciliation_service import (
    check_report_persistence,
)

logger = logging.getLogger(__name__)


class ReportUpdateEvaluationNotFoundError(Exception):
    pass


class ReportUpdateNotFinalizedError(Exception):
    pass


class ReportUpdateResultsNotAvailableError(Exception):
    pass


class ReportUpdateCommitUncertainError(Exception):
    pass


class ReportUpdateCleanupFailedError(Exception):
    pass


def update_observation_and_report(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    observation: str,
) -> RetinalEvaluation:
    """Guarda la observacion y actualiza el PDF solo si existe."""

    new_path = None
    old_path = None
    commit_started = False

    try:
        evaluation = db.execute(
            select(RetinalEvaluation)
            .where(
                RetinalEvaluation.id_evaluacion == evaluation_id,
                RetinalEvaluation.id_establecimiento == establishment_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if evaluation is None:
            raise ReportUpdateEvaluationNotFoundError()

        if evaluation.estado != "FINALIZADA":
            raise ReportUpdateNotFinalizedError()

        try:
            get_ai_evaluation_results(
                db=db,
                establishment_id=establishment_id,
                evaluation_id=evaluation_id,
            )
        except AIResultsNotAvailableError as exc:
            raise ReportUpdateResultsNotAvailableError() from exc

        # Guardar el mismo texto no genera una version nueva.
        if evaluation.observacion_medica == observation:
            db.rollback()
            return evaluation

        report = db.execute(
            select(Report).where(
                Report.id_evaluacion == evaluation_id
            )
        ).scalar_one_or_none()

        evaluation.observacion_medica = observation

        # Si no existe PDF, solo se actualiza la observacion.
        if report is not None:
            next_version = report.version + 1

            data, image_bytes = prepare_report_data(
                db=db,
                establishment_id=establishment_id,
                evaluation_id=evaluation_id,
                report_version=next_version,
            )

            pdf_bytes = generate_report_pdf(
                data=data,
                retinography_bytes=image_bytes,
            )

            # Nueva ruta: no sobrescribe el archivo anterior.
            new_path = upload_report_pdf(
                content=pdf_bytes,
                evaluation_id=evaluation_id,
            )

            old_path = report.ruta_pdf_s3

            report.ruta_pdf_s3 = new_path
            report.version = next_version
            report.fecha_generacion = datetime.now()

        db.flush()
        commit_started = True
        db.commit()

    except Exception as exc:
        db.rollback()

        if commit_started:
            if new_path is not None:
                try:
                    status = check_report_persistence(
                        establishment_id,
                        evaluation_id,
                        new_path,
                    )
                    logger.error(
                        "Confirmacion incierta del reporte %s: %s",
                        evaluation_id,
                        status.value,
                    )
                except Exception:
                    logger.exception(
                        "No se pudo reconciliar el reporte %s.",
                        evaluation_id,
                    )

            # Ante commit incierto, conservar ambos objetos.
            raise ReportUpdateCommitUncertainError(
                "No se pudo confirmar la actualizacion. "
                "Debe verificarse PostgreSQL antes de reintentar."
            ) from exc

        if new_path is not None:
            try:
                delete_report_pdf(new_path)
            except StorageDeleteError as cleanup_error:
                logger.exception(
                    "No se pudo limpiar el nuevo PDF %s.",
                    evaluation_id,
                )
                raise ReportUpdateCleanupFailedError(
                    "Fallo la actualizacion y la limpieza en S3."
                ) from cleanup_error

        raise

    # Eliminar el PDF antiguo solo despues del commit.
    if old_path is not None:
        try:
            delete_report_pdf(old_path)
        except StorageDeleteError:
            logger.exception(
                "El reporte se actualizo, pero quedo pendiente "
                "eliminar el PDF anterior de la evaluacion %s.",
                evaluation_id,
            )

    db.refresh(evaluation)

    return evaluation
