# Infrastructure

This directory stores deployment descriptors and environment runtime manifests.

For a high-level architecture diagram and component map, see [../docs/architecture.md](../docs/architecture.md).

## Contents

- `K8S/airflow-deployment.yaml`
- `K8S/spark-job.yaml`
- `K8S/dbt-runner.yaml`

## Purpose

- Define Kubernetes workload deployment artifacts for pipeline components.
- Keep runtime deployment specs separate from Terraform provisioning code.
- Support environment promotion with explicit manifest versioning.

## Related Paths

- Terraform IaC: `terraform/`
- Local stack Compose: `docker/docker-compose.yml`
