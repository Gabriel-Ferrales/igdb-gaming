"""Generic, page-streaming extraction orchestration for IGDB resources."""

from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from igdb_pipeline.auth import get_app_access_token
from igdb_pipeline.client import query_igdb
from igdb_pipeline.config import settings
from igdb_pipeline.endpoints import get_endpoint_config
from igdb_pipeline.pagination import build_query, iter_pages
from igdb_pipeline.storage import (
    GCSJsonUploader,
    manifest_object_name,
    page_object_name,
)

Record = dict[str, Any]
QueryFunction = Callable[..., list[Record]]


class JsonUploader(Protocol):
    """Structural interface used by extraction and mocked in unit tests."""

    def upload(
        self,
        value: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        object_name: str,
    ) -> str: ...


def extract_pages(
    endpoint: str,
    fields: Sequence[str],
    page_size: int = 500,
    max_pages: int | None = None,
    max_records: int | None = None,
    start_after_id: int = 0,
    where: str | None = None,
    *,
    client_id: str,
    access_token: str,
    query_fn: QueryFunction = query_igdb,
) -> Iterator[list[Record]]:
    """Yield successive endpoint pages using the ID cursor."""
    config = get_endpoint_config(endpoint)

    def fetch_page(last_id: int, request_size: int) -> list[Record]:
        query = build_query(
            fields=fields,
            page_size=request_size,
            last_id=last_id,
            where=where,
            cursor_field=config.historical_cursor_field,
        )
        return query_fn(
            endpoint=endpoint,
            query=query,
            client_id=client_id,
            access_token=access_token,
        )

    yield from iter_pages(
        fetch_page,
        page_size=page_size,
        max_pages=max_pages,
        max_records=max_records,
        start_after_id=start_after_id,
    )


def run_extraction(
    endpoint: str,
    fields: Sequence[str] | None = None,
    page_size: int = 500,
    max_pages: int | None = None,
    max_records: int | None = None,
    start_after_id: int = 0,
    where: str | None = None,
    load_type: str = "historical",
    *,
    batch_id: str | None = None,
    uploader: JsonUploader | None = None,
    query_fn: QueryFunction = query_igdb,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Extract, upload each page, and finally write a completed/failed manifest."""
    if load_type != "historical":
        raise ValueError("Only historical extraction is implemented")

    config = get_endpoint_config(endpoint)
    requested_fields = tuple(fields or config.fields)
    current_time = now_fn or (lambda: datetime.now(UTC))
    started_at = current_time()
    extraction_date = started_at.date()
    batch_id = batch_id or uuid4().hex
    uploader = uploader or GCSJsonUploader()

    page_count = 0
    record_count = 0
    min_id: int | None = None
    max_id: int | None = None
    uploaded_objects: list[str] = []
    failure: dict[str, str] | None = None
    extraction_error: Exception | None = None

    try:
        token = get_app_access_token(
            client_id=settings.twitch_client_id,
            client_secret=settings.twitch_client_secret,
        )
        pages = extract_pages(
            endpoint=endpoint,
            fields=requested_fields,
            page_size=page_size,
            max_pages=max_pages,
            max_records=max_records,
            start_after_id=start_after_id,
            where=where,
            client_id=settings.twitch_client_id,
            access_token=token.access_token,
            query_fn=query_fn,
        )
        for page in pages:
            page_min_id = page[0][config.historical_cursor_field]
            page_max_id = page[-1][config.historical_cursor_field]
            name = page_object_name(
                endpoint,
                load_type,
                extraction_date,
                batch_id,
                page_min_id,
                page_max_id,
            )
            uploaded_objects.append(uploader.upload(page, name))
            page_count += 1
            record_count += len(page)
            min_id = page_min_id if min_id is None else min(min_id, page_min_id)
            max_id = page_max_id if max_id is None else max(max_id, page_max_id)
        status = "completed"
    except Exception as error:
        status = "failed"
        extraction_error = error
        failure = {"type": type(error).__name__, "message": str(error)}

    manifest: dict[str, Any] = {
        "batch_id": batch_id,
        "endpoint": endpoint,
        "load_type": load_type,
        "status": status,
        "page_size": page_size,
        "page_count": page_count,
        "record_count": record_count,
        "min_id": min_id,
        "max_id": max_id,
        "started_at": started_at.isoformat(),
        "completed_at": current_time().isoformat(),
        "uploaded_objects": uploaded_objects.copy(),
        "failure": failure,
    }
    manifest_name = manifest_object_name(endpoint, load_type, extraction_date, batch_id)
    uploader.upload(manifest, manifest_name)

    if extraction_error is not None:
        raise extraction_error
    return manifest


def extract_games(limit: int = 100) -> list[Record]:
    """Backward-compatible single-page games extraction helper."""
    config = get_endpoint_config("games")
    token = get_app_access_token(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret,
    )
    pages = extract_pages(
        endpoint="games",
        fields=config.fields,
        page_size=limit,
        max_pages=1,
        client_id=settings.twitch_client_id,
        access_token=token.access_token,
    )
    return next(pages, [])
