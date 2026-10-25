from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_institutional_account
)
from app.models.account import Account
from app.schemas.retinography import RetinographyResponse
from app.services.retinography_service import (
    RetinographyEmptyFileError,
    RetinographyEvaluationNotFoundError,
    RetinographyUnreadableError,
    upload_evaluation_retinography
)
from app.services.storage_service import (
    StorageConfigurationError,
    StorageUploadError
)


router = APIRouter(
    prefix="/api/v1/evaluations",
    tags=["Retinographies"]
)


@router.put(
    "/{evaluation_id}/retinography",
    response_model=RetinographyResponse,
    status_code=status.HTTP_200_OK
)
async def upload_retinography(
    evaluation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):

    try:
        content = await file.read()

        retinography = upload_evaluation_retinography(
            db=db,
            establishment_id=(
                institutional_account.id_establecimiento
            ),
            evaluation_id=evaluation_id,
            filename=file.filename or "retinografia",
            content_type=file.content_type,
            content=content
        )

    except RetinographyEvaluationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La evaluación retiniana no fue encontrada."
        )

    except RetinographyEmptyFileError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La retinografía seleccionada está vacía."
        )

    except RetinographyUnreadableError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La retinografía no pudo ser leída correctamente."
        )

    except StorageConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El almacenamiento de retinografías no está configurado."
        )

    except StorageUploadError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo almacenar la retinografía."
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar la retinografía."
        )

    finally:
        await file.close()

    return retinography