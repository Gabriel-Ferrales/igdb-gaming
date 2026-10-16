# Architecture decisions

- Keep ingestion and dbt in independent uv environments.
- Separate raw, development, and production BigQuery datasets.
- Run the current pipeline manually and keep infrastructure declarative.
