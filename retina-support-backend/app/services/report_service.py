from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import RetinalEvaluation
from app.models.report import Report
from app.services.report_data_service import (
    prepare_report_data,
    ReportEvaluationNotFoundError,
    ReportEvaluationNotReadyError,
)
from app.services.report_pdf_service import generate_report_pdf
from app.services.report_reconciliation_service import (
    check_report_persistence,
    ReportPersistenceStatus,
)
from app.services.report_storage_service import (
    upload_report_pdf,
    delete_report_pdf,
    StorageDeleteError,
)


logger = logging.getLogger(__name__)


class ReportAlreadyExistsError(Exception):
    pass


class ReportCleanupFailedError(Exception):
    pass


class ReportCommitUncertainError(Exception):
    pass


def generate_initial_report(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
) -> Report:
    """Genera el primer PDF solo si el medico lo solicita."""

    s3_path: str | None = None
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
            raise ReportEvaluationNotFoundError()

        if evaluation.estado != "FINALIZADA":
            raise ReportEvaluationNotReadyError()

        existing = db.execute(
            select(Report).where(
                Report.id_evaluacion == evaluation_id
            )
        ).scalar_one_or_none()

        if existing is not None:
            raise ReportAlreadyExistsError()

        data, image_bytes = prepare_report_data(
            db=db,
            establishment_id=establishment_id,
            evaluation_id=evaluation_id,
            report_version=1,
        )

        pdf_bytes = generate_report_pdf(
            data=data,
            retinography_bytes=image_bytes,
        )

        s3_path = upload_report_pdf(
            content=pdf_bytes,
            evaluation_id=evaluation_id,
        )

        report = Report(
            id_evaluacion=evaluation_id,
            ruta_pdf_s3=s3_path,
            fecha_generacion=datetime.now(),
            version=1,
        )

        db.add(report)

        # Detectar errores de insercion antes del commit.
        db.flush()

        # A partir de aqui, el resultado puede ser incierto.
        commit_started = True
        db.commit()

    except Exception as exc:
        db.rollback()

        if commit_started:
            try:
                verification = check_report_persistence(
                    establishment_id=establishment_id,
                    evaluation_id=evaluation_id,
                    uploaded_s3_path=s3_path,
                )
            except Exception:
                logger.exception(
                    "Error inesperado durante la reconciliacion "
                    "del reporte de la evaluacion %s.",
                    evaluation_id,
                )
                verification = ReportPersistenceStatus.UNAVAILABLE

            logger.error(
                "Confirmacion incierta del reporte de la "
                "evaluacion %s. Verificacion: %s. "
                "Se conserva el PDF para evitar perdida de datos.",
                evaluation_id,
                verification.value,
            )

            raise ReportCommitUncertainError(
                "No se recibio confirmacion del registro "
                "del reporte. Estado de verificacion: "
                f"{verification.value}. "
                "Consulte el estado del reporte antes "
                "de intentar generarlo nuevamente."
            ) from exc

        if s3_path is not None:
            try:
                delete_report_pdf(s3_path)

            except StorageDeleteError as cleanup_error:
                logger.exception(
                    "Falló la limpieza del reporte PDF "
                    "de la evaluación %s.",
                    evaluation_id,
                )
                raise ReportCleanupFailedError(
                    "Falló el registro del reporte y no se "
                    "pudo completar la limpieza en S3."
                ) from cleanup_error

        raise

    db.refresh(report)
    return report
