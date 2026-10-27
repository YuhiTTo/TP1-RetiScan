from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


SERVICE_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    aws_s3_bucket: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=SERVICE_ROOT / ".env",
        env_file_encoding="utf-8"
    )


settings = Settings()