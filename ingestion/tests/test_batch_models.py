"""Tests for extraction manifest validation."""

from igdb_pipeline.batch_models import BatchManifest


def test_manifest_derives_partition_values_from_path() -> None:
    batch = BatchManifest.from_dict(
        {
            "endpoint": "games",
            "batch_id": "abc",
            "load_type": "historical",
            "status": "completed",
            "record_count": 2,
            "page_count": 1,
            "uploaded_objects": ["gs://bucket/raw/file.json"],
        },
        object_name="raw/games/load_type=historical/extraction_date=2026-07-15/batch_id=abc/manifest.json",
        bucket="bucket",
    )
    assert batch.extraction_date.isoformat() == "2026-07-15"
    assert batch.load_ready_prefix.startswith("load_ready/games/")


def test_manifest_rejects_path_mismatch() -> None:
    try:
        BatchManifest.from_dict(
            {
                "endpoint": "games",
                "batch_id": "wrong",
                "load_type": "historical",
                "status": "completed",
                "record_count": 0,
            },
            object_name="raw/games/load_type=historical/extraction_date=2026-07-15/batch_id=abc/manifest.json",
            bucket="bucket",
        )
    except ValueError as error:
        assert "GCS path" in str(error)
    else:
        raise AssertionError("expected ValueError")
