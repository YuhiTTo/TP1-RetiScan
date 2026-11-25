from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.establishment import Establishment

from app.repositories.evaluation_repository import (
    get_evaluation_by_id,
)
from app.repositories.retinography_repository import (
    get_retinography_by_evaluation,
)
from app.services.ai_results_service import (
    AIResultsNotAvailableError,
    get_ai_evaluation_results,
)
from app.services.storage_service import download_retinography
from app.services.report_pdf_service import ReportPDFData


class ReportEvaluationNotFoundError(Exception):
    pass


class ReportEvaluationNotReadyError(Exception):
    pass


class ReportDataIncompleteError(Exception):
    pass


def prepare_report_data(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    report_version: int = 1,
) -> tuple[ReportPDFData, bytes]:
    """Obtiene datos existentes para generar un reporte PDF."""

    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id,
    )

    if evaluation is None:
        raise ReportEvaluationNotFoundError()

    if evaluation.estado != "FINALIZADA":
        raise ReportEvaluationNotReadyError()

    patient = db.execute(
        select(Patient).where(
            Patient.id_paciente == evaluation.id_paciente,
            Patient.id_establecimiento == establishment_id,
        )
    ).scalar_one_or_none()

    doctor = db.execute(
        select(Doctor).where(
            Doctor.id_medico == evaluation.id_medico,
            Doctor.id_establecimiento == establishment_id,
        )
    ).scalar_one_or_none()

    establishment = db.execute(
        select(Establishment).where(
            Establishment.id_establecimiento == establishment_id
        )
    ).scalar_one_or_none()

    retinography = get_retinography_by_evaluation(
        db=db,
        evaluation_id=evaluation_id,
    )

    if (
        patient is None
        or doctor is None
        or establishment is None
        or retinography is None
    ):
        raise ReportDataIncompleteError()

    try:
        results = get_ai_evaluation_results(
            db=db,
            establishment_id=establishment_id,
            evaluation_id=evaluation_id,
        )
    except AIResultsNotAvailableError as exc:
        raise ReportEvaluationNotReadyError() from exc

    rd = results["retinopatia_diabetica"]
    glaucoma = results["glaucoma"]

    data = ReportPDFData(
        evaluation_id=evaluation.id_evaluacion,
        report_version=report_version,
        establishment_name=establishment.nombre,
        evaluation_date=evaluation.fecha_evaluacion,
        eye=evaluation.ojo_evaluado,
        patient_name=f"{patient.nombres} {patient.apellidos}",
        patient_document=patient.numero_documento,
        patient_birthdate=patient.fecha_nacimiento,
        patient_sex=patient.sexo,
        doctor_name=f"{doctor.nombres} {doctor.apellidos}",
        rd_result=rd["resultado"],
        rd_confidence=rd["confianza"],
        glaucoma_result=glaucoma["resultado"],
        glaucoma_confidence=glaucoma["confianza"],
        suggested_priority=evaluation.prioridad_sugerida,
        medical_observation=evaluation.observacion_medica,
    )

    image_bytes = download_retinography(
        retinography.ruta_original_s3
    )

    return data, image_bytes
