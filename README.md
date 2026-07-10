# IGDB Gaming Analytics

Production-style data engineering portfolio monorepo for extracting game data from IGDB, landing immutable objects in Google Cloud Storage, loading BigQuery, and transforming analytics models with dbt. Kestra will orchestrate historical, incremental, and transformation workloads.

## Architecture

`IGDB API → Python ingestion → GCS → BigQuery raw → dbt staging/intermediate/marts → dashboard`

Terraform defines the bucket, datasets, service account, and least-privilege project roles. Kestra is isolated in its own Docker Compose stack. See [docs/architecture.md](docs/architecture.md).

## Repository layout

- `ingestion/`: Python 3.11 API extraction package and tests
- `dbt/`: independent dbt Core/BigQuery project
- `terraform/`: reusable GCS, BigQuery, and IAM modules
- `kestra/`: local orchestrator and placeholder flows
- `sql/`, `notebooks/`, `dashboards/`: analysis and presentation workspaces
- `docs/`: architecture, dictionary, and decision records

## Requirements

- Git, Python 3.11, and [uv](https://docs.astral.sh/uv/)
- Terraform 1.6+
- Docker with Docker Compose
- A GCP project and Application Default Credentials for cloud operations
- Twitch/IGDB API credentials for future ingestion

## Setup

1. Copy `.env.example` to `.env` and fill it locally. Never commit it.
2. Run `make setup` to create both component environments.
3. Copy `dbt/profiles/profiles.yml.example` to `dbt/profiles/profiles.yml`.
4. Export the environment variables required by that profile.
5. Run `make terraform-init && make terraform-validate` before any reviewed infrastructure deployment.

## Common commands

Run `make ingestion-test`, `make ingestion-lint`, `make dbt-debug`, `make dbt-build-dev`, `make terraform-fmt`, or `make kestra-up`. Run `make help` for the full list. The prod dbt target is explicit: `make dbt-build-prod`.

## Security

Use environment variables or a secret manager. Never store Twitch secrets, GCP project identifiers, credential JSON, service-account keys, Terraform variable files, or dbt profiles containing secrets in Git. Review Terraform plans and cloud cost implications before applying; this repository intentionally provides no automatic `terraform apply` command.

