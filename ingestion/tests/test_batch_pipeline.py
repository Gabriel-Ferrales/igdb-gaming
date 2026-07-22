"""Tests for batch selection and resumability decisions."""

from datetime import date
from unittest.mock import Mock, patch

from igdb_pipeline.batch_models import BatchManifest, ConversionResult
from igdb_pipeline.batch_pipeline import BatchDecision, BatchPipeline


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


@patch("igdb_pipeline.batch_pipeline.discover_batches")
def test_failed_batch_is_identified_without_retry(discover: Mock) -> None:
    discover.return_value = [batch()]
    pipeline = BatchPipeline(
        Mock(), Mock(), project="p", bucket="bucket", dataset="raw"
    )
    pipeline.registry.statuses = Mock(return_value={("games", "b1"): "failed"})

    decision = pipeline.plan(endpoints={"games"})[0]

    assert decision.action == "ignore"
    assert decision.reason == "failed; pass --retry-failed"
    pipeline.registry.statuses.assert_called_once()


@patch("igdb_pipeline.batch_pipeline.discover_batches")
def test_unregistered_batch_is_identified_and_planning_does_not_write(
    discover: Mock,
) -> None:
    discover.return_value = [batch()]
    pipeline = BatchPipeline(
        Mock(), Mock(), project="p", bucket="bucket", dataset="raw"
    )
    pipeline.registry.statuses = Mock(return_value={})
    pipeline.registry.ensure_table = Mock()
    pipeline.registry.register_discovered = Mock()
    pipeline.registry.set_status = Mock()

    decision = pipeline.plan(endpoints={"games"})[0]

    assert decision.action == "convert-and-load"
    assert decision.reason == "registry status: not registered"
    pipeline.registry.statuses.assert_called_once()
    pipeline.registry.ensure_table.assert_not_called()
    pipeline.registry.register_discovered.assert_not_called()
    pipeline.registry.set_status.assert_not_called()


@patch("igdb_pipeline.batch_pipeline.discover_batches")
def test_run_processes_all_batches_and_counts_failures(discover: Mock) -> None:
    pipeline = BatchPipeline(Mock(), Mock(), project="p", bucket="bucket", dataset="raw")
    first, second = batch(), BatchManifest(
        "games", "b2", "historical", date(2026, 7, 15), "completed", 1, 1, 3, 3,
        (), "gs://bucket/raw/manifest.json", "raw/manifest.json"
    )
    pipeline.registry.ensure_table = Mock()
    pipeline.registry.statuses = Mock(return_value={("games", "b1"): "converted"})
    pipeline.registry.register_discovered = Mock()
    pipeline.registry.set_status = Mock()
    pipeline.loader.load_and_merge = Mock(side_effect=[RuntimeError("load failed"), 1])
    discover.return_value = [first]
    assert pipeline.plan(endpoints={"games"})[0].action == "load"
    pipeline.registry.statuses.assert_called_once()
    with patch(
        "igdb_pipeline.batch_pipeline.convert_batch",
        return_value=ConversionResult(1, 1, 1, ("gs://bucket/data.ndjson",), "gs://bucket/m.json"),
    ):
        summary = pipeline.run(
            [
                BatchDecision(first, "convert-and-load", "new"),
                BatchDecision(second, "convert-and-load", "new"),
                BatchDecision(first, "ignore", "already loaded"),
            ]
        )

    assert (summary.loaded, summary.skipped, summary.failed) == (1, 1, 1)
    pipeline.registry.ensure_table.assert_called_once()
    assert pipeline.registry.register_discovered.call_count == 2
