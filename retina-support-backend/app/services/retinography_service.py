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


def upload_evaluation_retinography(
    db: Session,
    establishment_id: int,
    evaluation_id: int,
    filename: str,
    content_type: str | None,
    content: bytes
) -> Retinography:

    # Comprobar que la evaluación existe y pertenece
    # al establecimiento autenticado.
    evaluation = get_evaluation_by_id(
        db=db,
        establishment_id=establishment_id,
        evaluation_id=evaluation_id
    )

    if evaluation is None:
        raise RetinographyEvaluationNotFoundError()

    if not content:
        raise RetinographyEmptyFileError()

    # Obtener dimensiones básicas de la imagen.
    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size

    except Exception as error:
        raise RetinographyUnreadableError() from error

    original_filename = Path(filename).name

    extension = Path(original_filename).suffix.lower().lstrip(".")

    # Subir o reemplazar el objeto en S3.
    s3_path = upload_retinography(
        content=content,
        evaluation_id=evaluation_id,
        content_type=content_type
    )

    # Una evaluación solamente puede tener una retinografía.
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
            estado_validacion="PENDIENTE",
            calidad_imagen=None,
            estado="CARGADA"
        )

        db.add(retinography)

    else:

        # US-10: reemplazo de la imagen existente.
        retinography.nombre_archivo = original_filename
        retinography.formato = extension
        retinography.tamano_bytes = len(content)
        retinography.ancho_px = width
        retinography.alto_px = height
        retinography.ruta_original_s3 = s3_path

        # Al reemplazar la imagen se reinicia su validación.
        retinography.estado_validacion = "PENDIENTE"
        retinography.calidad_imagen = None
        retinography.estado = "CARGADA"

    try:
        db.commit()
        db.refresh(retinography)

        return retinography

    except IntegrityError:
        db.rollback()
        raise