# Documentation Images

Use this file as a checklist for visual assets referenced by docs.

For a high-level architecture diagram and component map, see [architecture.md](architecture.md).

## Recommended Assets

### `architecture_diagram.png`

Show end-to-end flow across:

- sample/raw sources
- MinIO Bronze/Silver/Gold movement
- Spark processing jobs
- Airflow DAG orchestration
- dbt Data Vault and marts
- Snowflake targets for cloud mode

### `airflow_dag_overview.png`

Include DAG IDs and execution sequence:

- `s3_to_snowflake_ingest`
- `banking_processing_dag`
- `dbt_datavault_dag`

### `dbt_data_vault_flow.png`

Show layer progression:

- staging
- hubs
- links
- satellites
- marts

### `sample_data_preview.png`

Show key sample files:

- `spark_jobs/data/raw/customers.csv`
- `spark_jobs/data/raw/accounts.csv`
- `spark_jobs/data/raw/transactions.csv`

## Storage Convention

- Keep image files under `docs/images/`.
- Use relative links, for example `docs/images/architecture_diagram.png`.
