from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account,
)
from app.models.account import Account
from app.models.report import Report
from app.models.patient import Patient
from app.models.evaluation import RetinalEvaluation
from app.repositories.evaluation_repository import (
    get_evaluation_by_id,
)
from app.services.report_service import (
    generate_initial_report,
    ReportAlreadyExistsError,
    ReportCleanupFailedError,
    ReportCommitUncertainError,
)
from app.services.report_data_service import (
    ReportEvaluationNotFoundError,
    ReportEvaluationNotReadyError,
    ReportDataIncompleteError,
)
from app.services.report_storage_service import download_report_pdf
from app.services.storage_service import (
    StorageConfigurationError,
    StorageDownloadError,
    StorageUploadError,
)


router = APIRouter(
    prefix="/api/v1/evaluations",
    tags=["Reports"],
)

patient_reports_router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Reports"],
)


def _find_report(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
) -> Report:
    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id,
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada.",
        )

    report = db.execute(
        select(Report).where(
            Report.id_evaluacion == evaluation_id
        )
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Esta evaluación todavía no tiene un PDF generado.",
        )

    return report


@router.post("/{evaluation_id}/report", status_code=201)
def create_report(
    evaluation_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_institutional_account),
):
    try:
        report = generate_initial_report(
            db=db,
            establishment_id=account.id_establecimiento,
            evaluation_id=evaluation_id,
        )

    except ReportEvaluationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Evaluación no encontrada.",
        )

    except (
        ReportEvaluationNotReadyError,
        ReportDataIncompleteError,
    ):
        raise HTTPException(
            status_code=409,
            detail="La evaluación no está lista para generar el PDF.",
        )

    except ReportAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="La evaluación ya tiene un reporte PDF.",
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el reporte.",
        )

    except ReportCommitUncertainError:
        raise HTTPException(
            status_code=503,
            detail=(
                "No se pudo confirmar el registro del reporte. "
                "Consulte su estado antes de reintentar."
            ),
        )

    except ReportCleanupFailedError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Falló el registro y no se pudo completar "
                "la limpieza del archivo en S3."
            ),
        )

    except StorageConfigurationError:
        raise HTTPException(
            status_code=503,
            detail="Amazon S3 no está configurado.",
        )

    except (StorageUploadError, StorageDownloadError):
        raise HTTPException(
            status_code=502,
            detail="No se pudo procesar el archivo en Amazon S3.",
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo acceder a PostgreSQL.",
        )

    return {
        "id_reporte": report.id_reporte,
        "id_evaluacion": report.id_evaluacion,
        "fecha_generacion": report.fecha_generacion,
        "mensaje": "Reporte PDF generado correctamente.",
    }


def _get_report_response(
    evaluation_id: int,
    db: Session,
    establishment_id: int,
    download: bool,
) -> Response:
    report = _find_report(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id,
    )

    try:
        pdf_bytes = download_report_pdf(report.ruta_pdf_s3)

    except StorageDownloadError:
        raise HTTPException(
            status_code=502,
            detail="No se pudo recuperar el reporte PDF.",
        )

    disposition = "attachment" if download else "inline"

    filename = f"RetiScan_reporte_{evaluation_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'{disposition}; filename="{filename}"'
            ),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{evaluation_id}/report")
def view_report(
    evaluation_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_institutional_account),
):
    return _get_report_response(
        evaluation_id=evaluation_id,
        db=db,
        establishment_id=account.id_establecimiento,
        download=False,
    )


@router.get("/{evaluation_id}/report/download")
def download_report(
    evaluation_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_institutional_account),
):
    return _get_report_response(
        evaluation_id=evaluation_id,
        db=db,
        establishment_id=account.id_establecimiento,
        download=True,
    )



@patient_reports_router.get("/{patient_id}/reports")
def list_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_institutional_account),
):
    """Lista evaluaciones finalizadas y sus reportes vigentes."""

    establishment_id = account.id_establecimiento

    patient = db.execute(
        select(Patient).where(
            Patient.id_paciente == patient_id,
            Patient.id_establecimiento == establishment_id,
        )
    ).scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    statement = (
        select(RetinalEvaluation, Report)
        .outerjoin(
            Report,
            Report.id_evaluacion
            == RetinalEvaluation.id_evaluacion,
        )
        .where(
            RetinalEvaluation.id_paciente == patient_id,
            RetinalEvaluation.id_establecimiento
            == establishment_id,
            RetinalEvaluation.estado == "FINALIZADA",
        )
        .order_by(
            RetinalEvaluation.fecha_evaluacion.desc(),
            RetinalEvaluation.id_evaluacion.desc(),
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "id_evaluacion": evaluation.id_evaluacion,
            "fecha_evaluacion": evaluation.fecha_evaluacion,
            "ojo_evaluado": evaluation.ojo_evaluado,
            "tiene_reporte": report is not None,
            "fecha_generacion": (
                report.fecha_generacion
                if report is not None
                else None
            ),
        }
        for evaluation, report in rows
    ]
