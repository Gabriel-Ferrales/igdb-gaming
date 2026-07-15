Roadmap del proyecto IGDB Gaming Analytics
Fase 0 — Preparación del repositorio ✅
 Crear repositorio igdb-gaming-analytics
 Inicializar Git
 Crear estructura principal:
 terraform/
 ingestion/
 dbt/
 kestra/
 notebooks/
 sql/
 docs/
 dashboards/
 Crear .gitignore
 Crear .env.example
 Crear Makefile
 Inicializar entornos con uv
 Configurar dbt Core con BigQuery
 Crear proyecto de GCP
 Crear cuenta de servicio y credencial JSON
 Guardar la credencial fuera del repositorio
 Configurar variables de entorno
 Crear primer commit
Fase 1 — Infraestructura con Terraform ✅
Recursos creados
 Habilitar APIs necesarias:
 BigQuery
 Cloud Storage
 IAM
 Service Usage
 Cloud Resource Manager
 Crear bucket:
playground-a68cb-igdb-gaming-analytics
 Activar:
 bloqueo de acceso público
 acceso uniforme mediante IAM
 versionado
 eliminación automática después de 365 días
 Crear datasets:
 gaming_raw
 gaming_dev
 gaming_prod
 Asignar permisos a la cuenta de servicio:
 BigQuery Job User
 BigQuery Data Editor
 Storage Object Admin
 Validar con:
terraform plan
 Confirmar:
No changes. Your infrastructure matches the configuration.
Fase 2 — Configuración de la API de IGDB

Esta es la siguiente etapa inmediata.

2.1 Crear aplicación en Twitch

IGDB usa autenticación de Twitch.

 Crear una aplicación en Twitch Developer Console
 Obtener:
 TWITCH_CLIENT_ID
 TWITCH_CLIENT_SECRET
 Guardarlos en el archivo .env
 Confirmar que .env está ignorado por Git

Ejemplo:

TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
2.2 Probar autenticación
 Crear una función para solicitar un access token
 Validar que el token funcione
 Registrar el tiempo de expiración
 No guardar el token en Git

Archivo sugerido:

ingestion/src/igdb_pipeline/auth.py

Resultado esperado:

Access token obtained successfully
Expires in: ...
Fase 3 — Exploración inicial de la API

Antes de construir el pipeline completo, conviene entender bien los datos.

3.1 Crear notebook de exploración

Archivo:

notebooks/01_api_exploration.ipynb

Explorar inicialmente:

 endpoint games
 endpoint platforms
 endpoint genres
 endpoint companies
 endpoint release_dates
3.2 Revisar estructura
 campos disponibles
 campos opcionales
 arrays
 objetos anidados
 IDs relacionados
 valores nulos
 paginación
 límites de registros por llamada
 campos created_at
 campos updated_at
3.3 Definir primera versión del alcance

Para no hacerlo demasiado grande, empezaría con:

games
platforms
genres
release_dates
companies

Y dejaría para después:

covers
screenshots
videos
websites
keywords
themes
age_ratings
Fase 4 — Construir la ingesta en Python

Aquí empezará el pipeline real.

4.1 Configuración

Archivo:

ingestion/src/igdb_pipeline/config.py

Responsabilidades:

 leer .env
 validar variables requeridas
 exponer:
 TWITCH_CLIENT_ID
 TWITCH_CLIENT_SECRET
 GCP_PROJECT_ID
 GCS_BUCKET_NAME
 GOOGLE_APPLICATION_CREDENTIALS
 BQ_RAW_DATASET
4.2 Autenticación

Archivo:

ingestion/src/igdb_pipeline/auth.py

Responsabilidades:

 solicitar token OAuth
 controlar errores
 devolver token válido
 preparar renovación futura
4.3 Cliente IGDB

Archivo:

ingestion/src/igdb_pipeline/client.py

Responsabilidades:

 construir requests
 agregar headers
 enviar consultas
 controlar errores HTTP
 manejar timeouts
 implementar retries con tenacity
 respetar rate limits
4.4 Paginación

Archivo:

ingestion/src/igdb_pipeline/pagination.py

Responsabilidades:

 usar limit
 usar offset
 continuar hasta que no lleguen más registros
 evitar duplicados
 registrar número de páginas y filas
4.5 Extracción

Archivo:

ingestion/src/igdb_pipeline/extract.py

Responsabilidades:

 extraer un endpoint completo
 guardar los resultados como JSON
 agregar metadatos:
 extracted_at
 endpoint
 record_count
 pipeline_run_id
 offset
 source_updated_at
4.6 Subida a GCS

Archivo:

ingestion/src/igdb_pipeline/storage.py

Responsabilidades:

 conectarse al bucket
 subir JSON
 usar rutas organizadas por fecha
 verificar que el objeto se haya creado
 evitar sobrescrituras accidentales

Estructura recomendada:

raw/games/extraction_date=2026-07-10/games_0001.json
raw/platforms/extraction_date=2026-07-10/platforms_0001.json
raw/genres/extraction_date=2026-07-10/genres_0001.json
raw/companies/extraction_date=2026-07-10/companies_0001.json
raw/release_dates/extraction_date=2026-07-10/release_dates_0001.json
4.7 CLI o pipeline.py

Puedes usar:

ingestion/src/igdb_pipeline/cli.py

o crear:

ingestion/pipeline.py

Yo usaría cli.py como punto de entrada y dejaría la lógica repartida en módulos.

Flujo:

Cargar configuración
→ obtener token
→ consultar endpoint
→ paginar
→ guardar JSON local temporal
→ subir a GCS
→ imprimir resumen

Ejemplo esperado:

cd ingestion
uv run python -m igdb_pipeline.cli --endpoint games
Fase 5 — Pruebas de la ingesta

Antes de cargar miles de registros:

 probar con 10 registros
 probar con una sola página
 probar credenciales inválidas
 probar timeout
 probar respuesta vacía
 probar error 429
 probar subida a GCS

Pruebas:

ingestion/tests/test_client.py
ingestion/tests/test_pagination.py
ingestion/tests/test_storage.py

Comando:

make ingestion-test

Lint:

make ingestion-lint
Fase 6 — Primera carga histórica a GCS
Objetivo inicial

No intentes cargar todo IGDB de inmediato.

Primera meta:

 extraer 5,000 juegos
 extraer plataformas
 extraer géneros
 extraer compañías relacionadas
 extraer fechas de lanzamiento
 subir todo al bucket

Después verifica manualmente:

GCS
└── raw/
    ├── games/
    ├── platforms/
    ├── genres/
    ├── companies/
    └── release_dates/
Validaciones
 número de archivos
 número de registros
 archivos JSON válidos
 tamaño total
 fechas correctas
 ausencia de credenciales dentro de los archivos
Fase 7 — Carga raw hacia BigQuery

Hay dos caminos posibles.

Camino recomendado inicialmente

Python carga directamente a BigQuery después de subir a GCS.

Flujo:

IGDB
→ Python
→ GCS
→ BigQuery gaming_raw

Tablas iniciales:

gaming_raw.games
gaming_raw.platforms
gaming_raw.genres
gaming_raw.companies
gaming_raw.release_dates
Tareas
 definir esquema raw
 decidir entre:
 JSON nativo
 columnas tipadas
 agregar columnas de auditoría:
 ingested_at
 source_file
 pipeline_run_id
 cargar archivos desde GCS
 verificar conteos
 verificar duplicados

Para la primera versión, conservaría la mayor cantidad posible de la estructura original.

Fase 8 — Análisis exploratorio de datos

Notebook:

notebooks/02_data_quality.ipynb

Revisar:

 cantidad de juegos
 IDs únicos
 IDs duplicados
 porcentaje de nulos
 distribución de ratings
 distribución de fechas
 plataformas más comunes
 géneros más comunes
 registros sin relaciones
 datos fuera de rango

Resultados de esta etapa:

 reglas de calidad
 esquema dimensional definitivo
 campos que deben conservarse
 campos descartables
 estrategia incremental
Fase 9 — Modelado con dbt
9.1 Configurar sources

Crear:

dbt/models/staging/sources.yml

Fuentes:

sources:
  - name: igdb_raw
    schema: gaming_raw

Tablas:

 games
 platforms
 genres
 companies
 release_dates
9.2 Staging

Crear:

stg_igdb_games.sql
stg_igdb_platforms.sql
stg_igdb_genres.sql
stg_igdb_companies.sql
stg_igdb_release_dates.sql

Responsabilidades:

 renombrar columnas
 convertir timestamps
 normalizar booleanos
 limpiar strings
 preservar IDs
 eliminar columnas inútiles
 agregar tests básicos
9.3 Intermediate

Crear:

int_game_platforms.sql
int_game_genres.sql
int_game_companies.sql
int_game_releases.sql

Responsabilidades:

 desanidar arrays
 resolver relaciones muchos-a-muchos
 preparar tablas puente
 unir nombres y IDs
9.4 Marts

Crear:

dim_games.sql
dim_platforms.sql
dim_genres.sql
dim_companies.sql

bridge_game_platforms.sql
bridge_game_genres.sql
bridge_game_companies.sql

fct_game_releases.sql
fct_game_ratings.sql
9.5 Tests
 unique
 not_null
 relationships
 accepted_values
 rating entre 0 y 100
 fechas válidas
 IDs positivos
 conteos no negativos

Comandos:

make dbt-debug
make dbt-build-dev
make dbt-build-prod
Fase 10 — Carga incremental

Cuando la carga histórica funcione:

 usar updated_at de IGDB
 guardar fecha máxima procesada
 consultar solo registros modificados
 evitar duplicados
 implementar MERGE en BigQuery
 agregar backfill por rango de fechas
 conservar trazabilidad por ejecución

Flujo:

last_successful_updated_at
→ consultar IGDB
→ subir nuevos archivos
→ merge en gaming_raw
→ dbt build
Fase 11 — Historial de ratings

Para analizar cómo cambian las calificaciones:

 extraer ratings diariamente o semanalmente
 guardar:
 game_id
 rating
 rating_count
 aggregated_rating
 aggregated_rating_count
 observed_at
 crear snapshot dbt o tabla histórica
 calcular:
 rating inicial
 rating actual
 variación
 días desde lanzamiento
Fase 12 — Orquestación con Kestra

Cuando el pipeline manual funcione de principio a fin:

Flujos
kestra/flows/historical_backfill.yml
kestra/flows/incremental_ingestion.yml
kestra/flows/dbt_build.yml
DAG esperado
Start
→ validate environment
→ obtain Twitch token
→ extract IGDB endpoints
→ upload to GCS
→ load gaming_raw
→ run dbt build
→ run tests
→ publish execution summary
Funcionalidades
 schedule
 retries
 timeout
 concurrency limit
 backfill
 logs
 alertas por error
Fase 13 — Dashboard

Conectar gaming_prod a Looker Studio o Power BI.

Visualizaciones:

 lanzamientos por mes
 lanzamientos por plataforma
 géneros más comunes
 compañías con más lanzamientos
 rating promedio por plataforma
 evolución de ratings
 juegos multiplataforma
 diferencia entre fechas de lanzamiento por plataforma
Fase 14 — Documentación y portafolio
 diagrama de arquitectura
 README completo
 instrucciones de ejecución
 diccionario de datos
 screenshots
 DAG de dbt
 capturas de Kestra
 capturas de BigQuery
 dashboard final
 explicación de decisiones técnicas
 costos estimados
 limitaciones conocidas
Fase 15 — CI/CD

Después de tener una versión funcional:

 GitHub Actions
 ruff check
 pytest
 terraform fmt
 terraform validate
 dbt parse
 dbt test
 Workload Identity Federation
 evitar llaves JSON en GitHub