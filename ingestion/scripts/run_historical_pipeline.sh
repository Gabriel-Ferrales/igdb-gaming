#!/usr/bin/env bash

set -Eeuo pipefail

IMAGE_NAME="igdb-ingestion:local"
CREDENTIALS_CONTAINER_PATH="/run/secrets/gcp-key.json"

# Excluimos genres y platforms porque ya están completos.
ENDPOINTS=(
  "companies"
  "games"
  "involved_companies"
  "release_dates"
)

TOTAL_ENDPOINTS=${#ENDPOINTS[@]}
PIPELINE_START=$(date +%s)

docker_args=(
  --rm
  --env-file ../.env
  -v "${GOOGLE_APPLICATION_CREDENTIALS}:${CREDENTIALS_CONTAINER_PATH}:ro"
  -e "GOOGLE_APPLICATION_CREDENTIALS=${CREDENTIALS_CONTAINER_PATH}"
)

format_duration() {
  local total_seconds="$1"
  printf '%02d:%02d:%02d' \
    $((total_seconds / 3600)) \
    $(((total_seconds % 3600) / 60)) \
    $((total_seconds % 60))
}

print_progress_bar() {
  local current="$1"
  local total="$2"
  local width=30
  local completed=$((current * width / total))
  local remaining=$((width - completed))

  printf '['
  printf '%*s' "$completed" '' | tr ' ' '#'
  printf '%*s' "$remaining" '' | tr ' ' '-'
  printf '] %d/%d' "$current" "$total"
}

handle_error() {
  local exit_code=$?
  local endpoint="${CURRENT_ENDPOINT:-unknown}"

  echo
  echo "ERROR: Pipeline failed while processing endpoint: ${endpoint}"
  echo "Exit code: ${exit_code}"
  exit "$exit_code"
}

trap handle_error ERR

echo "Historical extraction and loading pipeline"
echo "Docker image: ${IMAGE_NAME}"
echo "Endpoints: ${ENDPOINTS[*]}"
echo

for index in "${!ENDPOINTS[@]}"; do
  endpoint="${ENDPOINTS[$index]}"
  current=$((index + 1))
  CURRENT_ENDPOINT="$endpoint"
  endpoint_start=$(date +%s)

  echo "============================================================"
  print_progress_bar "$current" "$TOTAL_ENDPOINTS"
  echo
  echo "Endpoint: ${endpoint}"
  echo "Phase 1/2: Historical extraction"
  echo "============================================================"

  docker run \
    "${docker_args[@]}" \
    "$IMAGE_NAME" \
    igdb_pipeline.cli extract \
    --endpoint "$endpoint" \
    --page-size 500

  echo
  echo "============================================================"
  echo "Endpoint: ${endpoint}"
  echo "Phase 2/2: Load pending batches into BigQuery"
  echo "============================================================"

  docker run \
    "${docker_args[@]}" \
    "$IMAGE_NAME" \
    igdb_pipeline.load_cli run \
    --endpoint "$endpoint"

  endpoint_end=$(date +%s)
  endpoint_duration=$((endpoint_end - endpoint_start))

  echo
  echo "Completed: ${endpoint}"
  echo "Elapsed: $(format_duration "$endpoint_duration")"
  echo
done

PIPELINE_END=$(date +%s)
PIPELINE_DURATION=$((PIPELINE_END - PIPELINE_START))

echo "============================================================"
echo "Historical pipeline completed successfully"
echo "Endpoints processed: ${TOTAL_ENDPOINTS}"
echo "Total elapsed: $(format_duration "$PIPELINE_DURATION")"
echo "============================================================"