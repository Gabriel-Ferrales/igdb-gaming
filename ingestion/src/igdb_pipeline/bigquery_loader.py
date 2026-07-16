"""Explicit-schema staging loads and idempotent raw table merges."""

from google.cloud import bigquery

from igdb_pipeline.batch_models import BatchManifest, ConversionResult
from igdb_pipeline.schemas import CLUSTER_FIELDS, SCHEMAS


class BigQueryLoader:
    def __init__(self, client: bigquery.Client, project: str, dataset: str) -> None:
        self.client = client
        self.project = project
        self.dataset = dataset

    def ensure_tables(self, endpoint: str) -> None:
        for prefix in ("stg_", ""):
            table = bigquery.Table(
                f"{self.project}.{self.dataset}.{prefix}{endpoint}",
                schema=SCHEMAS[endpoint],
            )
            table.clustering_fields = CLUSTER_FIELDS[endpoint]
            self.client.create_table(table, exists_ok=True)

    def load_and_merge(self, batch: BatchManifest, conversion: ConversionResult) -> int:
        self.ensure_tables(batch.endpoint)
        staging = f"{self.project}.{self.dataset}.stg_{batch.endpoint}"
        raw = f"{self.project}.{self.dataset}.{batch.endpoint}"
        config = bigquery.LoadJobConfig(
            schema=SCHEMAS[batch.endpoint],
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
            ignore_unknown_values=False,
        )
        self.client.load_table_from_uri(
            list(conversion.output_uris), staging, job_config=config
        ).result()
        validation = next(
            iter(
                self.client.query(
                    f"""
            SELECT COUNT(*) row_count, COUNTIF(id IS NULL) null_ids,
                   COUNT(*) - COUNT(DISTINCT id) duplicate_ids
            FROM `{staging}` WHERE _batch_id=@batch_id
        """,
                    job_config=bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter(
                                "batch_id", "STRING", batch.batch_id
                            )
                        ]
                    ),
                ).result()
            )
        )
        if validation.row_count != conversion.record_count:
            raise ValueError(
                f"staging has {validation.row_count} rows; expected {conversion.record_count}"
            )
        if validation.null_ids or validation.duplicate_ids:
            raise ValueError(
                f"staging validation failed: null_ids={validation.null_ids}, duplicate_ids={validation.duplicate_ids}"
            )
        columns = [field.name for field in SCHEMAS[batch.endpoint]]
        updates = ", ".join(
            f"T.`{name}`=S.`{name}`" for name in columns if name != "id"
        )
        names = ", ".join(f"`{name}`" for name in columns)
        source_names = ", ".join(f"S.`{name}`" for name in columns)
        self.client.query(f"""
            MERGE `{raw}` T USING `{staging}` S ON T.id=S.id
            WHEN MATCHED THEN UPDATE SET {updates}
            WHEN NOT MATCHED THEN INSERT ({names}) VALUES ({source_names})
        """).result()
        return int(validation.row_count)
