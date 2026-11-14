from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account
)
from app.models.account import Account
from app.schemas.ai_analysis import (
    AIAnalysisResponse
)
from app.services.ai_analysis_service import (
    AIAnalysisEvaluationNotFoundError,
    AIAnalysisExecutionError,
    AIAnalysisPreprocessingError,
    AIAnalysisRetinographyNotFoundError,
    AIModelConfigurationError,
    run_ai_analysis
)


router = APIRouter(
    prefix="/api/v1/evaluations",
    tags=["AI Analysis"]
)


@router.post(
    "/{evaluation_id}/analysis",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK
)
def analyze_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        return run_ai_analysis(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            evaluation_id=evaluation_id
        )

    except AIAnalysisEvaluationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "La evaluación retiniana "
                "no fue encontrada."
            )
        )

    except AIAnalysisRetinographyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La evaluación no tiene "
                "una retinografía registrada."
            )
        )

    except AIModelConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Los modelos de inteligencia "
                "artificial no están configurados "
                "correctamente."
            )
        )

    except AIAnalysisPreprocessingError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error)
        )

    except AIAnalysisExecutionError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error)
        )
