# Contributing

Thanks for contributing to this project.

## Workflow

We use GitHub Flow:

1. Create a feature branch from `main`.
2. Make focused changes.
3. Run local checks.
4. Open a pull request.

## Local Checks

Run these before opening a PR:

```bash
pre-commit run --all-files
terraform validate
dbt test --selector ci
```

## Pull Requests

- Keep PRs focused and small where possible.
- Add or update docs when behavior changes.
- Include test evidence for code changes.

## Commit Style

Use clear, imperative commit messages, for example:

- `add duckdb ui service to compose`
- `fix staging model local target columns`
- `update setup docs for local workflow`
