import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


class StorageConfigurationError(Exception):
    pass


class StorageUploadError(Exception):
    pass


def get_s3_client():
    client_config = {
        "service_name": "s3",
        "region_name": settings.aws_region
    }

    # Desarrollo local: usar credenciales del .env
    if (
        settings.aws_access_key_id
        and settings.aws_secret_access_key
    ):
        client_config["aws_access_key_id"] = (
            settings.aws_access_key_id
        )
        client_config["aws_secret_access_key"] = (
            settings.aws_secret_access_key
        )

    return boto3.client(**client_config)

def upload_retinography(
    content: bytes,
    evaluation_id: int,
    content_type: str | None = None
) -> str:

    if not settings.aws_s3_bucket:
        raise StorageConfigurationError(
            "El bucket de Amazon S3 no está configurado."
        )

    # Una sola imagen original por evaluación.
    # Si se vuelve a cargar, S3 reemplaza este mismo objeto.
    object_key = (
        f"retinografias/{evaluation_id}/original"
    )

    s3_client = get_s3_client()

    try:
        put_args = {
            "Bucket": settings.aws_s3_bucket,
            "Key": object_key,
            "Body": content
        }

        if content_type:
            put_args["ContentType"] = content_type

        s3_client.put_object(**put_args)

    except (BotoCoreError, ClientError) as error:
        raise StorageUploadError(
            "No se pudo almacenar la retinografía en Amazon S3."
        ) from error

    return (
        f"s3://{settings.aws_s3_bucket}/"
        f"{object_key}"
    )