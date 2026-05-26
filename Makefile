# =====================================================================
# Makefile — Local Docker Compose routines for Banking Data Platform
# =====================================================================
# NOTE: All targets run on the HOST. Do not run make inside a container.
#       If you are in a container shell, type 'exit' first.
# =====================================================================

COMPOSE = docker compose -f docker/docker-compose.yml

.PHONY: help up down restart build logs logs-service ps dbt dbt-shell spark airflow clean

help:
	@echo ""
	@echo "Banking Data Platform — local dev targets"
	@echo "-----------------------------------------"
	@echo "  make up              Build + start all services (detached)"
	@echo "  make down            Stop + remove all containers"
	@echo "  make restart         down + up"
	@echo "  make build           Rebuild all images without starting"
	@echo "  make logs            Tail logs for ALL services"
	@echo "  make logs-service s= Tail logs for one service  e.g. s=airflow-scheduler"
	@echo "  make ps              List running containers"
	@echo "  make dbt             One-off dbt run (deps + run) via dbt-runner"
	@echo "  make dbt-shell       Interactive shell inside dbt-runner container"
	@echo "  make spark           Interactive shell inside spark-master container"
	@echo "  make airflow         Open Airflow UI in browser (http://localhost:8080)"
	@echo "  make clean           Remove ALL volumes — wipes DuckDB, MinIO, Postgres!"
	@echo ""

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

restart: down up

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

# Tail a single service: make logs-service s=airflow-scheduler
logs-service:
	$(COMPOSE) logs -f $(s)

ps:
	$(COMPOSE) ps

# One-off dbt run (deps + run) — exits when complete
dbt:
	$(COMPOSE) run --rm dbt-runner

# Interactive shell inside the dbt-runner container
dbt-shell:
	$(COMPOSE) run --rm --entrypoint /bin/bash dbt-runner

# Interactive shell inside spark-master (exit with 'exit' to return to host)
spark:
	$(COMPOSE) exec spark-master /bin/bash

# Open Airflow UI in browser
airflow:
	open http://localhost:8080 || xdg-open http://localhost:8080

# Remove all volumes — DANGEROUS: wipes DuckDB, MinIO, Postgres
clean:
	$(COMPOSE) down -v
