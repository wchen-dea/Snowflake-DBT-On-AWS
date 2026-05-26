# Airflow DAGs

## Purpose

This directory contains orchestration DAGs for ingestion, processing, and modeling workflows.

## Design Principles

- Kubernetes-native execution via `KubernetesPodOperator`
- Production-ready defaults (retries, logging, alert hooks)
- Modular DAG separation by pipeline stage
- Horizontal scalability for high-volume banking workloads

## Extension Points

Add branching logic, SLA sensors, and notification integrations (for example Slack) as pipeline maturity grows.
