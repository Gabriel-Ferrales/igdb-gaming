# Architecture

IGDB data will be extracted by the Python package, stored as immutable raw objects in GCS, loaded into `gaming_raw`, and transformed by dbt into environment-specific BigQuery datasets. Kestra will coordinate retries, schedules, backfills, and dbt builds.
