"""Deterministic keyset pagination for IGDB results."""

from collections.abc import Callable, Iterator, Sequence
from typing import Any

Record = dict[str, Any]
FetchPage = Callable[[int, int], list[Record]]


def normalize_where_clause(where: str | None) -> str | None:
    """Normalize a filter expression and reject additional query statements."""
    if where is None or not where.strip():
        return None

    expression = where.strip()
    if expression.lower().startswith("where "):
        expression = expression[6:].strip()
    if expression.endswith(";"):
        expression = expression[:-1].rstrip()
    if not expression or ";" in expression:
        raise ValueError("where must contain exactly one IGDB filter expression")
    return expression


def combine_where_clause(
    cursor_field: str,
    last_id: int,
    where: str | None = None,
) -> str:
    """Combine a cursor predicate with an optional, parenthesized filter."""
    cursor = f"{cursor_field} > {last_id}"
    expression = normalize_where_clause(where)
    if expression is None:
        return cursor
    return f"({cursor}) & ({expression})"


def build_query(
    fields: Sequence[str],
    page_size: int,
    last_id: int,
    where: str | None = None,
    cursor_field: str = "id",
) -> str:
    """Build one deterministic IGDB keyset-pagination query."""
    if not fields:
        raise ValueError("fields must not be empty")
    if not 1 <= page_size <= 500:
        raise ValueError("page_size must be between 1 and 500")
    if last_id < 0:
        raise ValueError("last_id must be non-negative")

    predicate = combine_where_clause(cursor_field, last_id, where)
    return "\n".join(
        (
            f"fields {', '.join(fields)};",
            f"where {predicate};",
            f"sort {cursor_field} asc;",
            f"limit {page_size};",
        )
    )


def iter_pages(
    fetch_page: FetchPage,
    *,
    page_size: int,
    max_pages: int | None = None,
    max_records: int | None = None,
    start_after_id: int = 0,
) -> Iterator[list[Record]]:
    """Yield validated pages without retaining prior page data in memory."""
    if not 1 <= page_size <= 500:
        raise ValueError("page_size must be between 1 and 500")
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be positive when provided")
    if max_records is not None and max_records < 1:
        raise ValueError("max_records must be positive when provided")
    if start_after_id < 0:
        raise ValueError("start_after_id must be non-negative")

    last_id = start_after_id
    page_count = 0
    record_count = 0

    while max_pages is None or page_count < max_pages:
        remaining = (
            page_size
            if max_records is None
            else min(page_size, max_records - record_count)
        )
        if remaining <= 0:
            return

        page = fetch_page(last_id, remaining)
        if not page:
            return

        ids = [record.get("id") for record in page]
        if any(not isinstance(record_id, int) for record_id in ids):
            raise ValueError("Every IGDB record must contain an integer id")
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise ValueError("IGDB page ids must be unique and sorted ascending")
        if ids[0] <= last_id:
            raise ValueError("IGDB page did not advance beyond the cursor")

        yield page

        page_count += 1
        record_count += len(page)
        last_id = ids[-1]
        if len(page) < remaining:
            return
