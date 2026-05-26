# GitHub Workflows

This folder contains CI/CD workflow definitions for linting, tests, dbt validation, Terraform planning, and container image publishing.

## Workflow Files

- `ci.yml`: Python code quality, unit tests, and DAG validation
- `dbt-test.yml`: dbt deps/seed/run/test/docs flow
- `terraform-plan.yml`: Terraform plan/apply workflow by environment
- `docker-build.yml`: image build and push automation

## Common Secrets

Configure repository secrets in GitHub Actions settings.

### Snowflake

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_CI_USER`
- `SNOWFLAKE_CI_PASSWORD`

### AWS (if used by workflow steps)

- `AWS_ACCESS_KEY_ID_DEV`
- `AWS_SECRET_ACCESS_KEY_DEV`
- `AWS_ACCESS_KEY_ID_PROD`
- `AWS_SECRET_ACCESS_KEY_PROD`

### Optional

- `SLACK_WEBHOOK`

## Manual Trigger Examples

```bash
# Run selected workflows manually from the GitHub CLI
gh workflow run ci.yml
gh workflow run dbt-test.yml
gh workflow run terraform-plan.yml -f environment=dev
gh workflow run docker-build.yml
```

## Notes

- Branch and path filters are defined inside each workflow file.
- Keep workflow docs aligned whenever new required secrets are introduced.
