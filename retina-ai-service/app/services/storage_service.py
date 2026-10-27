import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


class StorageDownloadError(Exception):
    pass


def get_s3_client():
    client_config = {
        "service_name": "s3",
        "region_name": settings.aws_region
    }

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


def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    if not s3_uri.startswith("s3://"):
        raise ValueError(
            "La ruta proporcionada no es una URI válida de S3."
        )

    path = s3_uri[5:]
    parts = path.split("/", 1)

    if len(parts) != 2:
        raise ValueError(
            "La URI S3 no contiene un objeto válido."
        )

    bucket, key = parts

    return bucket, key


def download_retinography(s3_uri: str) -> bytes:
    bucket, key = parse_s3_uri(s3_uri)

    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )

        return response["Body"].read()

    except (BotoCoreError, ClientError) as error:
        raise StorageDownloadError(
            "No se pudo descargar la retinografía desde Amazon S3."
        ) from error