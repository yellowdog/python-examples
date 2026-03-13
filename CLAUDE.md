# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YellowDog Python Examples (`yellowdog-python-examples`) is a Python CLI tool suite for managing distributed computing jobs and resources on the YellowDog platform. It provides 21 `yd-*` commands (e.g., `yd-submit`, `yd-provision`, `yd-list`) installable as a package.

Current version: defined in `yellowdog_cli/__init__.py`.

## Commands

```bash
# Install in editable/development mode
make install          # builds then pip install -U -e .

# Format code (pyupgrade → isort → black)
make format

# Run individual formatters
make black            # black --preview on all src + tests
make isort            # isort --profile black
make pyupgrade        # pyupgrade --py310-plus

# Build distribution
make build            # python -m build

# Run tests
pytest -v                           # standard tests only
pytest -v --run-demos               # include demo integration tests
pytest -v -n 2 --run-demos          # parallel with pytest-xdist
pytest -v -k test_variable          # run a single test file/pattern

# Update dependencies
make update           # pip install -U pip -r requirements.txt -r requirements-dev.txt
```

**Note:** mypy is intentionally disabled (commented out in Makefile).

## Architecture

### Package Structure

```
yellowdog_cli/
├── __init__.py           # Version only
├── *.py                  # ~28 command modules (one per yd-* command)
└── utils/
    ├── wrapper.py        # Global CLIENT + CONFIG_COMMON; @main_wrapper decorator
    ├── args.py           # CLIParser class (single shared instance: ARGS_PARSER)
    ├── config_types.py   # Configuration dataclasses
    ├── load_config.py    # Config loading from TOML/env vars
    ├── settings.py       # Constants, env var names, Rich theme
    ├── entity_utils.py   # API entity lookups (LRU-cached search functions)
    ├── printing.py       # Rich-based output formatting
    ├── variables.py      # Variable substitution engine ({{ }})
    ├── submit_utils.py   # Work requirement construction helpers
    ├── csv_data.py       # CSV batch task processing
    └── cloudwizard_*.py  # AWS/Azure/GCP provider integration
```

### Command Pattern

Every command module follows this structure:

```python
from yellowdog_cli.utils.wrapper import main_wrapper

# Module-level config loading (runs at import time)
CONFIG_XXX = load_config_xxx()

@main_wrapper
def main():
    # Command logic using CLIENT, ARGS_PARSER, CONFIG_COMMON from wrapper
    ...

if __name__ == "__main__":
    main()
```

### Global State (wrapper.py)

`wrapper.py` initialises two module-level globals used everywhere:
- `CLIENT` — `PlatformClient` instance (YellowDog SDK)
- `CONFIG_COMMON` — loaded from `config.toml` (or `--config` arg / env vars)

`ARGS_PARSER` is a `CLIParser` instance from `args.py`, also module-level. These three are imported directly by command modules.

The `@main_wrapper` decorator handles: PAC proxy setup, exception catching (permission/auth errors), `CLIENT.close()`, and exit codes.

### Configuration

Config is loaded from (in priority order): CLI args → environment variables → TOML file. Key env vars: `YD_KEY`, `YD_SECRET`, `YD_NAMESPACE`, `YD_TAG`, `YD_URL`. Variables prefixed `YD_VAR_` are available for substitution in specs.

### Variable Substitution

Specs (TOML/JSON/Jsonnet) support `{{variable_name}}` substitution with type tags: `num:`, `bool:`, `array:`, `table:`, `format_name:`. Default values use `:=` separator. Environment variables via `env:` prefix. Up to 3 levels of nesting (`TOML_VAR_NESTED_DEPTH = 3`).

### Coding Conventions

- Python 3.10+ syntax: use `str | None` (not `Optional[str]`), `match` statements where appropriate
- Type hints on all new functions
- Constants in `settings.py` (UPPERCASE); property name constants prefixed `PROP_`, resource name constants prefixed `RN_`
- Use `print_error()`, `print_info()`, `print_warning()` from `printing.py` — never `print()` directly
- LRU cache on entity lookup functions in `entity_utils.py`
- Config dataclasses in `config_types.py`; no raw dicts for structured config

### Dependencies

- `yellowdog-sdk` — YellowDog platform API client
- `rich` (pinned 13.9.4) — terminal output formatting
- `tomli` — TOML parsing
- `python-dotenv` — `.env` file support
- `pypac` — proxy auto-configuration
- `jsonnet` — optional, for Jsonnet spec templating
- Cloud wizard extras: `boto3`, `google-cloud-*`, `azure-*`