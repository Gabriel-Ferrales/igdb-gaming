"""Tests for deterministic keyset pagination."""

import pytest

from igdb_pipeline.pagination import (
    build_query,
    combine_where_clause,
    iter_pages,
)


def test_build_query_uses_cursor_sort_and_limit() -> None:
    query = build_query(["id", "name"], page_size=250, last_id=42)

    assert query == ("fields id, name;\nwhere id > 42;\nsort id asc;\nlimit 250;")
    assert "offset" not in query.lower()


def test_where_clause_is_parenthesized_before_combining() -> None:
    result = combine_where_clause("id", 10, "category = 0 | category = 1;")

    assert result == "(id > 10) & (category = 0 | category = 1)"


def test_where_clause_rejects_multiple_statements() -> None:
    with pytest.raises(ValueError, match="one IGDB filter"):
        combine_where_clause("id", 0, "name != null; limit 1")


def test_cursor_progresses_between_pages_and_stops_on_empty_page() -> None:
    calls: list[tuple[int, int]] = []
    responses = iter([[{"id": 1}, {"id": 3}], [{"id": 4}, {"id": 8}], []])

    def fetch(last_id: int, size: int) -> list[dict[str, int]]:
        calls.append((last_id, size))
        return next(responses)

    assert list(iter_pages(fetch, page_size=2)) == [
        [{"id": 1}, {"id": 3}],
        [{"id": 4}, {"id": 8}],
    ]
    assert calls == [(0, 2), (3, 2), (8, 2)]


def test_partial_final_page_stops_without_empty_request() -> None:
    calls = 0

    def fetch(last_id: int, size: int) -> list[dict[str, int]]:
        nonlocal calls
        calls += 1
        return [{"id": 11}]

    assert list(iter_pages(fetch, page_size=2, start_after_id=10)) == [[{"id": 11}]]
    assert calls == 1


def test_max_pages_stops_page_requests() -> None:
    cursors: list[int] = []

    def fetch(last_id: int, size: int) -> list[dict[str, int]]:
        cursors.append(last_id)
        return [{"id": last_id + 1}]

    pages = list(iter_pages(fetch, page_size=1, max_pages=2))

    assert pages == [[{"id": 1}], [{"id": 2}]]
    assert cursors == [0, 1]


def test_max_records_reduces_final_request_size() -> None:
    request_sizes: list[int] = []

    def fetch(last_id: int, size: int) -> list[dict[str, int]]:
        request_sizes.append(size)
        return [{"id": last_id + offset + 1} for offset in range(size)]

    pages = list(iter_pages(fetch, page_size=3, max_records=5))

    assert [len(page) for page in pages] == [3, 2]
    assert request_sizes == [3, 2]


def test_duplicate_id_between_pages_is_rejected() -> None:
    responses = iter([[{"id": 1}, {"id": 2}], [{"id": 2}, {"id": 3}]])

    with pytest.raises(ValueError, match="did not advance"):
        list(iter_pages(lambda _last_id, _size: next(responses), page_size=2))


def test_resume_uses_start_after_id_as_first_cursor() -> None:
    cursors: list[int] = []

    def fetch(last_id: int, size: int) -> list[dict[str, int]]:
        cursors.append(last_id)
        return []

    assert list(iter_pages(fetch, page_size=100, start_after_id=987)) == []
    assert cursors == [987]
