import re
from uuid import uuid4
from urllib.parse import urlparse

from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.services.storage_service import (
    get_s3_client,
    StorageConfigurationError,
    StorageUploadError,
    StorageDownloadError,
)


def upload_report_pdf(
    content: bytes,
    evaluation_id: int
) -> str:
    """Almacena el PDF vigente de una evaluación en S3."""

    if not settings.aws_s3_bucket:
        raise StorageConfigurationError(
            "El bucket de Amazon S3 no está configurado."
        )

    if not isinstance(evaluation_id, int) or evaluation_id <= 0:
        raise ValueError("El identificador de evaluación no es válido.")

    if not content or not content.startswith(b"%PDF-"):
        raise ValueError("El contenido no es un documento PDF válido.")

    object_key = f"reportes/{evaluation_id}/reporte-{uuid4().hex}.pdf"

    try:
        get_s3_client().put_object(
            Bucket=settings.aws_s3_bucket,
            Key=object_key,
            Body=content,
            ContentType="application/pdf"
        )

    except (BotoCoreError, ClientError) as error:
        raise StorageUploadError(
            "No se pudo almacenar el reporte PDF en Amazon S3."
        ) from error

    return f"s3://{settings.aws_s3_bucket}/{object_key}"


def download_report_pdf(s3_path: str) -> bytes:
    """Recupera un reporte PDF desde Amazon S3."""

    parsed = urlparse(s3_path)

    object_key = parsed.path.lstrip("/")

    if (
        parsed.scheme != "s3"
        or not settings.aws_s3_bucket
        or parsed.netloc != settings.aws_s3_bucket
        or parsed.params
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(
            r"reportes/[1-9][0-9]*/reporte-[0-9a-f]{32}\.pdf",
            object_key
        )
    ):
        raise StorageDownloadError(
            "La ubicación del reporte PDF no es válida."
        )

    try:
        response = get_s3_client().get_object(
            Bucket=settings.aws_s3_bucket,
            Key=object_key
        )

        return response["Body"].read()

    except (BotoCoreError, ClientError) as error:
        raise StorageDownloadError(
            "No se pudo recuperar el reporte PDF de Amazon S3."
        ) from error


class StorageDeleteError(Exception):
    pass


def delete_report_pdf(s3_path: str) -> None:
    """Elimina un PDF de RetiScan almacenado en S3."""

    parsed = urlparse(s3_path)
    object_key = parsed.path.lstrip("/")

    if (
        parsed.scheme != "s3"
        or not settings.aws_s3_bucket
        or parsed.netloc != settings.aws_s3_bucket
        or parsed.params
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(
            r"reportes/[1-9][0-9]*/reporte-[0-9a-f]{32}\.pdf",
            object_key
        )
    ):
        raise StorageDeleteError(
            "La ubicación del reporte PDF no es válida."
        )

    try:
        get_s3_client().delete_object(
            Bucket=settings.aws_s3_bucket,
            Key=object_key
        )

    except (BotoCoreError, ClientError) as error:
        raise StorageDeleteError(
            "No se pudo eliminar el reporte PDF de Amazon S3."
        ) from error
