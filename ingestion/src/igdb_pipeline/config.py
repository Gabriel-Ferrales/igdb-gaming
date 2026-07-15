"""Environment-backed pipeline configuration."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application configuration."""

    twitch_client_id: str
    twitch_client_secret: str

    gcp_project_id: str
    gcp_region: str

    gcs_bucket_name: str

    google_application_credentials: str

    bq_raw_dataset: str
    bq_dev_dataset: str
    bq_prod_dataset: str

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()