"""Authentication with Twitch for access to the IGDB API."""

from dataclasses import dataclass

import httpx

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


@dataclass(frozen=True)
class TwitchToken:
    """Twitch application access token."""

    access_token: str
    expires_in: int
    token_type: str


def get_app_access_token(
    client_id: str,
    client_secret: str,
) -> TwitchToken:
    """Obtain a Twitch app access token using client credentials."""

    response = httpx.post(
        TWITCH_TOKEN_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=30.0,
    )

    response.raise_for_status()
    payload = response.json()

    return TwitchToken(
        access_token=payload["access_token"],
        expires_in=payload["expires_in"],
        token_type=payload["token_type"],
    )
