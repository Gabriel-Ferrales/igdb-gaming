"""Validated models shared by the batch loading pipeline."""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class BatchManifest:
    endpoint: str
    batch_id: str
    load_type: str
    extraction_date: date
    status: str
    page_count: int | None
    record_count: int
    min_id: int | None
    max_id: int | None
    uploaded_objects: tuple[str, ...]
    manifest_uri: str
    manifest_object: str

    @classmethod
    def from_dict(
        cls, value: dict[str, Any], *, object_name: str, bucket: str
    ) -> "BatchManifest":
        parts = dict(
            part.split("=", 1) for part in object_name.split("/") if "=" in part
        )
        endpoint = object_name.split("/")[1]
        required = ("batch_id", "endpoint", "load_type", "status", "record_count")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(
                f"manifest is missing required fields: {', '.join(missing)}"
            )
        if value["endpoint"] != endpoint or value["batch_id"] != parts.get("batch_id"):
            raise ValueError("manifest values do not match its GCS path")
        extraction_date = date.fromisoformat(parts["extraction_date"])
        objects = tuple(value.get("uploaded_objects") or ())
        return cls(
            endpoint=endpoint,
            batch_id=str(value["batch_id"]),
            load_type=str(value["load_type"]),
            extraction_date=extraction_date,
            status=str(value["status"]),
            page_count=int(value["page_count"])
            if value.get("page_count") is not None
            else None,
            record_count=int(value["record_count"]),
            min_id=value.get("min_id"),
            max_id=value.get("max_id"),
            uploaded_objects=objects,
            manifest_uri=f"gs://{bucket}/{object_name}",
            manifest_object=object_name,
        )

    @property
    def key(self) -> tuple[str, str]:
        return self.endpoint, self.batch_id

    @property
    def load_ready_prefix(self) -> str:
        return (
            f"load_ready/{self.endpoint}/load_type={self.load_type}/"
            f"extraction_date={self.extraction_date.isoformat()}/batch_id={self.batch_id}"
        )


@dataclass(frozen=True)
class ConversionResult:
    record_count: int
    min_id: int
    max_id: int
    output_uris: tuple[str, ...]
    manifest_uri: str
