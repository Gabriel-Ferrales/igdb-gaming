"""Dataset extraction orchestration interfaces."""
"""Extraction functions for IGDB resources."""

from typing import Any

from igdb_pipeline.auth import get_app_access_token
from igdb_pipeline.client import query_igdb
from igdb_pipeline.config import settings


def extract_games(limit: int = 100) -> list[dict[str, Any]]:
    """Extract games from IGDB.

    Args:
        limit: Maximum number of games to retrieve. IGDB allows up to
            500 records per request.

    Returns:
        A list of game records returned by IGDB.
    """
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    token = get_app_access_token(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret,
    )

    query = f"""
        fields
            id,
            name,
            slug,
            first_release_date,
            rating,
            rating_count,
            genres,
            platforms;
        where name != null;
        sort id asc;
        limit {limit};
    """

    return query_igdb(
        endpoint="games",
        query=query,
        client_id=settings.twitch_client_id,
        access_token=token.access_token,
    )