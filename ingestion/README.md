# IGDB ingestion

Generic historical extraction for the configured IGDB endpoints. Extraction uses
ID keyset pagination, uploads one immutable JSON object per page, and writes a
completed or failed batch manifest after page processing.

```bash
uv run python -m igdb_pipeline.cli extract \
  --endpoint games \
  --page-size 500 \
  --max-pages 2 \
  --start-after-id 0 \
  --load-type historical
```

Supported endpoints are `games`, `platforms`, `genres`, `companies`,
`involved_companies`, and `release_dates`. The legacy option-only CLI form and
`--limit` alias remain available.
