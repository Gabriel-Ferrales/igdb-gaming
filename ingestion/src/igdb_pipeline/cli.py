"""Command-line entry point for the IGDB ingestion pipeline."""

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from igdb_pipeline.endpoints import ENDPOINTS
from igdb_pipeline.extract import run_extraction
from igdb_pipeline.storage import GCSJsonUploader


class LocalMirroringUploader:
    """Mirror streamed GCS objects locally for the legacy save-local option."""

    def __init__(self, uploader: GCSJsonUploader, root: Path) -> None:
        self._uploader = uploader
        self._root = root

    def upload(
        self,
        value: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        object_name: str,
    ) -> str:
        uri = self._uploader.upload(value, object_name)
        path = self._root / object_name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
        return uri


def build_parser() -> argparse.ArgumentParser:
    """Create the command parser."""
    parser = argparse.ArgumentParser(description="Extract IGDB data to GCS.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract_parser = subparsers.add_parser("extract", help="Run an extraction batch.")
    extract_parser.add_argument("--endpoint", choices=tuple(ENDPOINTS), default="games")
    extract_parser.add_argument("--page-size", type=int, default=500)
    extract_parser.add_argument("--max-pages", type=int)
    extract_parser.add_argument(
        "--max-records", "--limit", dest="max_records", type=int
    )
    extract_parser.add_argument("--start-after-id", type=int, default=0)
    extract_parser.add_argument("--where")
    extract_parser.add_argument(
        "--load-type", choices=("historical",), default="historical"
    )
    extract_parser.add_argument(
        "--save-local",
        action="store_true",
        help="Also mirror each uploaded page and manifest below data/.",
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse arguments, treating legacy option-only invocation as extract."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0].startswith("-"):
        arguments.insert(0, "extract")
    return build_parser().parse_args(arguments)


def main() -> None:
    """Run the selected extraction command."""
    args = parse_arguments()
    uploader: GCSJsonUploader | LocalMirroringUploader = GCSJsonUploader()
    if args.save_local:
        uploader = LocalMirroringUploader(uploader, Path("data"))

    manifest = run_extraction(
        endpoint=args.endpoint,
        page_size=args.page_size,
        max_pages=args.max_pages,
        max_records=args.max_records,
        start_after_id=args.start_after_id,
        where=args.where,
        load_type=args.load_type,
        uploader=uploader,
    )
    print(
        f"Batch {manifest['batch_id']} completed: "
        f"{manifest['record_count']} records in {manifest['page_count']} pages."
    )


if __name__ == "__main__":
    main()
