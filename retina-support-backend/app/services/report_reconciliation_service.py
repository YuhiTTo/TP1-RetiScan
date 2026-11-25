import logging
from enum import Enum

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.evaluation import RetinalEvaluation
from app.models.report import Report


logger = logging.getLogger(__name__)


class ReportPersistenceStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    NOT_FOUND = "NOT_FOUND"
    DIFFERENT_PATH = "DIFFERENT_PATH"
    UNAVAILABLE = "UNAVAILABLE"


def check_report_persistence(
    establishment_id: int,
    evaluation_id: int,
    uploaded_s3_path: str,
) -> ReportPersistenceStatus:
    """Consulta el reporte usando una nueva sesion PostgreSQL.

    No modifica registros ni elimina objetos de Amazon S3.
    """

    try:
        statement = (
            select(Report.ruta_pdf_s3)
            .join(
                RetinalEvaluation,
                Report.id_evaluacion
                == RetinalEvaluation.id_evaluacion,
            )
            .where(
                RetinalEvaluation.id_evaluacion == evaluation_id,
                RetinalEvaluation.id_establecimiento == establishment_id,
            )
        )

        with SessionLocal() as verification_db:
            registered_path = verification_db.execute(
                statement
            ).scalar_one_or_none()

    except SQLAlchemyError:
        logger.exception(
            "No se pudo verificar el reporte de la evaluacion %s.",
            evaluation_id,
        )
        return ReportPersistenceStatus.UNAVAILABLE

    if registered_path is None:
        return ReportPersistenceStatus.NOT_FOUND

    if registered_path == uploaded_s3_path:
        return ReportPersistenceStatus.CONFIRMED

    return ReportPersistenceStatus.DIFFERENT_PATH
