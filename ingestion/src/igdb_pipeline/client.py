"""HTTP client for the IGDB API with bounded transient-error retries."""

import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

IGDB_BASE_URL = "https://api.igdb.com/v4"
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _retry_after_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())


def query_igdb(
    endpoint: str,
    query: str,
    client_id: str,
    access_token: str,
    *,
    max_retries: int = 3,
    backoff_base_seconds: float = 1.0,
) -> list[dict[str, Any]]:
    """Send a query to an IGDB endpoint."""
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    if backoff_base_seconds < 0:
        raise ValueError("backoff_base_seconds must be non-negative")

    for attempt in range(max_retries + 1):
        try:
            response = httpx.post(
                f"{IGDB_BASE_URL}/{endpoint}",
                headers={
                    "Client-ID": client_id,
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                content=query,
                timeout=30.0,
            )
        except httpx.TimeoutException:
            if attempt == max_retries:
                raise
            time.sleep(backoff_base_seconds * (2**attempt))
            continue

        if response.status_code not in RETRYABLE_STATUS_CODES:
            response.raise_for_status()
            return response.json()
        if attempt == max_retries:
            response.raise_for_status()

        retry_after = _retry_after_seconds(response.headers.get("Retry-After"))
        delay = (
            retry_after
            if retry_after is not None
            else backoff_base_seconds * (2**attempt)
        )
        time.sleep(delay)

    raise RuntimeError("unreachable")
