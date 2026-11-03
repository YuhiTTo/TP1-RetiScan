from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.ai_model import AIModel
from app.models.ai_result import AIResult
from app.models.model_execution import ModelExecution
from app.repositories.evaluation_repository import get_evaluation_by_id
from app.repositories.retinography_repository import (
    get_retinography_by_evaluation
)
from app.services.ai_client_service import (
    AIServiceAnalysisError,
    AIServiceConnectionError,
    request_ai_analysis
)


class AIAnalysisEvaluationNotFoundError(Exception):
    pass


class AIAnalysisRetinographyNotFoundError(Exception):
    pass


class AIModelConfigurationError(Exception):
    pass


class AIAnalysisExecutionError(Exception):
    pass


def _get_active_models(
    db: Session
) -> dict[str, AIModel]:

    statement = select(AIModel).where(
        AIModel.estado == "ACTIVO"
    )

    models = list(
        db.execute(statement).scalars().all()
    )

    models_by_objective: dict[str, AIModel] = {}

    for model in models:

        if model.objetivo in models_by_objective:
            raise AIModelConfigurationError(
                "Existe más de un modelo activo "
                f"para {model.objetivo}."
            )

        models_by_objective[
            model.objetivo
        ] = model

    required_objectives = {
        "RETINOPATIA_DIABETICA",
        "GLAUCOMA"
    }

    if not required_objectives.issubset(
        models_by_objective
    ):
        raise AIModelConfigurationError(
            "No están configurados todos "
            "los modelos IA requeridos."
        )

    return models_by_objective


def run_ai_analysis(
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
        raise AIAnalysisEvaluationNotFoundError()

    retinography = get_retinography_by_evaluation(
        db=db,
        evaluation_id=evaluation_id
    )

    if retinography is None:
        raise AIAnalysisRetinographyNotFoundError()

    models = _get_active_models(
        db=db
    )

    analysis = AIAnalysis(
        id_retinografia=(
            retinography.id_retinografia
        ),
        estado="PENDIENTE"
    )

    db.add(analysis)
    db.flush()

    rd_execution = ModelExecution(
        id_analisis=analysis.id_analisis,
        id_modelo=models[
            "RETINOPATIA_DIABETICA"
        ].id_modelo,
        estado="PENDIENTE"
    )

    glaucoma_execution = ModelExecution(
        id_analisis=analysis.id_analisis,
        id_modelo=models[
            "GLAUCOMA"
        ].id_modelo,
        estado="PENDIENTE"
    )

    db.add_all([
        rd_execution,
        glaucoma_execution
    ])

    db.commit()

    try:
        response = request_ai_analysis(
            evaluation_id=evaluation_id,
            s3_path=retinography.ruta_original_s3
        )

    except (
        AIServiceConnectionError,
        AIServiceAnalysisError
    ) as error:

        now = datetime.now()
        error_detail = str(error)[:1000]

        analysis.estado = "ERROR"
        analysis.fecha_fin = now

        rd_execution.estado = "ERROR"
        rd_execution.fecha_fin = now
        rd_execution.detalle_error = error_detail

        glaucoma_execution.estado = "ERROR"
        glaucoma_execution.fecha_fin = now
        glaucoma_execution.detalle_error = (
            error_detail
        )

        db.commit()

        raise AIAnalysisExecutionError(
            error_detail
        ) from error

    try:
        rd_data = response[
            "retinopatia_diabetica"
        ]

        glaucoma_data = response[
            "glaucoma"
        ]

        rd_result = AIResult(
            id_ejecucion=(
                rd_execution.id_ejecucion
            ),
            resultado=rd_data["resultado"],
            nivel_confianza=rd_data[
                "confianza"
            ]
        )

        glaucoma_result = AIResult(
            id_ejecucion=(
                glaucoma_execution.id_ejecucion
            ),
            resultado=glaucoma_data[
                "resultado"
            ],
            nivel_confianza=glaucoma_data[
                "confianza"
            ]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ) as error:

        now = datetime.now()

        analysis.estado = "ERROR"
        analysis.fecha_fin = now

        rd_execution.estado = "ERROR"
        rd_execution.fecha_fin = now
        rd_execution.detalle_error = (
            "Respuesta inválida del Servicio IA."
        )

        glaucoma_execution.estado = "ERROR"
        glaucoma_execution.fecha_fin = now
        glaucoma_execution.detalle_error = (
            "Respuesta inválida del Servicio IA."
        )

        db.commit()

        raise AIAnalysisExecutionError(
            "El Servicio IA devolvió "
            "una respuesta inválida."
        ) from error

    now = datetime.now()

    rd_execution.estado = "COMPLETADO"
    rd_execution.fecha_fin = now

    glaucoma_execution.estado = "COMPLETADO"
    glaucoma_execution.fecha_fin = now

    analysis.estado = "COMPLETADO"
    analysis.fecha_fin = now

    db.add_all([
        rd_result,
        glaucoma_result
    ])

    db.commit()

    db.refresh(analysis)
    db.refresh(rd_result)
    db.refresh(glaucoma_result)

    return {
        "id_analisis": (
            analysis.id_analisis
        ),
        "id_evaluacion": evaluation_id,
        "estado": analysis.estado,
        "retinopatia_diabetica": {
            "resultado": rd_result.resultado,
            "confianza": rd_result.nivel_confianza,
            "requiere_revision": rd_data.get(
                "requiere_revision",
                False
            )
        },
        "glaucoma": {
            "resultado": glaucoma_result.resultado,
            "confianza": glaucoma_result.nivel_confianza,
            "requiere_revision": glaucoma_data.get(
                "requiere_revision",
                False
            )
        },
        "requiere_revision": response.get(
            "requiere_revision",
            False
        )
    }
