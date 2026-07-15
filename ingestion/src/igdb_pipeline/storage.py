"""Local and Google Cloud Storage persistence helpers."""

import json
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

from google.cloud import storage
from google.oauth2 import service_account

from igdb_pipeline.config import settings


def save_json_locally(
    records: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    """Save records as formatted JSON on the local filesystem."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
    return output_path


def batch_prefix(
    endpoint: str,
    load_type: str,
    extraction_date: date,
    batch_id: str,
) -> str:
    """Return the immutable prefix assigned to one extraction batch."""
    return (
        f"raw/{endpoint}/load_type={load_type}/"
        f"extraction_date={extraction_date.isoformat()}/batch_id={batch_id}"
    )


def page_object_name(
    endpoint: str,
    load_type: str,
    extraction_date: date,
    batch_id: str,
    min_id: int,
    max_id: int,
) -> str:
    """Build a deterministic object name for an ID-bounded page."""
    return (
        f"{batch_prefix(endpoint, load_type, extraction_date, batch_id)}/"
        f"{endpoint}_id_{min_id}_{max_id}.json"
    )


def manifest_object_name(
    endpoint: str,
    load_type: str,
    extraction_date: date,
    batch_id: str,
) -> str:
    """Build the manifest name for one batch."""
    return (
        f"{batch_prefix(endpoint, load_type, extraction_date, batch_id)}/manifest.json"
    )


class GCSJsonUploader:
    """Upload JSON values to one configured GCS bucket."""

    def __init__(
        self,
        client: storage.Client | None = None,
        bucket_name: str | None = None,
    ) -> None:
        if client is None:
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_application_credentials
            )
            client = storage.Client(
                project=settings.gcp_project_id,
                credentials=credentials,
            )
        self._bucket = client.bucket(bucket_name or settings.gcs_bucket_name)
        self._bucket_name = bucket_name or settings.gcs_bucket_name

    def upload(
        self,
        value: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        object_name: str,
    ) -> str:
        """Serialize and create an object, refusing accidental replacement."""
        payload = json.dumps(value, ensure_ascii=False, indent=2)
        blob = self._bucket.blob(object_name)
        blob.upload_from_string(
            payload,
            content_type="application/json",
            if_generation_match=0,
        )
        return f"gs://{self._bucket_name}/{object_name}"


def upload_json_to_gcs(
    records: list[dict[str, Any]],
    endpoint: str,
    *,
    object_name: str | None = None,
    uploader: GCSJsonUploader | None = None,
) -> str:
    """Upload records, retaining the old two-argument helper interface."""
    if object_name is None:
        if not records:
            raise ValueError("records must not be empty when object_name is omitted")
        ids = [record["id"] for record in records]
        object_name = page_object_name(
            endpoint=endpoint,
            load_type="historical",
            extraction_date=date.today(),
            batch_id=uuid4().hex,
            min_id=min(ids),
            max_id=max(ids),
        )
    return (uploader or GCSJsonUploader()).upload(records, object_name)
