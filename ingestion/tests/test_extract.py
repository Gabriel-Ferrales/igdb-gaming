"""Tests for generic extraction and manifest orchestration."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from igdb_pipeline import extract


class FakeUploader:
    def __init__(self) -> None:
        self.uploads: list[tuple[object, str]] = []

    def upload(
        self,
        value: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        object_name: str,
    ) -> str:
        self.uploads.append((value, object_name))
        return f"gs://test-bucket/{object_name}"


def fixed_times() -> Any:
    times = iter(
        [
            datetime(2026, 7, 15, 1, 2, 3, tzinfo=UTC),
            datetime(2026, 7, 15, 1, 2, 4, tzinfo=UTC),
        ]
    )
    return lambda: next(times)


def test_extract_pages_builds_queries_with_progressing_cursor() -> None:
    queries: list[str] = []
    responses = iter([[{"id": 6}, {"id": 8}], []])

    def query_fn(**kwargs: Any) -> list[dict[str, int]]:
        queries.append(kwargs["query"])
        return next(responses)

    pages = list(
        extract.extract_pages(
            endpoint="genres",
            fields=["id", "name"],
            page_size=2,
            start_after_id=5,
            client_id="client",
            access_token="token",
            query_fn=query_fn,
        )
    )

    assert pages == [[{"id": 6}, {"id": 8}]]
    assert "where id > 5;" in queries[0]
    assert "where id > 8;" in queries[1]


def test_completed_manifest_summarizes_uploaded_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uploader = FakeUploader()
    responses = iter([[{"id": 1}, {"id": 2}], [{"id": 7}]])
    monkeypatch.setattr(
        extract,
        "get_app_access_token",
        lambda **kwargs: SimpleNamespace(access_token="token"),
    )

    manifest = extract.run_extraction(
        endpoint="genres",
        page_size=2,
        batch_id="known-batch",
        uploader=uploader,
        query_fn=lambda **kwargs: next(responses),
        now_fn=fixed_times(),
    )

    assert manifest["status"] == "completed"
    assert manifest["page_count"] == 2
    assert manifest["record_count"] == 3
    assert manifest["min_id"] == 1
    assert manifest["max_id"] == 7
    assert len(manifest["uploaded_objects"]) == 2
    assert manifest["failure"] is None
    assert len(uploader.uploads) == 3
    assert uploader.uploads[-1][0] == manifest
    assert uploader.uploads[-1][1].endswith("known-batch/manifest.json")


def test_failed_manifest_is_written_after_partial_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uploader = FakeUploader()
    responses: Any = iter([[{"id": 1}, {"id": 2}], RuntimeError("IGDB unavailable")])
    monkeypatch.setattr(
        extract,
        "get_app_access_token",
        lambda **kwargs: SimpleNamespace(access_token="token"),
    )

    def query_fn(**kwargs: Any) -> list[dict[str, int]]:
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    with pytest.raises(RuntimeError, match="IGDB unavailable"):
        extract.run_extraction(
            endpoint="genres",
            page_size=2,
            batch_id="failed-batch",
            uploader=uploader,
            query_fn=query_fn,
            now_fn=fixed_times(),
        )

    failed_manifest = uploader.uploads[-1][0]
    assert isinstance(failed_manifest, dict)
    assert failed_manifest["status"] == "failed"
    assert failed_manifest["page_count"] == 1
    assert failed_manifest["record_count"] == 2
    assert failed_manifest["failure"] == {
        "type": "RuntimeError",
        "message": "IGDB unavailable",
    }
