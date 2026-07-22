"""CLI for discovering and loading existing extraction batches."""

import argparse
import logging
from collections.abc import Sequence

from google.cloud import bigquery, storage
from google.oauth2 import service_account

from igdb_pipeline.batch_pipeline import BatchPipeline
from igdb_pipeline.config import settings
from igdb_pipeline.endpoints import ENDPOINTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load existing IGDB GCS batches into BigQuery."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser("discover", help="List manifests without writing state.")
    discover.add_argument("--endpoint", choices=tuple(ENDPOINTS))
    run = sub.add_parser("run", help="Convert and load selected batches.")
    selection = run.add_mutually_exclusive_group(required=True)
    selection.add_argument("--endpoint", choices=tuple(ENDPOINTS))
    selection.add_argument("--all-endpoints", action="store_true")
    run.add_argument("--max-batches", type=int)
    run.add_argument("--retry-failed", action="store_true")
    run.add_argument("--batch-id")
    run.add_argument("--skip-conversion", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    return parser


def _clients() -> tuple[storage.Client, bigquery.Client]:
    credentials = service_account.Credentials.from_service_account_file(
        settings.google_application_credentials
    )
    return (
        storage.Client(project=settings.gcp_project_id, credentials=credentials),
        bigquery.Client(project=settings.gcp_project_id, credentials=credentials),
    )


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    storage_client, bq_client = _clients()
    pipeline = BatchPipeline(
        storage_client,
        bq_client,
        project=settings.gcp_project_id,
        bucket=settings.gcs_bucket_name,
        dataset=settings.bq_raw_dataset,
    )
    endpoint = getattr(args, "endpoint", None)
    is_discover = args.command == "discover"
    decisions = pipeline.plan(
        endpoints={endpoint} if endpoint else None,
        batch_id=getattr(args, "batch_id", None),
        max_batches=getattr(args, "max_batches", None),
        retry_failed=getattr(args, "retry_failed", False),
        read_registry=not is_discover,
    )
    for item in decisions:
        print(
            f"{item.action:16} {item.batch.endpoint}/{item.batch.batch_id}: {item.reason}"
        )
    if is_discover:
        return 0
    if args.dry_run:
        skipped = sum(item.action == "ignore" for item in decisions)
        logging.getLogger(__name__).info(
            "Batch run summary: loaded=0 skipped=%d failed=0", skipped
        )
        return 0
    summary = pipeline.run(decisions, skip_conversion=args.skip_conversion)
    return 1 if summary.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
