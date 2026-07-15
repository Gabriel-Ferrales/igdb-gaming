"""Central configuration for supported IGDB endpoints."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class EndpointConfig:
    """Fields and cursor metadata for one IGDB endpoint."""

    name: str
    fields: tuple[str, ...]
    historical_cursor_field: str = "id"
    incremental_watermark_field: str = "updated_at"


_ENDPOINTS = {
    "games": EndpointConfig(
        name="games",
        fields=(
            "id",
            "name",
            "slug",
            "summary",
            "first_release_date",
            "created_at",
            "updated_at",
            "category",
            "status",
            "rating",
            "rating_count",
            "aggregated_rating",
            "aggregated_rating_count",
            "genres",
            "platforms",
            "involved_companies",
            "release_dates",
            "checksum",
        ),
    ),
    "platforms": EndpointConfig(
        name="platforms",
        fields=(
            "id",
            "name",
            "slug",
            "abbreviation",
            "alternative_name",
            "category",
            "generation",
            "platform_family",
            "platform_logo",
            "versions",
            "websites",
            "created_at",
            "updated_at",
            "checksum",
        ),
    ),
    "genres": EndpointConfig(
        name="genres",
        fields=("id", "name", "slug", "created_at", "updated_at", "checksum"),
    ),
    "companies": EndpointConfig(
        name="companies",
        fields=(
            "id",
            "name",
            "slug",
            "description",
            "country",
            "developed",
            "published",
            "parent",
            "start_date",
            "changed_company_id",
            "logo",
            "websites",
            "url",
            "created_at",
            "updated_at",
            "checksum",
        ),
    ),
    "involved_companies": EndpointConfig(
        name="involved_companies",
        fields=(
            "id",
            "game",
            "company",
            "developer",
            "publisher",
            "porting",
            "supporting",
            "created_at",
            "updated_at",
            "checksum",
        ),
    ),
    "release_dates": EndpointConfig(
        name="release_dates",
        fields=(
            "id",
            "game",
            "platform",
            "date",
            "human",
            "m",
            "y",
            "region",
            "status",
            "category",
            "created_at",
            "updated_at",
            "checksum",
        ),
    ),
}

ENDPOINTS: Mapping[str, EndpointConfig] = MappingProxyType(_ENDPOINTS)

# Kept as a derived view for exploration code; fields are defined only above.
ENDPOINT_FIELDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {name: config.fields for name, config in ENDPOINTS.items()}
)


def get_endpoint_config(endpoint: str) -> EndpointConfig:
    """Return endpoint configuration with a useful error for unsupported names."""
    try:
        return ENDPOINTS[endpoint]
    except KeyError as error:
        supported = ", ".join(ENDPOINTS)
        raise ValueError(
            f"Unsupported endpoint {endpoint!r}. Supported endpoints: {supported}"
        ) from error
