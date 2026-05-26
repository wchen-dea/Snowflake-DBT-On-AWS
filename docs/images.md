# Documentation Images

## Recommended Image Assets

### architecture_diagram.png

High-level end-to-end architecture diagram showing:

- data sources
- Bronze/Silver/Gold layers
- Data Vault and analytics outputs
- core platform services (AWS, Spark, Airflow, dbt, Snowflake, Docker, K8s)

### airflow_dag_overview.png

Visual DAG flow for onboarding and runbook usage, for example:

- `ingestion_dag.py` -> `processing_dag.py` -> `dbt_dag.py`
- task dependencies and execution order

### dbt_data_vault_flow.png

Data Vault flow illustration covering:

- staging models
- hubs
- links
- satellites

### sample_data_preview.png

Screenshot preview of sample CSVs (`customers.csv`, `accounts.csv`, `transactions.csv`) to communicate column names and relationships quickly.

## Notes

- Store documentation images under `docs/images/`.
- Use repository-relative Markdown paths from the README, for example `docs/images/<file>.png`.
- Extend this set with ERDs, dashboard screenshots, and monitoring views as the platform evolves.
