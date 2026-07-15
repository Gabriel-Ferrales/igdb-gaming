"""Tests for IGDB HTTP retry behavior."""

from collections.abc import Iterator

import httpx
import pytest

from igdb_pipeline import client


def response(status: int, *, retry_after: str | None = None) -> httpx.Response:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    request = httpx.Request("POST", "https://api.igdb.com/v4/games")
    return httpx.Response(status, headers=headers, json=[{"id": 1}], request=request)


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_retryable_http_errors_are_retried(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    responses: Iterator[httpx.Response] = iter([response(status), response(200)])
    sleeps: list[float] = []
    monkeypatch.setattr(client.httpx, "post", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(client.time, "sleep", sleeps.append)

    result = client.query_igdb("games", "fields id;", "client", "token")

    assert result == [{"id": 1}]
    assert sleeps == [1.0]


def test_retry_after_header_controls_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([response(429, retry_after="7"), response(200)])
    sleeps: list[float] = []
    monkeypatch.setattr(client.httpx, "post", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(client.time, "sleep", sleeps.append)

    client.query_igdb("games", "fields id;", "client", "token")

    assert sleeps == [7.0]


def test_retries_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    def post(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response(503)

    monkeypatch.setattr(client.httpx, "post", post)
    monkeypatch.setattr(client.time, "sleep", sleeps.append)

    with pytest.raises(httpx.HTTPStatusError):
        client.query_igdb("games", "fields id;", "client", "token", max_retries=2)

    assert calls == 3
    assert sleeps == [1.0, 2.0]


def test_timeout_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    outcomes: Iterator[httpx.Response | Exception] = iter(
        [httpx.ReadTimeout("slow"), response(200)]
    )
    sleeps: list[float] = []

    def post(*args: object, **kwargs: object) -> httpx.Response:
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(client.httpx, "post", post)
    monkeypatch.setattr(client.time, "sleep", sleeps.append)

    assert client.query_igdb("games", "fields id;", "client", "token") == [{"id": 1}]
    assert sleeps == [1.0]


@pytest.mark.parametrize("status", [400, 401, 403])
def test_non_retryable_http_errors_fail_immediately(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    calls = 0

    def post(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response(status)

    monkeypatch.setattr(client.httpx, "post", post)
    monkeypatch.setattr(
        client.time,
        "sleep",
        lambda seconds: pytest.fail(f"unexpected sleep: {seconds}"),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.query_igdb("games", "fields id;", "client", "token")
    assert calls == 1
