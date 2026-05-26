# dbt Project

This directory contains the dbt Data Vault project (`banking_vault`).

## Targets

Targets are defined in the root `profiles.yml`:

- `local`: DuckDB + MinIO (default)
- `dev`: Snowflake development database
- `prod`: Snowflake production database

Set the active target via environment variable:

```bash
export DBT_TARGET=local
```

## Model Layers

- `models/staging`: source alignment and standardized staging models
- `models/vault`: Data Vault entities (hubs, links, satellites)
- `models/marts`: curated business-facing marts

## Common Commands

Run from the repository root:

```bash
uv run dbt deps --project-dir dbt --profiles-dir .
uv run dbt debug --project-dir dbt --profiles-dir .
uv run dbt run --project-dir dbt --profiles-dir .
uv run dbt test --project-dir dbt --profiles-dir .
```

Generate docs:

```bash
uv run dbt docs generate --project-dir dbt --profiles-dir .
```
