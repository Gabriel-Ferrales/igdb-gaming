"""Tests for loader command exit status."""

from unittest.mock import Mock, patch
from datetime import date

import pytest

from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.batch_pipeline import BatchDecision, BatchRunSummary
from igdb_pipeline.load_cli import main


def decision(action: str, reason: str) -> BatchDecision:
    return BatchDecision(
        BatchManifest(
            "games",
            "b1",
            "historical",
            date(2026, 7, 15),
            "completed",
            1,
            1,
            1,
            1,
            (),
            "gs://bucket/raw/manifest.json",
            "raw/manifest.json",
        ),
        action,
        reason,
    )


@patch("igdb_pipeline.load_cli._clients", return_value=(Mock(), Mock()))
@patch("igdb_pipeline.load_cli.BatchPipeline")
def test_run_returns_one_when_any_batch_fails(pipeline_cls: Mock, _: Mock) -> None:
    pipeline = pipeline_cls.return_value
    pipeline.plan.return_value = []
    pipeline.run.return_value = BatchRunSummary(loaded=1, skipped=0, failed=1)

    assert main(["run", "--endpoint", "games"]) == 1


@patch("igdb_pipeline.load_cli._clients", return_value=(Mock(), Mock()))
@patch("igdb_pipeline.load_cli.BatchPipeline")
def test_run_returns_zero_when_batches_load_or_skip(pipeline_cls: Mock, _: Mock) -> None:
    pipeline = pipeline_cls.return_value
    pipeline.plan.return_value = []
    pipeline.run.return_value = BatchRunSummary(loaded=1, skipped=2, failed=0)

    assert main(["run", "--endpoint", "games"]) == 0


@patch("igdb_pipeline.load_cli._clients", return_value=(Mock(), Mock()))
@patch("igdb_pipeline.load_cli.BatchPipeline")
def test_discover_reads_registry_without_running_writes(
    pipeline_cls: Mock, _: Mock, capsys: pytest.CaptureFixture[str]
) -> None:
    pipeline = pipeline_cls.return_value
    pipeline.plan.return_value = [decision("ignore", "already loaded")]

    assert main(["discover"]) == 0

    assert pipeline.plan.call_args.kwargs["read_registry"] is True
    pipeline.run.assert_not_called()
    assert "already loaded" in capsys.readouterr().out
