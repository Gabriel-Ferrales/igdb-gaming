"""Orchestration for resumable GCS-to-BigQuery batch ingestion."""

import logging
from dataclasses import dataclass

from google.cloud import bigquery, storage

from igdb_pipeline.batch_discovery import discover_batches
from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.batch_registry import BatchRegistry
from igdb_pipeline.bigquery_loader import BigQueryLoader
from igdb_pipeline.json_converter import convert_batch, validate_conversion_manifest

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchDecision:
    batch: BatchManifest
    action: str
    reason: str


class BatchPipeline:
    def __init__(
        self,
        storage_client: storage.Client,
        bq_client: bigquery.Client,
        *,
        project: str,
        bucket: str,
        dataset: str,
    ) -> None:
        self.storage_client = storage_client
        self.bucket = bucket
        self.registry = BatchRegistry(bq_client, project, dataset)
        self.loader = BigQueryLoader(bq_client, project, dataset)

    def plan(
        self,
        *,
        endpoints: set[str] | None = None,
        batch_id: str | None = None,
        max_batches: int | None = None,
        retry_failed: bool = False,
        read_registry: bool = True,
    ) -> list[BatchDecision]:
        batches = discover_batches(self.storage_client, self.bucket)
        statuses = self.registry.statuses() if read_registry else {}
        decisions: list[BatchDecision] = []
        selected = 0
        for batch in batches:
            status = statuses.get(batch.key)
            if endpoints and batch.endpoint not in endpoints:
                decisions.append(
                    BatchDecision(batch, "ignore", "endpoint not selected")
                )
                continue
            if batch_id and batch.batch_id != batch_id:
                decisions.append(
                    BatchDecision(batch, "ignore", "batch_id not selected")
                )
                continue
            if batch.status != "completed":
                decisions.append(
                    BatchDecision(batch, "ignore", f"manifest status is {batch.status}")
                )
                continue
            if status == "loaded":
                decisions.append(BatchDecision(batch, "ignore", "already loaded"))
                continue
            if status == "failed" and not retry_failed and not batch_id:
                decisions.append(
                    BatchDecision(batch, "ignore", "failed; pass --retry-failed")
                )
                continue
            if max_batches is not None and selected >= max_batches:
                decisions.append(BatchDecision(batch, "ignore", "max-batches reached"))
                continue
            action = "load" if status == "converted" else "convert-and-load"
            decisions.append(
                BatchDecision(
                    batch, action, f"registry status: {status or 'not registered'}"
                )
            )
            selected += 1
        return decisions

    def run(
        self, decisions: list[BatchDecision], *, skip_conversion: bool = False
    ) -> None:
        self.registry.ensure_table()
        for decision in decisions:
            if decision.action == "ignore":
                continue
            batch = decision.batch
            self.registry.register_discovered(batch)
            try:
                if decision.action == "load" or skip_conversion:
                    conversion = validate_conversion_manifest(
                        self.storage_client, self.bucket, batch
                    )
                    if skip_conversion:
                        self.registry.set_status(
                            batch,
                            "converted",
                            converted_record_count=conversion.record_count,
                            min_id=conversion.min_id,
                            max_id=conversion.max_id,
                        )
                else:
                    self.registry.set_status(batch, "converting")
                    conversion = convert_batch(self.storage_client, self.bucket, batch)
                    self.registry.set_status(
                        batch,
                        "converted",
                        converted_record_count=conversion.record_count,
                        min_id=conversion.min_id,
                        max_id=conversion.max_id,
                    )
                self.registry.set_status(batch, "loading")
                loaded = self.loader.load_and_merge(batch, conversion)
                self.registry.set_status(batch, "loaded", loaded_record_count=loaded)
                LOGGER.info(
                    "Loaded %s/%s (%d records)", batch.endpoint, batch.batch_id, loaded
                )
            except Exception as error:
                LOGGER.exception("Batch %s/%s failed", batch.endpoint, batch.batch_id)
                self.registry.set_status(
                    batch, "failed", error_message=str(error)[:10000]
                )
