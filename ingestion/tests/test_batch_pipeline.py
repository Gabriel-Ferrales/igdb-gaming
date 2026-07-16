"""Tests for batch selection and resumability decisions."""

from datetime import date
from unittest.mock import Mock, patch

from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.batch_pipeline import BatchPipeline


def batch(status: str = "completed") -> BatchManifest:
    return BatchManifest(
        "games",
        "b1",
        "historical",
        date(2026, 7, 15),
        status,
        1,
        2,
        1,
        2,
        (),
        "gs://bucket/raw/manifest.json",
        "raw/manifest.json",
    )


@patch("igdb_pipeline.batch_pipeline.discover_batches")
def test_loaded_batch_is_ignored(discover: Mock) -> None:
    discover.return_value = [batch()]
    pipeline = BatchPipeline(
        Mock(), Mock(), project="p", bucket="bucket", dataset="raw"
    )
    pipeline.registry.statuses = Mock(return_value={("games", "b1"): "loaded"})
    decision = pipeline.plan(endpoints={"games"})[0]
    assert decision.action == "ignore"
    assert decision.reason == "already loaded"


@patch("igdb_pipeline.batch_pipeline.discover_batches")
def test_converted_batch_resumes_at_load(discover: Mock) -> None:
    discover.return_value = [batch()]
    pipeline = BatchPipeline(
        Mock(), Mock(), project="p", bucket="bucket", dataset="raw"
    )
    pipeline.registry.statuses = Mock(return_value={("games", "b1"): "converted"})
    assert pipeline.plan(endpoints={"games"})[0].action == "load"
