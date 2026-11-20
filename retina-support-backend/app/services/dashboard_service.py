from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import (
    count_patients_by_establishment,
    count_evaluations_by_status,
    count_reports_by_establishment,
    get_recent_evaluations,
)

from app.schemas.dashboard import (
    DashboardRecentEvaluationResponse,
    DashboardSummaryResponse,
)


def get_dashboard_summary(
    db: Session,
    establishment_id: int
) -> DashboardSummaryResponse:

    # 1. Obtener total de pacientes
    total_patients = count_patients_by_establishment(
        db=db,
        establishment_id=establishment_id
    )

    # 2. Obtener evaluaciones por estado
    evaluation_counts = count_evaluations_by_status(
        db=db,
        establishment_id=establishment_id
    )

    # 3. Obtener total de reportes
    total_reports = count_reports_by_establishment(
        db=db,
        establishment_id=establishment_id
    )

    # 4. Obtener las últimas siete evaluaciones
    recent_rows = get_recent_evaluations(
        db=db,
        establishment_id=establishment_id
    )

    # 5. Preparar información de las evaluaciones recientes
    recent_evaluations = [
        DashboardRecentEvaluationResponse(
            id_evaluacion=evaluation.id_evaluacion,
            nombres_paciente=patient.nombres,
            apellidos_paciente=patient.apellidos,
            fecha_evaluacion=evaluation.fecha_evaluacion,
            ojo_evaluado=evaluation.ojo_evaluado,
            estado=evaluation.estado
        )
        for evaluation, patient in recent_rows
    ]

    # 6. Construir respuesta del Dashboard
    return DashboardSummaryResponse(
        total_pacientes=total_patients,
        evaluaciones_realizadas=(
            evaluation_counts["evaluaciones_realizadas"]
        ),
        evaluaciones_pendientes=(
            evaluation_counts["evaluaciones_pendientes"]
        ),
        reportes_generados=total_reports,
        evaluaciones_recientes=recent_evaluations
    )