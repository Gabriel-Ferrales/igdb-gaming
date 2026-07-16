"""Explicit BigQuery schemas for every supported endpoint."""

from google.cloud import bigquery

S = bigquery.SchemaField
COMMON = [
    S("id", "INT64", mode="REQUIRED"),
    S("created_at", "INT64"),
    S("updated_at", "INT64"),
    S("checksum", "STRING"),
]
METADATA = [
    S("created_at_ts", "TIMESTAMP"),
    S("updated_at_ts", "TIMESTAMP"),
    S("_batch_id", "STRING", mode="REQUIRED"),
    S("_source_file", "STRING", mode="REQUIRED"),
    S("_load_type", "STRING", mode="REQUIRED"),
    S("_extraction_date", "DATE", mode="REQUIRED"),
    S("_loaded_at", "TIMESTAMP", mode="REQUIRED"),
]


def fields(*items: tuple[str, str, str | None]) -> list[bigquery.SchemaField]:
    return [S(name, kind, mode=mode or "NULLABLE") for name, kind, mode in items]


SCHEMAS = {
    "games": COMMON
    + fields(
        ("name", "STRING", None),
        ("slug", "STRING", None),
        ("summary", "STRING", None),
        ("first_release_date", "INT64", None),
        ("first_release_date_ts", "TIMESTAMP", None),
        ("category", "INT64", None),
        ("status", "INT64", None),
        ("rating", "FLOAT64", None),
        ("rating_count", "INT64", None),
        ("aggregated_rating", "FLOAT64", None),
        ("aggregated_rating_count", "INT64", None),
        ("genres", "INT64", "REPEATED"),
        ("platforms", "INT64", "REPEATED"),
        ("involved_companies", "INT64", "REPEATED"),
        ("release_dates", "INT64", "REPEATED"),
    )
    + METADATA,
    "platforms": COMMON
    + fields(
        ("name", "STRING", None),
        ("slug", "STRING", None),
        ("abbreviation", "STRING", None),
        ("alternative_name", "STRING", None),
        ("category", "INT64", None),
        ("generation", "INT64", None),
        ("platform_family", "INT64", None),
        ("platform_logo", "INT64", None),
        ("versions", "INT64", "REPEATED"),
        ("websites", "INT64", "REPEATED"),
    )
    + METADATA,
    "genres": COMMON
    + fields(("name", "STRING", None), ("slug", "STRING", None))
    + METADATA,
    "companies": COMMON
    + fields(
        ("name", "STRING", None),
        ("slug", "STRING", None),
        ("description", "STRING", None),
        ("country", "INT64", None),
        ("developed", "INT64", "REPEATED"),
        ("published", "INT64", "REPEATED"),
        ("parent", "INT64", None),
        ("start_date", "INT64", None),
        ("start_date_ts", "TIMESTAMP", None),
        ("changed_company_id", "INT64", None),
        ("logo", "INT64", None),
        ("websites", "INT64", "REPEATED"),
        ("url", "STRING", None),
    )
    + METADATA,
    "involved_companies": COMMON
    + fields(
        ("game", "INT64", None),
        ("company", "INT64", None),
        ("developer", "BOOL", None),
        ("publisher", "BOOL", None),
        ("porting", "BOOL", None),
        ("supporting", "BOOL", None),
    )
    + METADATA,
    "release_dates": COMMON
    + fields(
        ("game", "INT64", None),
        ("platform", "INT64", None),
        ("date", "INT64", None),
        ("date_ts", "TIMESTAMP", None),
        ("human", "STRING", None),
        ("m", "INT64", None),
        ("y", "INT64", None),
        ("region", "INT64", None),
        ("status", "INT64", None),
        ("category", "INT64", None),
    )
    + METADATA,
}

CLUSTER_FIELDS = {
    "games": ["id"],
    "platforms": ["id"],
    "genres": ["id"],
    "companies": ["id"],
    "involved_companies": ["game", "company"],
    "release_dates": ["game", "platform"],
}

INGESTION_BATCHES_SCHEMA = fields(
    ("endpoint", "STRING", None),
    ("batch_id", "STRING", None),
    ("load_type", "STRING", None),
    ("extraction_date", "DATE", None),
    ("manifest_uri", "STRING", None),
    ("source_record_count", "INT64", None),
    ("converted_record_count", "INT64", None),
    ("loaded_record_count", "INT64", None),
    ("min_id", "INT64", None),
    ("max_id", "INT64", None),
    ("status", "STRING", None),
    ("discovered_at", "TIMESTAMP", None),
    ("conversion_started_at", "TIMESTAMP", None),
    ("conversion_completed_at", "TIMESTAMP", None),
    ("load_started_at", "TIMESTAMP", None),
    ("load_completed_at", "TIMESTAMP", None),
    ("error_message", "STRING", None),
)
