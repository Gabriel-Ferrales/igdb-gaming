"""Cloud Storage and BigQuery persistence interfaces."""
"""Storage functions for local files and Google Cloud Storage."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.cloud import storage

from igdb_pipeline.config import settings
from google.oauth2 import service_account


def save_json_locally(
    records: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    """Save records as formatted JSON on the local filesystem."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def upload_json_to_gcs(
    records: list[dict[str, Any]],
    endpoint: str,
) -> str:
    """Serialize records and upload them directly to Google Cloud Storage."""
    extracted_at = datetime.now(UTC)
    timestamp = extracted_at.strftime("%Y%m%dT%H%M%SZ")
    extraction_date = extracted_at.strftime("%Y-%m-%d")

    object_name = (
        f"raw/{endpoint}/"
        f"extraction_date={extraction_date}/"
        f"{endpoint}_{timestamp}.json"
    )

    credentials = service_account.Credentials.from_service_account_file(
    settings.google_application_credentials
    )

    client = storage.Client(
        project=settings.gcp_project_id,
        credentials=credentials,
    )

    
    bucket = client.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(object_name)

    payload = json.dumps(
        records,
        ensure_ascii=False,
        indent=2,
    )

    blob.upload_from_string(
        payload,
        content_type="application/json",
    )

    return f"gs://{settings.gcs_bucket_name}/{object_name}"