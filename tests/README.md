# Tests

Tests are run using [pytest](https://docs.pytest.org/).

## Test Categories

Three categories of test exist, controlled by pytest flags:

| Flag | Marker | Description |
|---|---|---|
| *(none)* | — | Unit tests and dry-run tests; no platform connectivity required |
| `--run-demos` | `demos` | Full live demo runs on the platform |
| `--run-system` | `system` | System tests (resource CRUD, error handling, WR control); requires credentials |
| `--run-system-compute` | `system_compute` | System tests that provision real cloud compute (implies `--run-system`) |

## Quick Reference

```shell
# Unit and dry-run tests only (no credentials needed)
pytest -v

# Add system tests (credentials required)
pytest -v --run-system

# Add compute-provisioning tests (slow, costs money)
pytest -v --run-system-compute

# Add live demos
pytest -v --run-demos

# Everything
pytest -v --run-system-compute --run-demos

# Run a single file or pattern
pytest -v tests/test_ydid_utils.py
pytest -v -k test_variable

# Parallel execution
pytest -v -n 4 --run-demos
```

## Test Files

### Unit Tests (no flags required, no credentials needed)

| File | What it tests |
|---|---|
| `test_csv_data.py` | `utils/csv_data.py` — `CSVTaskData`, `CSVDataCache`, substitution helpers |
| `test_misc_utils.py` | `utils/misc_utils.py` — name formatting, ID generation, delimiter parsing, etc. |
| `test_type_check.py` | `utils/type_check.py` — `check_int/float/bool/str/list/dict` |
| `test_variable_processing.py` | `utils/misc_utils.py` — `split_delimited_string`, `remove_outer_delimiters` |
| `test_variable_subs.py` | `utils/variables.py` — `{{variable}}` substitution engine |
| `test_ydid_utils.py` | `utils/ydid_utils.py` — `get_ydid_type`, `is_valid_ydid`, type constants |

### Other No-Flag Tests (no credentials needed)

| File | What it tests |
|---|---|
| `test_dryruns.py` | All standard demos in `--dry-run` mode (no platform calls) |
| `test_entrypoints.py` | All `yd-*` CLI entry points are present and respond to `--help` |
| `test_gui.py` | GUI interface starts without error |

### System Tests (`--run-system`, credentials required)

| File | What it tests |
|---|---|
| `test_system_error_handling.py` | Hard failures (exit 1) and soft failures (exit 0 + error message) for bad input, unknown YDIDs, missing resources |
| `test_system_resources.py` | Full create → list → show → remove lifecycle for keyrings, namespaces, image families, namespace policies, attributes, groups |
| `test_system_cancel_hold_finish.py` | Work Requirement control commands: hold, start, finish, cancel (WR stays PENDING — no compute provisioned) |

### System Compute Tests (`--run-system-compute`, provisions real cloud instances)

| File | What it tests |
|---|---|
| `test_system_lifecycle.py` | Minimal end-to-end: provision pool → submit trivial WR → follow to completion → shutdown |
| `test_system_csv_batch.py` | CSV-driven batch: 10 tasks from `tasks.csv`, all verified complete |
| `test_system_resize.py` | Worker Pool resize: provision with 1 node, resize to 2, verify, tear down |

### Demo Tests (`--run-demos`, provisions real cloud instances)

| File | What it tests |
|---|---|
| `test_demos.py` | Full live runs of all standard demo workloads (bash, primes, image montage, OpenFOAM, Slurm, Blender, Monte Carlo, Nextflow, etc.) |

### Other Platform Tests (no flags, but credentials required)

| File | What it tests |
|---|---|
| `test_create_remove.py` | `yd-create` / `yd-remove` round-trips for all resource types |
| `test_list.py` | `yd-list` with various resource-type filters |
| `test_objects.py` | Object store upload and delete via `yd-upload` / `yd-delete` |

## Prerequisites for Platform Tests

Set credentials in the environment or provide a `config.toml`:

```shell
export YD_KEY=...
export YD_SECRET=...
export YD_URL=...   # optional, defaults to production
```

## Parallel Execution

Unit tests and demo tests support parallel execution via `pytest-xdist`:

```shell
pytest -v -n 4                     # 4 workers, unit/dry-run tests
pytest -v -n 4 --run-demos         # parallel demo runs
pytest -v -n 4 --run-demos -k 'bash or primes'
```