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

## Loading existing GCS batches

The loader discovers completed `raw/**/manifest.json` batches, converts their
JSON arrays to validated NDJSON under `load_ready/`, loads a reusable staging
table, and merges one current row per ID into `gaming_raw`. It never modifies
the source objects.

Previewing is read-only (including BigQuery and GCS):

```bash
uv run python -m igdb_pipeline.load_cli run --endpoint games --max-batches 1 --dry-run
```

Load one batch, or inspect all manifests without registering them:

```bash
uv run python -m igdb_pipeline.load_cli run --endpoint games --max-batches 1
uv run python -m igdb_pipeline.load_cli discover
```

Use `--retry-failed` to select failed registry entries. `--batch-id` targets a
specific recovery batch. `--skip-conversion` is accepted only when an existing
conversion manifest and all of its files pass validation.

```mermaid
flowchart TD
    classDef source fill:#F9AB00,stroke:#333,stroke-width:1px,color:#000;
    classDef gcs fill:#4285F4,stroke:#333,stroke-width:1px,color:#fff;
    classDef bq fill:#EA4335,stroke:#333,stroke-width:1px,color:#fff;
    classDef process fill:#34A853,stroke:#333,stroke-width:1px,color:#fff;
    classDef decision fill:#FBBC04,stroke:#333,stroke-width:1px,color:#000;
    classDef cli fill:#9334E6,stroke:#333,stroke-width:1px,color:#fff;
    classDef future fill:#9AA0A6,stroke:#333,stroke-width:1px,color:#fff;

    subgraph Phase1["Fase 1: Extracción"]
        A["IGDB API"]:::source
        B["Extractor paginado<br/>igdb_pipeline.cli"]:::process
        C[("GCS<br/>raw/{endpoint}/.../batch_id={id}/")]:::gcs
        CM["manifest.json<br/>Commit marker del batch"]:::gcs

        A -->|"HTTP POST"| B
        B -->|"JSON array por página"| C
        B -->|"status = completed"| CM
    end

    subgraph Phase2["Fase 2: Descubrimiento y selección"]
        CLI["CLI manual o programada<br/>igdb_pipeline.load_cli"]:::cli
        D["Batch Discovery<br/>Busca manifest.json"]:::process
        E["Validación del manifest<br/>y archivos fuente"]:::process
        F{¿Batch elegible?}:::decision
        R[("BigQuery<br/>gaming_raw.ingestion_batches")]:::bq

        CLI -->|"discover / run"| D
        CM --> D
        D --> E
        E --> F
        R -->|"Consulta estado previo"| F
        F -->|"No: incomplete, loaded<br/>o no seleccionado"| SKIP["Ignorar batch"]:::process
        F -->|"Sí: nuevo, converted<br/>o retry-failed"| R
    end

    subgraph Phase3["Fase 3: Conversión"]
        G["Conversor JSON array → NDJSON<br/>Procesa un objeto de GCS a la vez"]:::process
        H[("GCS<br/>load_ready/{endpoint}/.../batch_id={id}/")]:::gcs
        CH["conversion_manifest.json"]:::gcs

        R -->|"status = converting"| G
        C -->|"Lee archivos raw sin modificarlos"| G
        G -->|"Escribe archivos .ndjson"| H
        G -->|"Conteos y metadata de conversión"| CH
        CH -->|"status = converted"| R
    end

    subgraph Phase4["Fase 4: Carga y validación"]
        I["BigQuery Load Job"]:::process
        S[("BigQuery<br/>gaming_raw.stg_{endpoint}")]:::bq
        V{¿Validaciones correctas?}:::decision
        L["MERGE por id"]:::process
        M[("BigQuery<br/>gaming_raw.{endpoint}<br/>Estado actual por ID")]:::bq
        FAIL["Registrar error<br/>status = failed"]:::process

        H -->|"NDJSON del batch"| I
        R -->|"status = loading"| I
        I -->|"WRITE_TRUNCATE"| S
        S -->|"Conteo, IDs nulos,<br/>duplicados, min y max"| V
        V -->|"Sí"| L
        L --> M
        M -->|"status = loaded<br/>y métricas finales"| R
        V -->|"No"| FAIL
        I -->|"Error de carga"| FAIL
        G -->|"Error de conversión"| FAIL
        FAIL --> R
    end

    subgraph Phase5["Fase 5: Transformación analítica"]
        DBT["dbt<br/>Modelos staging, intermedios y marts"]:::future
        M -.->|"Siguiente fase"| DBT
    end
``` 

### 💡 Puntos clave reflejados en el flujo:
* raw/ es la zona original e inmutable.
* manifest.json determina si un batch es procesable.
* ingestion_batches controla estados, reintentos e idempotencia.
* load_ready/ contiene los archivos NDJSON compatibles con BigQuery.
* stg_* es temporal y se sobrescribe por batch.
* gaming_raw.* conserva una fila actual por id.
* dbt realizará después el modelado analítico y el UNNEST de relaciones.