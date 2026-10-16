# Roadmap

## Implemented

- Six-endpoint Python historical extraction with keyset pagination and immutable GCS batches.
- Manifest discovery, NDJSON conversion, validated BigQuery staging, batch registry, retries, and ID-based `MERGE`.
- dbt staging and intermediate views, dimensions, bridges, facts, five analytics marts, and data tests.
- Five-page Looker Studio dashboard with repository screenshots.
- Terraform resource definitions and local development tooling.

## Future improvements

- Add automated orchestration for extraction, loading, and dbt builds.
- Add persisted incremental watermarks and scheduled ingestion.
- Expand IGDB metadata coverage beyond the six current endpoints.
- Carry explicit source date precision into analytical marts and add quality monitoring.
- Retain rating observations over time instead of replacing current-state tables.
- Add CI/CD, deployment automation, and a production authentication workflow.

These are future directions, not prerequisites for reviewing the current portfolio project.
