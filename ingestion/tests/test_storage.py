"""Tests for deterministic GCS object naming."""

from datetime import date

from igdb_pipeline.storage import manifest_object_name, page_object_name


def test_page_object_name_is_scoped_to_batch_and_id_range() -> None:
    name = page_object_name(
        endpoint="games",
        load_type="historical",
        extraction_date=date(2026, 7, 15),
        batch_id="batch-123",
        min_id=101,
        max_id=200,
    )

    assert name == (
        "raw/games/load_type=historical/extraction_date=2026-07-15/"
        "batch_id=batch-123/games_id_101_200.json"
    )


def test_manifest_shares_batch_prefix() -> None:
    name = manifest_object_name("genres", "historical", date(2026, 7, 15), "batch-456")

    assert name.endswith("batch_id=batch-456/manifest.json")
