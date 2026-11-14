from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import ( get_db, require_institutional_account )
from app.models.account import Account
from app.schemas.retinography import RetinographyResponse
from app.repositories.evaluation_repository import get_evaluation_by_id
from app.repositories.retinography_repository import get_retinography_by_evaluation

from app.services.retinography_service import (
    RetinographyEmptyFileError,
    RetinographyEvaluationNotFoundError,
    RetinographyReplacementNotAllowedError,
    RetinographyUnreadableError,
    RetinographyUnsupportedFormatError,
    upload_evaluation_retinography,
)

from app.services.storage_service import (
    StorageConfigurationError,
    StorageDownloadError,
    StorageUploadError,
    download_retinography,
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

    except RetinographyReplacementNotAllowedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede cargar o reemplazar la retinografía "
                "porque ya fue analizada o la evaluación "
                "se encuentra finalizada."
            )
        )

    except RetinographyEmptyFileError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La retinografía seleccionada está vacía."
        )

    except RetinographyUnsupportedFormatError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Formato de retinografía no admitido. "
                "Utilice JPG, JPEG o PNG."
            )
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


@router.get("/{evaluation_id}/retinography/image")
def get_retinography_image(
    evaluation_id: int,
    db: Session = Depends(get_db),
    institutional_account: Account = Depends(
        require_institutional_account
    )
):
    # Verificar que la evaluación pertenezca
    # al establecimiento autenticado.
    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=institutional_account.id_establecimiento,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="La evaluación retiniana no fue encontrada."
        )

    # Buscar la retinografía asociada.
    retinography = get_retinography_by_evaluation(
        db=db,
        evaluation_id=evaluation_id
    )

    if retinography is None:
        raise HTTPException(
            status_code=404,
            detail="La evaluación no tiene una retinografía registrada."
        )

    # Determinar el formato de imagen.
    image_format = retinography.formato.lower()

    if image_format not in {"jpg", "jpeg", "png"}:
        raise HTTPException(
            status_code=415,
            detail="Formato de imagen no admitido."
        )

    media_type = (
        "image/png"
        if image_format == "png"
        else "image/jpeg"
    )

    # Recuperar la imagen original desde S3.
    try:
        image_bytes = download_retinography(
            retinography.ruta_original_s3
        )

    except StorageDownloadError:
        raise HTTPException(
            status_code=502,
            detail="No se pudo recuperar la retinografía."
        )

    # Enviar los bytes de imagen al frontend.
    return Response(
        content=image_bytes,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff"
        }
    )
