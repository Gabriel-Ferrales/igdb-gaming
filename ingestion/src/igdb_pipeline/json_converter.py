"""Validated, non-destructive JSON-array to NDJSON conversion."""

import json
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from google.cloud import storage

from igdb_pipeline.batch_models import BatchManifest, ConversionResult

TIMESTAMP_FIELDS = (
    "created_at",
    "updated_at",
    "first_release_date",
    "start_date",
    "date",
)


def _object_name(uri_or_name: str, bucket_name: str) -> str:
    prefix = f"gs://{bucket_name}/"
    return uri_or_name[len(prefix) :] if uri_or_name.startswith(prefix) else uri_or_name


def conversion_manifest_name(batch: BatchManifest) -> str:
    return f"{batch.load_ready_prefix}/conversion_manifest.json"


def validate_conversion_manifest(
    client: storage.Client, bucket_name: str, batch: BatchManifest
) -> ConversionResult:
    blob = client.bucket(bucket_name).blob(conversion_manifest_name(batch))
    if not blob.exists():
        raise ValueError("conversion_manifest.json does not exist")
    value = json.loads(blob.download_as_text())
    if (
        value.get("batch_id") != batch.batch_id
        or value.get("endpoint") != batch.endpoint
    ):
        raise ValueError("conversion manifest does not match the batch")
    if int(value.get("record_count", -1)) != batch.record_count:
        raise ValueError(
            "conversion manifest record count does not match source manifest"
        )
    uris = tuple(value.get("output_uris") or ())
    if not uris:
        raise ValueError("conversion manifest has no output files")
    seen: set[int] = set()
    bucket = client.bucket(bucket_name)
    for uri in uris:
        converted_blob = bucket.blob(_object_name(uri, bucket_name))
        if not converted_blob.exists():
            raise ValueError(f"converted file does not exist: {uri}")
        for line_number, line in enumerate(
            converted_blob.download_as_text().splitlines(), start=1
        ):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid NDJSON object at {uri}:{line_number}"
                ) from error
            if not isinstance(record, dict):
                raise ValueError(f"NDJSON line is not an object at {uri}:{line_number}")
            record_id = record.get("id")
            if record_id is None:
                raise ValueError(f"null id at {uri}:{line_number}")
            record_id = int(record_id)
            if record_id in seen:
                raise ValueError(f"duplicate id {record_id} in converted batch")
            seen.add(record_id)
    if len(seen) != batch.record_count:
        raise ValueError(
            f"converted files contain {len(seen)} records; expected {batch.record_count}"
        )
    actual_min, actual_max = (min(seen), max(seen)) if seen else (0, 0)
    if int(value["min_id"]) != actual_min or int(value["max_id"]) != actual_max:
        raise ValueError("conversion manifest ID bounds do not match converted files")
    return ConversionResult(
        int(value["record_count"]),
        actual_min,
        actual_max,
        uris,
        f"gs://{bucket_name}/{blob.name}",
    )


def convert_batch(
    client: storage.Client, bucket_name: str, batch: BatchManifest
) -> ConversionResult:
    bucket = client.bucket(bucket_name)
    source_names = [_object_name(uri, bucket_name) for uri in batch.uploaded_objects]
    if not source_names:
        prefix = batch.manifest_object.rsplit("/", 1)[0] + "/"
        source_names = [
            blob.name
            for blob in client.list_blobs(bucket, prefix=prefix)
            if blob.name.endswith(".json") and not blob.name.endswith("/manifest.json")
        ]
    if batch.page_count is not None and len(source_names) != batch.page_count:
        raise ValueError(
            f"expected {batch.page_count} source files, found {len(source_names)}"
        )
    if not source_names and batch.record_count:
        raise ValueError("no source data files found")

    seen: set[int] = set()
    output_uris: list[str] = []
    loaded_at = datetime.now(UTC)
    for source_name in sorted(source_names):
        source_blob = bucket.blob(source_name)
        if not source_blob.exists():
            raise ValueError(
                f"source file does not exist: gs://{bucket_name}/{source_name}"
            )
        records = json.loads(source_blob.download_as_text())
        if not isinstance(records, list) or any(
            not isinstance(row, dict) for row in records
        ):
            raise ValueError(
                f"source file is not a JSON array of objects: {source_name}"
            )
        lines: list[str] = []
        for record in records:
            record_id = record.get("id")
            if record_id is None:
                raise ValueError(f"null id in {source_name}")
            record_id = int(record_id)
            if record_id in seen:
                raise ValueError(f"duplicate id {record_id} in batch")
            seen.add(record_id)
            converted: dict[str, Any] = dict(record)
            for field in TIMESTAMP_FIELDS:
                if converted.get(field) is not None:
                    converted[f"{field}_ts"] = datetime.fromtimestamp(
                        int(converted[field]), UTC
                    ).isoformat()
            converted.update(
                {
                    "_batch_id": batch.batch_id,
                    "_source_file": f"gs://{bucket_name}/{source_name}",
                    "_load_type": batch.load_type,
                    "_extraction_date": batch.extraction_date.isoformat(),
                    "_loaded_at": loaded_at.isoformat(),
                }
            )
            line = json.dumps(converted, ensure_ascii=False, separators=(",", ":"))
            if "\n" in line:
                raise ValueError(
                    "converted record unexpectedly contains a literal newline"
                )
            lines.append(line)
        output_name = (
            f"{batch.load_ready_prefix}/{PurePosixPath(source_name).stem}.ndjson"
        )
        bucket.blob(output_name).upload_from_string(
            "\n".join(lines) + ("\n" if lines else ""),
            content_type="application/x-ndjson",
        )
        output_uris.append(f"gs://{bucket_name}/{output_name}")
    if len(seen) != batch.record_count:
        raise ValueError(
            f"expected {batch.record_count} records, converted {len(seen)}"
        )
    if not output_uris:
        output_name = f"{batch.load_ready_prefix}/{batch.endpoint}_empty.ndjson"
        bucket.blob(output_name).upload_from_string(
            "", content_type="application/x-ndjson"
        )
        output_uris.append(f"gs://{bucket_name}/{output_name}")
    min_id, max_id = (min(seen), max(seen)) if seen else (0, 0)
    value = {
        "endpoint": batch.endpoint,
        "batch_id": batch.batch_id,
        "load_type": batch.load_type,
        "extraction_date": batch.extraction_date.isoformat(),
        "record_count": len(seen),
        "file_count": len(output_uris),
        "min_id": min_id,
        "max_id": max_id,
        "output_uris": output_uris,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    name = conversion_manifest_name(batch)
    bucket.blob(name).upload_from_string(
        json.dumps(value, indent=2), content_type="application/json"
    )
    return ConversionResult(
        len(seen), min_id, max_id, tuple(output_uris), f"gs://{bucket_name}/{name}"
    )
