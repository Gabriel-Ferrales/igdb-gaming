PROJECT_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
ENV_FILE := $(PROJECT_ROOT)/.env

ifneq ($(wildcard $(ENV_FILE)),)
include $(ENV_FILE)
export
endif

.PHONY: help setup ingestion-install ingestion-test ingestion-lint dbt-install dbt-debug dbt-build-dev dbt-build-prod terraform-init terraform-fmt terraform-validate clean

help:
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z_-]+:.*## / {printf "%-24s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ingestion-install dbt-install ## Install all component dependencies
ingestion-install: ## Install ingestion dependencies
	cd ingestion && uv sync
ingestion-test: ## Run ingestion tests
	cd ingestion && uv run pytest
ingestion-lint: ## Lint ingestion code
	cd ingestion && uv run ruff check .
dbt-install: ## Install dbt and packages
	cd dbt && uv sync && uv run dbt deps
dbt-debug: ## Check the dev dbt connection
	cd dbt && uv run dbt debug --profiles-dir profiles --target "$${DBT_TARGET}"
dbt-build-dev: ## Build dbt models against dev
	cd dbt && uv run dbt build --profiles-dir profiles --target dev
dbt-build-prod: ## Build dbt models against prod
	cd dbt && uv run dbt build --profiles-dir profiles --target prod
terraform-init: ## Initialize Terraform without applying
	cd terraform && terraform init
terraform-fmt: ## Format Terraform recursively
	cd terraform && terraform fmt -recursive
terraform-validate: ## Validate Terraform configuration
	cd terraform && terraform validate
clean: ## Remove generated local artifacts
	cd ingestion && rm -rf .venv .pytest_cache .ruff_cache
	cd dbt && rm -rf .venv target logs dbt_packages
