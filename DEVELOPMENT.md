# Development Guide

## Prerequisites

- Python 3.10 or later
- Git
- [pipx](https://pipx.pypa.io/) or [uv](https://docs.astral.sh/uv/) recommended for managing tool installs

## Getting Started

```shell
git clone https://github.com/yellowdog/yellowdog-cli
cd yellowdog-cli
git checkout next-version

# Install in editable mode with all dev dependencies
pip install -e ".[dev,jsonnet,cloudwizard]"
```

This installs the package in editable mode, making all `yd-*` commands available in your environment and reflecting any local code changes immediately.

To update all dependencies to their latest versions:

```shell
make update
```

## Code Formatting

All formatting is handled by [ruff](https://docs.astral.sh/ruff/):

```shell
make format
```

This runs `ruff check --fix` (import sorting, pyupgrade, unused imports) followed by `ruff format` (Black-compatible formatting). Always run before committing. Ruff is configured in `pyproject.toml` under `[tool.ruff]`.

## Testing

Unit tests require no credentials and no network access:

```shell
pytest -v
```

See [`tests/README.md`](tests/README.md) for the full test matrix — including dry-run, system, compute, and demo test categories, credentials setup, and parallel execution options.

## Building

```shell
make build        # builds the distribution into dist/
make pypi_check   # checks the distribution with twine
```

## Project Structure

```
yellowdog_cli/          # One module per yd-* command
yellowdog_cli/utils/    # Shared utilities (config, variables, printing, SDK wrappers, etc.)
tests/                  # All tests (see tests/README.md)
pyproject.toml          # Package metadata, dependencies, ruff config
Makefile                # format, build, install, update, toc, pypi targets
config-template.toml    # Annotated template for all TOML configuration properties
RELEASING.md            # Branch model, release process, PyPI credentials
```

For a detailed description of the architecture and coding conventions, see [`CLAUDE.md`](CLAUDE.md).

## Branching

| Branch         | Purpose                                                            |
|----------------|--------------------------------------------------------------------|
| `main`         | Current released version — always matches PyPI                     |
| `next-version` | Ongoing development                                                |
| `feature/*`    | Larger features; branch from `next-version`, merge back when ready |

Day-to-day work goes on `next-version`. See [`RELEASING.md`](RELEASING.md) for the full release process.
