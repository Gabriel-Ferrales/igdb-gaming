"""Discover and validate completed extraction manifests in GCS."""

import json
import logging
from collections.abc import Iterable

from google.cloud import storage

from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.endpoints import ENDPOINTS

LOGGER = logging.getLogger(__name__)


def discover_batches(client: storage.Client, bucket_name: str) -> list[BatchManifest]:
    bucket = client.bucket(bucket_name)
    batches: list[BatchManifest] = []
    for blob in client.list_blobs(bucket, prefix="raw/"):
        if not blob.name.endswith("/manifest.json"):
            continue
        try:
            manifest = BatchManifest.from_dict(
                json.loads(blob.download_as_text()),
                object_name=blob.name,
                bucket=bucket_name,
            )
            if manifest.endpoint not in ENDPOINTS:
                raise ValueError(f"unsupported endpoint {manifest.endpoint!r}")
            batches.append(manifest)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            LOGGER.warning(
                "Ignoring invalid manifest gs://%s/%s: %s",
                bucket_name,
                blob.name,
                error,
            )
    return sorted(
        batches, key=lambda item: (item.extraction_date, item.endpoint, item.batch_id)
    )


def completed_batches(batches: Iterable[BatchManifest]) -> list[BatchManifest]:
    return [batch for batch in batches if batch.status == "completed"]
