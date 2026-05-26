# GitHub Workflows

## Purpose

This directory contains CI/CD workflow definitions for validation, planning, and image build steps.

## Required Secrets

Add these in GitHub: `Settings -> Secrets and variables -> Actions`.

### AWS

- `AWS_ACCESS_KEY_ID_DEV`
- `AWS_SECRET_ACCESS_KEY_DEV`
- `AWS_ACCESS_KEY_ID_PROD`
- `AWS_SECRET_ACCESS_KEY_PROD`

### Snowflake

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER_DEV`
- `SNOWFLAKE_PASSWORD_DEV`
- `SNOWFLAKE_USER_PROD`
- `SNOWFLAKE_PASSWORD_PROD`
- `SNOWFLAKE_CI_USER`
- `SNOWFLAKE_CI_PASSWORD`

### Optional

- `SLACK_WEBHOOK` (notifications)

## Usage

### Run CI pipeline

```bash
# Automatically runs on push/PR to main or develop
git push origin develop
```

### Run Terraform plan manually

```bash
gh workflow run terraform-plan.yml -f environment=dev
```

### Run Terraform apply manually

```bash
# Production apply should still follow approval controls in workflow design
gh workflow run terraform-plan.yml -f environment=prod
```

### Build Docker images manually

```bash
gh workflow run docker-build.yml
```
