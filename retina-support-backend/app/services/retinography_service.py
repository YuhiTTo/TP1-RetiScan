from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.retinography import Retinography
from app.repositories.evaluation_repository import get_evaluation_by_id
from app.repositories.retinography_repository import (
    get_retinography_by_evaluation
)
from app.services.storage_service import upload_retinography


class RetinographyEvaluationNotFoundError(Exception):
    pass


class RetinographyEmptyFileError(Exception):
    pass


class RetinographyUnreadableError(Exception):
    pass


class RetinographyUnsupportedFormatError(Exception):
    pass

def upload_evaluation_retinography(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    filename: str,
    content_type: str | None,
    content: bytes
) -> Retinography:
    
    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise RetinographyEvaluationNotFoundError()

    if not content:
        raise RetinographyEmptyFileError()

    original_filename = Path(filename).name

    extension = (
        Path(original_filename)
        .suffix
        .lower()
        .lstrip(".")
    )

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png"
    }

    if extension not in allowed_extensions:
        raise RetinographyUnsupportedFormatError()

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()

        with Image.open(BytesIO(content)) as image:
            width, height = image.size

            detected_format = (
                image.format.lower()
                if image.format
                else ""
            )

    except Exception as error:
        raise RetinographyUnreadableError() from error

    allowed_formats = {
        "jpeg",
        "png"
    }

    if detected_format not in allowed_formats:
        raise RetinographyUnsupportedFormatError()
    
    s3_path = upload_retinography(
        content=content,
        evaluation_id=evaluation_id,
        content_type=content_type
    )
    
    retinography = get_retinography_by_evaluation(
        db=db,
        evaluation_id=evaluation_id
    )

    if retinography is None:

        retinography = Retinography(
            id_evaluacion=evaluation_id,
            nombre_archivo=original_filename,
            formato=extension,
            tamano_bytes=len(content),
            ancho_px=width,
            alto_px=height,
            ruta_original_s3=s3_path,
            estado_validacion="VALIDADA",
            calidad_imagen=None,
            estado="CARGADA"
        )

        db.add(retinography)

    else:
        
        retinography.nombre_archivo = original_filename
        retinography.formato = extension
        retinography.tamano_bytes = len(content)
        retinography.ancho_px = width
        retinography.alto_px = height
        retinography.ruta_original_s3 = s3_path

        retinography.estado_validacion = "VALIDADA"
        retinography.calidad_imagen = None
        retinography.estado = "CARGADA"

    try:
        db.commit()
        db.refresh(retinography)

        return retinography

    except IntegrityError:
        db.rollback()
        raise