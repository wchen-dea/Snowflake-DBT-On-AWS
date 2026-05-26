# Raw Sample Data

Synthetic CSV seed data used by local ingestion and transformation flows.

## Files

- `customers.csv`
- `accounts.csv`
- `transactions.csv`

## Usage

- `minio-init` in `docker/docker-compose.yml` copies these files into MinIO bucket paths.
- Spark jobs consume these files through S3-compatible URIs.
- The dataset is intentionally non-sensitive and small for local development.

## Maintenance

- Preserve key relationships across customer/account/transaction records.
- Update downstream Spark and dbt logic when columns are changed.
