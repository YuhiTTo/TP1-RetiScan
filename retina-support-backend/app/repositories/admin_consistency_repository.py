from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.ai_model import AIModel
from app.models.ai_result import AIResult
from app.models.doctor import Doctor
from app.models.establishment import Establishment
from app.models.evaluation import RetinalEvaluation
from app.models.model_execution import ModelExecution
from app.models.patient import Patient
from app.models.retinography import Retinography


def load_admin_consistency_evaluations(
    db: Session,
) -> list[dict]:
    """
    Consulta datos de integridad de las evaluaciones.

    No recupera nombres ni documentos de pacientes.
    No modifica registros.
    """

    statement = (
        select(
            RetinalEvaluation.id_evaluacion,
            RetinalEvaluation.id_establecimiento,
            RetinalEvaluation.estado.label(
                "estado_evaluacion"
            ),
            RetinalEvaluation.fecha_finalizacion,

            Establishment.nombre.label(
                "establecimiento"
            ),

            Patient.id_paciente.label(
                "paciente_id_encontrado"
            ),
            Patient.id_establecimiento.label(
                "paciente_establecimiento_id"
            ),

            Doctor.id_medico.label(
                "medico_id_encontrado"
            ),
            Doctor.id_establecimiento.label(
                "medico_establecimiento_id"
            ),

            Retinography.id_retinografia,
            Retinography.estado.label(
                "estado_retinografia"
            ),
        )
        .select_from(RetinalEvaluation)
        .outerjoin(
            Establishment,
            Establishment.id_establecimiento
            == RetinalEvaluation.id_establecimiento,
        )
        .outerjoin(
            Patient,
            Patient.id_paciente
            == RetinalEvaluation.id_paciente,
        )
        .outerjoin(
            Doctor,
            Doctor.id_medico
            == RetinalEvaluation.id_medico,
        )
        .outerjoin(
            Retinography,
            Retinography.id_evaluacion
            == RetinalEvaluation.id_evaluacion,
        )
        .order_by(
            RetinalEvaluation.id_evaluacion.desc()
        )
    )

    return [
        dict(row)
        for row in db.execute(statement).mappings().all()
    ]


def load_latest_admin_consistency_ai(
    db: Session,
    retinography_ids: list[int],
) -> list[dict]:
    """
    Consulta exclusivamente el ultimo analisis
    registrado de cada retinografia indicada.

    No recupera predicciones ni datos clinicos.
    No modifica registros.
    """

    if not retinography_ids:
        return []

    latest_analysis = (
        select(
            AIAnalysis.id_retinografia,
            func.max(
                AIAnalysis.id_analisis
            ).label("id_analisis"),
        )
        .where(
            AIAnalysis.id_retinografia.in_(
                retinography_ids
            )
        )
        .group_by(
            AIAnalysis.id_retinografia
        )
        .subquery()
    )

    statement = (
        select(
            AIAnalysis.id_retinografia,
            AIAnalysis.id_analisis,
            AIAnalysis.estado.label(
                "estado_analisis"
            ),

            ModelExecution.id_ejecucion,
            ModelExecution.estado.label(
                "estado_ejecucion"
            ),

            AIModel.objetivo.label(
                "objetivo_modelo"
            ),

            AIResult.id_resultado,
        )
        .select_from(AIAnalysis)
        .join(
            latest_analysis,
            AIAnalysis.id_analisis
            == latest_analysis.c.id_analisis,
        )
        .outerjoin(
            ModelExecution,
            ModelExecution.id_analisis
            == AIAnalysis.id_analisis,
        )
        .outerjoin(
            AIModel,
            AIModel.id_modelo
            == ModelExecution.id_modelo,
        )
        .outerjoin(
            AIResult,
            AIResult.id_ejecucion
            == ModelExecution.id_ejecucion,
        )
        .order_by(
            AIAnalysis.id_retinografia,
            ModelExecution.id_ejecucion,
        )
    )

    return [
        dict(row)
        for row in db.execute(statement).mappings().all()
    ]
