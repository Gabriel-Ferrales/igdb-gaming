"""Command-line entry point for the IGDB ingestion pipeline."""

import argparse
from pathlib import Path

from igdb_pipeline.extract import extract_games
from igdb_pipeline.storage import save_json_locally, upload_json_to_gcs


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract games from IGDB and upload them to GCS."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of games to extract. Maximum: 500.",
    )

    parser.add_argument(
        "--save-local",
        action="store_true",
        help="Also save the extracted records locally.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the games extraction pipeline."""
    args = parse_arguments()

    games = extract_games(limit=args.limit)

    print(f"Registros extraídos: {len(games)}")

    if args.save_local:
        local_path = save_json_locally(
            records=games,
            output_path=Path("data/games.json"),
        )
        print(f"Archivo local: {local_path.resolve()}")

    gcs_uri = upload_json_to_gcs(
        records=games,
        endpoint="games",
    )

    print(f"Archivo subido a GCS: {gcs_uri}")


if __name__ == "__main__":
    main()