# dbt Project

## Purpose

This directory contains the dbt project implementing Data Vault 2.0 modeling for banking data.

## Modeling Approach

- Data Vault 2.0 layers: Hubs, Links, Satellites
- Staging layer to standardize/hash source data before vault loading
- Snowflake-oriented materializations (views for staging, incremental/table patterns for vault/marts)
- Airflow-friendly orchestration via dedicated dbt DAGs

## Project Structure

```text
dbt/
├── dbt_project.yml
├── packages.yml
├── selectors.yml
├── macros/
├── models/
│   ├── staging/
│   ├── vault/
│   │   ├── hubs/
│   │   ├── links/
│   │   └── satellites/
│   └── marts/
└── tests/
```

## Local Run Example

```bash
# Run dbt from repository root while using root-level profiles.yml
dbt run --project-dir dbt --profiles-dir .
```
