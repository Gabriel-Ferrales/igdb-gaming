"""Tests for resilient source timestamp conversion."""

import json
from datetime import date

import pytest

from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.json_converter import convert_batch, safe_unix_timestamp


class FakeBlob:
    def __init__(self, name: str, values: dict[str, str]) -> None:
        self.name = name
        self.values = values

    def exists(self) -> bool:
        return self.name in self.values

    def download_as_text(self) -> str:
        return self.values[self.name]

    def upload_from_string(self, value: str, **_: object) -> None:
        self.values[self.name] = value


class FakeBucket:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(name, self.values)


class FakeStorageClient:
    def __init__(self, values: dict[str, str]) -> None:
        self.bucket_value = FakeBucket(values)

    def bucket(self, _: str) -> FakeBucket:
        return self.bucket_value


def test_safe_unix_timestamp_handles_valid_none_invalid_and_out_of_range(
    caplog: pytest.LogCaptureFixture,
) -> None:
    context = {
        "endpoint": "companies",
        "batch_id": "batch-1",
        "record_id": 99,
        "field_name": "created_at",
    }

    assert safe_unix_timestamp(0, **context) == "1970-01-01T00:00:00+00:00"
    assert safe_unix_timestamp(-1, **context) == "1969-12-31T23:59:59+00:00"
    assert safe_unix_timestamp(None, **context) is None
    assert safe_unix_timestamp("not-a-timestamp", **context) is None
    assert safe_unix_timestamp(-10**20, **context) is None
    assert "endpoint=companies batch_id=batch-1 record_id=99" in caplog.text
    assert "field=created_at value='not-a-timestamp'" in caplog.text


def test_invalid_timestamp_keeps_record_and_raw_value() -> None:
    source_name = "raw/companies/page-0001.json"
    values = {source_name: json.dumps([{"id": 7, "created_at": "invalid"}])}
    batch = BatchManifest(
        "companies",
        "batch-1",
        "historical",
        date(2026, 7, 15),
        "completed",
        1,
        1,
        7,
        7,
        (f"gs://bucket/{source_name}",),
        "gs://bucket/raw/companies/manifest.json",
        "raw/companies/manifest.json",
    )

    result = convert_batch(FakeStorageClient(values), "bucket", batch)

    converted_name = result.output_uris[0].removeprefix("gs://bucket/")
    converted = json.loads(values[converted_name])
    assert converted["id"] == 7
    assert converted["created_at"] == "invalid"
    assert converted["created_at_ts"] is None
