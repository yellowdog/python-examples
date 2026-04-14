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
| `test_arguments_assembly.py` | `utils/submit_utils.py` — `assemble_arguments` (argumentsPrefix + arguments + argumentsPostfix combination) |
| `test_build_dc_substitutions.py` | `utils/load_config.py` — `_build_dc_substitutions` (data client config merging and inheritance) |
| `test_environment_merge.py` | `utils/submit_utils.py` — `merge_environment` (addEnvironment merging and key-override behaviour) |
| `test_compact_json.py` | `utils/compact_json.py` — `CompactJSONEncoder` (inline vs. expanded formatting, float notation) |
| `test_csv_data.py` | `utils/csv_data.py` — `CSVTaskData`, `CSVDataCache`, substitution helpers |
| `test_dataclient_utils.py` | `utils/dataclient_utils.py` — `resolve_remote_path` (rclone remote path resolution) |
| `test_interactive.py` | `utils/interactive.py` — `confirmed` (--yes / YD_YES shortcuts), `get_selected_list_items` (range parsing: comma, dash, `*`, error recovery) |
| `test_ls_formatting.py` | `ls.py` — `_print_listing`, `_print_flat`, `_print_tree` output formatting |
| `test_misc_utils.py` | `utils/misc_utils.py` — name formatting, ID generation, delimiter parsing, etc. |
| `test_printing.py` | `utils/printing.py` — `_truncate_text`, `_yes_or_no`, `indent`, `status_counts_msg`, `get_type_name`, `print_string`; table-building helpers |
| `test_property_overrides.py` | `utils/load_config.py` — `_apply_property_overrides`, `_parse_property_value` (CLI `--property` flag) |
| `test_rclone_utils.py` | `utils/rclone_utils.py` — `parse_rclone_config` (plain remotes and inline config strings) |
| `test_resequence_resources.py` | `utils/load_resources.py` — `_resequence_resources` (creation/removal dependency ordering) |
| `test_select_dc_section.py` | `utils/load_config.py` — `_select_dc_section` (data client profile selection and merging) |
| `test_type_check.py` | `utils/type_check.py` — `check_int/float/bool/str/list/dict` |
| `test_validate_properties.py` | `utils/validate_properties.py` — `validate_properties` (key validation, deprecated and excluded keys) |
| `test_variable_processing.py` | `utils/misc_utils.py` — `split_delimited_string`, `remove_outer_delimiters` |
| `test_variable_subs.py` | `utils/variables.py` — `{{variable}}` substitution engine |
| `test_ydid_utils.py` | `utils/ydid_utils.py` — `get_ydid_type`, type constants |

### Other No-Flag Tests (no credentials needed)

| File | What it tests |
|---|---|
| `test_dryruns.py` | All standard demos in `--dry-run` mode (no platform calls); GUI starts and stays up |
| `test_entrypoints.py` | All `yd-*` CLI entry points are present and respond to `--help` |

### System Tests (`--run-system`, credentials required)

| File | What it tests |
|---|---|
| `test_system_error_handling.py` | Hard failures (exit 1) and soft failures (exit 0 + error message) for bad input, unknown YDIDs, missing resources |
| `test_system_resources.py` | Full create → list → show → remove lifecycle for keyrings, namespaces, image families, namespace policies, attributes, groups |
| `test_system_cancel_hold_finish.py` | Work Requirement control commands: hold, start, finish, cancel (WR stays PENDING — no compute provisioned) |
| `test_system_dataclient.py` | Data client commands (`yd-upload`, `yd-ls`, `yd-download`, `yd-delete`): upload/list/delete cycle, upload→download round-trip, recursive upload and listing, wildcard list and delete, dry-run enforcement for upload/download/delete |

### System Compute Tests (`--run-system-compute`, provisions real cloud instances)

| File | What it tests |
|---|---|
| `test_system_lifecycle.py` | Minimal end-to-end: provision pool → submit trivial WR → follow to completion → shutdown |
| `test_system_csv_batch.py` | CSV-driven batch: 10 tasks from `tasks.csv`, all verified complete |
| `test_system_resize.py` | Worker Pool resize: provision with 1 node, resize to 2, verify, tear down |

### Demo Tests (`--run-demos`, provisions real cloud instances)

| File | What it tests                                                  |
|---|----------------------------------------------------------------|
| `test_demos.py` | Full live runs of all standard python-examples-demos workloads |

### Other Platform Tests (no flags, but credentials required)

| File | What it tests |
|---|---|
| `test_create_remove.py` | `yd-create` / `yd-remove` round-trips for all resource types |
| `test_list.py` | `yd-list` with various resource-type filters |

## Prerequisites for Platform Tests

Set credentials in the environment or provide a `config.toml`:

```shell
export YD_KEY=...
export YD_SECRET=...
export YD_URL=...   # optional, defaults to production
```

`test_system_dataclient.py` additionally requires a `[dataClient]` section in `tests/system/config.toml` (rclone connection string and remote path).

## Parallel Execution

Unit tests and demo tests support parallel execution via `pytest-xdist`:

```shell
pytest -v -n 4                              # 4 workers, unit/dry-run tests
pytest -v -n 4 --run-demos tests/test_demos.py  # parallel demo runs (target file directly to avoid unit tests consuming workers first)
pytest -v -n 4 --run-demos tests/test_demos.py -k 'bash or primes'
```