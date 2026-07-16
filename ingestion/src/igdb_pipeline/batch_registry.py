"""Idempotent BigQuery registry for ingestion batch state."""

from typing import Any

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from igdb_pipeline.batch_models import BatchManifest
from igdb_pipeline.schemas import INGESTION_BATCHES_SCHEMA

VALID_STATES = {"discovered", "converting", "converted", "loading", "loaded", "failed"}


class BatchRegistry:
    def __init__(self, client: bigquery.Client, project: str, dataset: str) -> None:
        self.client = client
        self.table_id = f"{project}.{dataset}.ingestion_batches"

    def ensure_table(self) -> None:
        table = bigquery.Table(self.table_id, schema=INGESTION_BATCHES_SCHEMA)
        table.clustering_fields = ["endpoint", "batch_id"]
        self.client.create_table(table, exists_ok=True)

    def statuses(self) -> dict[tuple[str, str], str]:
        try:
            rows = self.client.query(
                f"SELECT endpoint, batch_id, status FROM `{self.table_id}`"
            ).result()
        except NotFound:
            return {}
        return {(row.endpoint, row.batch_id): row.status for row in rows}

    def register_discovered(self, batch: BatchManifest) -> None:
        query = f"""
        MERGE `{self.table_id}` T USING (SELECT @endpoint endpoint, @batch_id batch_id) S
        ON T.endpoint=S.endpoint AND T.batch_id=S.batch_id
        WHEN NOT MATCHED THEN INSERT
          (endpoint,batch_id,load_type,extraction_date,manifest_uri,source_record_count,min_id,max_id,status,discovered_at)
          VALUES(@endpoint,@batch_id,@load_type,@extraction_date,@manifest_uri,@count,@min_id,@max_id,'discovered',CURRENT_TIMESTAMP())
        """
        self._query(
            query,
            endpoint=batch.endpoint,
            batch_id=batch.batch_id,
            load_type=batch.load_type,
            extraction_date=batch.extraction_date,
            manifest_uri=batch.manifest_uri,
            count=batch.record_count,
            min_id=batch.min_id,
            max_id=batch.max_id,
        )

    def set_status(self, batch: BatchManifest, status: str, **values: Any) -> None:
        if status not in VALID_STATES:
            raise ValueError(f"invalid registry status: {status}")
        timestamp_columns = {
            "converting": "conversion_started_at",
            "converted": "conversion_completed_at",
            "loading": "load_started_at",
            "loaded": "load_completed_at",
        }
        assignments = ["status=@status", "error_message=@error_message"]
        if column := timestamp_columns.get(status):
            assignments.append(f"{column}=CURRENT_TIMESTAMP()")
        for key in (
            "converted_record_count",
            "loaded_record_count",
            "min_id",
            "max_id",
        ):
            if key in values:
                assignments.append(f"{key}=@{key}")
        query = f"UPDATE `{self.table_id}` SET {', '.join(assignments)} WHERE endpoint=@endpoint AND batch_id=@batch_id"
        self._query(
            query,
            endpoint=batch.endpoint,
            batch_id=batch.batch_id,
            status=status,
            error_message=values.get("error_message"),
            **{k: v for k, v in values.items() if k != "error_message"},
        )

    def _query(self, sql: str, **parameters: Any) -> None:
        query_parameters = []
        parameter_types = {
            "extraction_date": "DATE",
            "count": "INT64",
            "converted_record_count": "INT64",
            "loaded_record_count": "INT64",
            "min_id": "INT64",
            "max_id": "INT64",
        }
        for name, value in parameters.items():
            kind = parameter_types.get(name, "STRING")
            query_parameters.append(bigquery.ScalarQueryParameter(name, kind, value))
        self.client.query(
            sql, job_config=bigquery.QueryJobConfig(query_parameters=query_parameters)
        ).result()
