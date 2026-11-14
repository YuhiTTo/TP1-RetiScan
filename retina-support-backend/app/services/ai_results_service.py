
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.ai_model import AIModel
from app.models.ai_result import AIResult
from app.models.model_execution import ModelExecution

from app.repositories.evaluation_repository import (
    get_evaluation_by_id
)
from app.repositories.retinography_repository import (
    get_retinography_by_evaluation
)


class AIResultsEvaluationNotFoundError(Exception):
    pass


class AIResultsNotAvailableError(Exception):
    pass


def get_ai_evaluation_results(
    db: Session,
    establishment_id: int,
    evaluation_id: int
) -> dict:

    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise AIResultsEvaluationNotFoundError()

    retinography = get_retinography_by_evaluation(
        db=db,
        evaluation_id=evaluation_id
    )

    if (
        retinography is None
        or retinography.estado != "ANALIZADA"
    ):
        raise AIResultsNotAvailableError()

    statement = (
        select(AIAnalysis)
        .where(
            AIAnalysis.id_retinografia
            == retinography.id_retinografia
        )
        .order_by(AIAnalysis.id_analisis.desc())
        .limit(1)
    )

    analysis = db.execute(
        statement
    ).scalar_one_or_none()

    if (
        analysis is None
        or analysis.estado != "COMPLETADO"
    ):
        raise AIResultsNotAvailableError()

    statement = (
        select(ModelExecution, AIModel, AIResult)
        .join(
            AIModel,
            ModelExecution.id_modelo == AIModel.id_modelo
        )
        .outerjoin(
            AIResult,
            AIResult.id_ejecucion
            == ModelExecution.id_ejecucion
        )
        .where(
            ModelExecution.id_analisis
            == analysis.id_analisis
        )
    )

    rows = db.execute(statement).all()

    expected_objectives = {
        "RETINOPATIA_DIABETICA",
        "GLAUCOMA"
    }

    results = {}

    for execution, model, result in rows:

        if model.objetivo not in expected_objectives:
            continue

        if (
            execution.estado != "COMPLETADO"
            or result is None
            or model.objetivo in results
        ):
            raise AIResultsNotAvailableError()

        results[model.objetivo] = {
            "estado": execution.estado,
            "resultado": result.resultado,
            "confianza": result.nivel_confianza,
            "requiere_revision": result.requiere_revision
        }

    if set(results) != expected_objectives:
        raise AIResultsNotAvailableError()

    rd = results["RETINOPATIA_DIABETICA"]
    glaucoma = results["GLAUCOMA"]

    resumen = None

    if (
        rd["resultado"]
        == "Sin indicios de Retinopatía Diabética"
        and glaucoma["resultado"]
        == "Bajo riesgo de Glaucoma"
    ):
        resumen = (
            "Sin indicios de las patologías evaluadas"
        )

    review_flags = [
        rd["requiere_revision"],
        glaucoma["requiere_revision"]
    ]

    if True in review_flags:
        requiere_revision = True
    elif None in review_flags:
        requiere_revision = None
    else:
        requiere_revision = False

    return {
        "id_evaluacion": evaluation.id_evaluacion,
        "id_analisis": analysis.id_analisis,
        "estado": analysis.estado,

        "retinografia": {
            "id_retinografia": retinography.id_retinografia,
            "nombre_archivo": retinography.nombre_archivo,
            "formato": retinography.formato,
            "ancho_px": retinography.ancho_px,
            "alto_px": retinography.alto_px
        },

        "retinopatia_diabetica": rd,
        "glaucoma": glaucoma,

        "requiere_revision": requiere_revision,
        "prioridad_sugerida": evaluation.prioridad_sugerida,
        "resumen": resumen,

        "aviso_soporte_clinico": (
            "Los resultados automatizados y la "
            "prioridad sugerida son información "
            "de soporte clínico. No sustituyen "
            "la evaluación ni el criterio del "
            "médico oftalmólogo."
        )
    }
