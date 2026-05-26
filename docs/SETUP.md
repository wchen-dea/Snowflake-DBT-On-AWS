# Setup Guide

## Prerequisites

- Docker Desktop
- Python 3.11+
- Terraform 1.5+
- AWS account (for cloud deployment)
- Snowflake account (for dev/prod dbt targets)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/omidsaraf/AWS_Snowflake_DBT__Project.git
cd AWS_Snowflake_DBT__Project
```

### 2. Configure Environment Variables

```bash
cp docker/.env.example .env
```

Edit `.env` and set values as needed for local or cloud targets.

### 3. Start the Local Stack

```bash
docker compose -f docker/docker-compose.yml up --build
```

Core local endpoints:

- Airflow UI: `http://localhost:8080`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- DuckDB Local UI: `http://localhost:4213`

### 4. Run dbt Locally (Optional)

```bash
cd dbt
dbt deps
dbt debug --profiles-dir ..
dbt run --profiles-dir ..
dbt test --profiles-dir ..
```

### 5. Terraform (Cloud Environments)

```bash
cd terraform/env/dev
terraform init
terraform plan
terraform apply
```

## Troubleshooting

For Docker-specific troubleshooting (including DuckDB UI), see [docker/README.md](../docker/README.md#troubleshooting).

## Additional Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [Data Vault Modeling (Overview)](https://en.wikipedia.org/wiki/Data_vault_modeling)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Snowflake dbt Setup](https://docs.getdbt.com/reference/warehouse-setups/snowflake-setup)
