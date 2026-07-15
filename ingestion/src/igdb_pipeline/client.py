"""HTTP client for the IGDB API."""

from typing import Any

import httpx

IGDB_BASE_URL = "https://api.igdb.com/v4"


def query_igdb(
    endpoint: str,
    query: str,
    client_id: str,
    access_token: str,
) -> list[dict[str, Any]]:
    """Send a query to an IGDB endpoint."""

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

    response.raise_for_status()
    return response.json()