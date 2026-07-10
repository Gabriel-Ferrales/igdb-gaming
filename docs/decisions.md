# Architecture decisions

- Keep ingestion and dbt in independent uv environments.
- Separate raw, development, and production BigQuery datasets.
- Keep orchestration local-first and infrastructure declarative.
