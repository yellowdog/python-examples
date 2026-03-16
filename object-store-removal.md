# Implementation Plan: Remove Object Store + Special Task Type Treatment

## Design decisions to confirm before starting

1. **`taskType` / `taskTypes` as pass-through data** — these properties (just strings sent to the API) are separate from the *special client-side treatment* of "bash", "docker", etc. The assumption below is that `taskType` and `taskTypes` remain as neutral properties you can set in a spec, but the client no longer does anything special with their values.

2. **`yd-delete`** — currently deletes object store objects. There is no other use of that command. Remove entirely (resource removal uses `yd-remove`).

3. **`executable`** — only exists to support bash/docker special handling. Remove entirely.

4. **Data Client (`generateTaskDataObject`)** — assume this stays; only the *object store* upload path goes.

---

## Phase 1 — Delete entire files

These files have no surviving purpose:

| File | Reason |
|---|---|
| `yellowdog_cli/upload.py` | `yd-upload` command |
| `yellowdog_cli/download.py` | `yd-download` command |
| `yellowdog_cli/delete.py` | `yd-delete` command (object store objects only) |
| `yellowdog_cli/utils/upload_utils.py` | `upload_file()`, `upload_file_core()`, `unique_upload_pathname()` |
| `tests/test_objects.py` | Tests `yd-upload`, `yd-list -o`, `yd-delete` |

---

## Phase 2 — `pyproject.toml` and `requirements.txt`

**`pyproject.toml`** — remove three entry points:
```
yd-delete
yd-download
yd-upload
```

---

## Phase 3 — `utils/property_names.py`

Remove constants (and their entries in `ALL_KEYS`):

*Object store:*
`ALWAYS_UPLOAD`, `FILE_PATTERN`, `FLATTEN_PATHS`, `FLATTEN_UPLOAD_PATHS`, `INPUTS_OPTIONAL`, `INPUTS_REQUIRED`, `OUTPUTS_OPTIONAL`, `OUTPUTS_OTHER`, `OUTPUTS_REQUIRED`, `UPLOAD_FILES`, `UPLOAD_PATH`, `UPLOAD_TASKOUTPUT`, `VERIFY_AT_START`, `VERIFY_WAIT`

*Task type special treatment:*
`DOCKER_ENV`, `DOCKER_OPTIONS`, `DOCKER_PASSWORD`, `DOCKER_REGISTRY`, `DOCKER_USERNAME`, `EXECUTABLE`

Keep: `TASK_TYPE`, `TASK_TYPES` (neutral pass-through data); `LOCAL_PATH`, `TASK_DATA`, `TASK_DATA_FILE`, `TASK_DATA_INPUTS`, `TASK_DATA_OUTPUTS`, `TASK_DATA_SOURCE`, `TASK_DATA_DESTINATION` (all data client).

---

## Phase 4 — `utils/config_types.py`

Remove fields from `ConfigWorkRequirement`:

*Object store:*
`always_upload`, `flatten_input_paths`, `flatten_upload_paths`, `inputs_optional`, `inputs_required`, `outputs_optional`, `outputs_other`, `outputs_required`, `upload_files`, `upload_taskoutput`, `verify_at_start`, `verify_wait`

Keep: `task_data_inputs`, `task_data_outputs`, `task_data_file` (data client).

*Task type special treatment:*
`docker_env`, `docker_options`, `docker_password`, `docker_registry`, `docker_username`, `executable`

---

## Phase 5 — `utils/settings.py`

Remove:
- `NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR = "::"`
- `RN_STORAGE_CONFIGURATION = "NamespaceStorageConfiguration"`
- `MAX_PARALLEL_TASK_BATCH_UPLOAD_THREADS` (if `--parallel-batches` is also removed)

---

## Phase 6 — `utils/args.py`

Remove argument definitions and their property accessors:

*Object store arguments:*
- `--object-paths` / `--objects` (yd-list, yd-delete, yd-download)
- `--namespace-storage-configurations` (yd-list)
- `--all` (if only used for object listing — audit carefully)
- `--non-exact-namespace-match`, `--directory`, `--flatten`, `--pattern` (yd-download)
- `filenames`, `--flatten-upload-paths`, `--recursive`, `--batch` (yd-upload)
- Remove `"delete"` and `"download"` from the interactive mode command guard

*Task type special treatment:*
- `--executable` / `-X`

Keep: `--task-type` / `-T` (neutral pass-through, if `taskType` survives).

Also remove the suffix description strings for `delete`, `download`, and `upload` modules.

---

## Phase 7 — `utils/load_config.py`

Remove loading blocks for all deleted `ConfigWorkRequirement` fields (see Phase 4). Specifically: `executable`, all five `docker_*` fields, `always_upload`, `flatten_input_paths`, `flatten_upload_paths`, `inputs_optional`, `inputs_required`, `outputs_optional`, `outputs_other`, `outputs_required`, `upload_files`, `upload_taskoutput`, `verify_at_start`, `verify_wait`.

---

## Phase 8 — `utils/misc_utils.py`

Remove:
- `NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR` import
- `unpack_namespace_in_prefix()` — only called by the deleted upload/download/list code

---

## Phase 9 — `utils/csv_data.py`

Remove from `csv_expand_toml_tasks()`:
- All five `docker_*` property tuples
- `executable` tuple
- `always_upload`, `flatten_input_paths`, `flatten_upload_paths`, `inputs_optional`, `inputs_required` tuples
- `outputs_optional`, `outputs_other`, `outputs_required` tuples
- `upload_files`, `upload_taskoutput`, `verify_at_start`, `verify_wait` tuples

Keep: `task_data`, `task_data_file`, `task_data_inputs`, `task_data_outputs` tuples (data client).

---

## Phase 10 — `utils/submit_utils.py`

Remove entirely:
- `generate_task_input_list()`, `generate_task_input()`, `get_namespace_and_filepath()`
- `UploadedFile` and `UploadedFiles` classes (the whole upload tracking and cleanup machinery)

Remove imports: `ObjectPath`, `TaskInput`, `TaskInputVerification`, `TaskInputSource`, `NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR`, `unique_upload_pathname`, `upload_file_core`.

Keep imports: `TaskData`, `TaskDataInput`, `TaskDataOutput` (used by `generate_taskdata_object()`); `LOCAL_PATH` (used by data client path).

Keep: `update_config_work_requirement_object()`, `pause_between_batches()`, `generate_taskdata_object()`, `generate_task_error_matchers_list()`, `generate_dependencies()`.

---

## Phase 11 — `submit.py`

This is the most complex file. Work top-to-bottom:

**Imports** — remove `upload_utils`, `UploadedFiles` from `submit_utils`, object-store SDK model imports (`ObjectPath`, `TaskInput`, `TaskInputSource`, `TaskInputVerification`, `TaskOutput`), `NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR`, `MAX_PARALLEL_TASK_BATCH_UPLOAD_THREADS`. Keep `rclone_utils` import; keep `TaskData`, `TaskDataInput`, `TaskDataOutput` (data client).

**Module-level globals** — remove `UPLOADED_FILES`. Keep `RCLONE_UPLOADED_FILES`.

**`submit_work_requirement()`** — remove `UPLOADED_FILES` initialisation, `flatten_upload_paths` setup and threading. Keep `RCLONE_UPLOADED_FILES` initialisation.

**`add_tasks_to_task_group()`** — remove `flatten_upload_paths` parameter and all propagation of it.

**`generate_batch_of_tasks_for_task_group()`** — remove:
- `flatten_input_paths` setup block
- All `inputs`/`uploadFiles` object store upload logic, `TaskInput` construction, `VERIFY_AT_START`/`VERIFY_WAIT` handling
- All `outputs`/`outputsRequired`/`outputsOther`/`uploadTaskProcessOutput`/`alwaysUpload` processing
- `executable` lookup from the task/group/wr data cascade

Keep: `RCLONE_UPLOADED_FILES.upload_dataclient_input_files()` call; `generate_taskdata_object()` call; `task_data_inputs`/`task_data_outputs` lookups from task/group/wr data.

**`create_task()`** — remove:
- `flatten_upload_paths` parameter
- The `bash`/`powershell`/`python`/`cmd`/`bat` branch (executable upload + args prepend)
- The `docker` branch (docker env setup, credential injection)
- Collapse the remaining `else` block into the unconditional path
- The `if add_yd_env_vars and (task_type != "docker" or ...)` guard reduces to `if add_yd_env_vars`

**`cleanup_on_failure()`** — remove `UPLOADED_FILES.delete()`. Keep `RCLONE_UPLOADED_FILES.delete()`.

**`deduplicate_inputs()`** and **`check_for_duplicates_in_file_lists()`** — remove entirely.

**`submit_json_raw()`** — remove the `VERIFY_AT_START` warning/pause block.

---

## Phase 12 — `utils/entity_utils.py`

Remove:
- `ObjectPath`, `ObjectPathsRequest` imports
- `list_matching_object_paths()` function
- `get_non_exact_namespace_matches()` function (calls `get_namespace_storage_configurations()`)

---

## Phase 13 — `list.py`

Remove:
- `ObjectDetail` import
- `list_matching_object_paths` import
- `ARGS_PARSER.object_paths` branch in `main()`
- `ARGS_PARSER.namespace_storage_configurations` branch in `main()`
- `list_object_paths()` function
- `list_namespace_storage_configurations()` function
- The corresponding entries in `check_for_valid_option()`

---

## Phase 14 — `create.py` and `remove.py`

Remove namespace storage configuration create/remove functions and their dispatch branches in each file's `main()`.

---

## Phase 15 — Cloudwizard (`cloudwizard_aws.py`, `cloudwizard_azure.py`, `cloudwizard_gcp.py`)

Each provider's cloudwizard module creates a cloud storage bucket/container and a YellowDog namespace storage configuration to back the object store. All of that must be removed.

**`cloudwizard_aws.py`:**
- Remove `RN_STORAGE_CONFIGURATION` from `settings` import
- Remove `S3_BUCKET_NAME_PREFIX` constant (used only for bucket creation)
- Remove `_create_s3_bucket()` method (creates the S3 bucket for namespace mapping)
- Remove `_generate_yd_namespace_configuration()` method
- Remove the namespace configuration create/remove calls from the setup and teardown flows

**`cloudwizard_azure.py`:**
- Remove `RN_STORAGE_CONFIGURATION` from `settings` import
- Remove `STORAGE_BLOB_NAME` constant
- Remove `YD_CREDENTIAL_NAME_STORAGE` constant (storage-specific credential, not needed without object store)
- Remove `_create_storage_account_and_blob()` method
- Remove `_generate_yd_namespace_configuration()` method
- Remove `_generate_yd_azure_storage_credential()` method (generates credential for namespace storage config only)
- Remove the storage credential, namespace configuration create/remove calls from the setup and teardown flows

**`cloudwizard_gcp.py`:**
- Remove `RN_STORAGE_CONFIGURATION` from `settings` import
- Remove `GCP_BUCKET_PREFIX` constant
- Remove `_create_storage_bucket()` method
- Remove `_generate_namespace_configuration()` method
- Remove the namespace configuration create/remove calls from the setup and teardown flows

---

## Phase 16 — `utils/printing.py`

Remove:
- `DownloadBatchBuilder`, `UploadBatchBuilder` imports
- `object_path_table()` function
- The `ObjectPath` branch in `print_numbered_object_list()`
- `print_batch_upload_files()` function
- `print_batch_download_files()` function

---

## Phase 17 — Tests

**`tests/test_entrypoints.py`** — remove assertions for `yd-delete`, `yd-download`, `yd-upload`.

**`tests/test_demos.py`** — remove `yd-delete -y` from `CMD_SEQ` and any per-test references; remove `test_bash()`, `test_powershell()`, `test_cmd_exe()` if the demos themselves are being retired, or update them if demos are restructured to use the data client.

**`tests/test_dryruns.py`** — same: remove/update bash, powershell, cmd dry-run tests.

**`tests/test_system_resources.py`** — audit for any namespace storage configuration test (none found, but verify).

**`tests/README.md`** — update the test file table to remove `test_objects.py` entry and update demo test descriptions.

---

## Phase 18 — Documentation and config template

**`README.md`**:
- Remove `yd-delete`, `yd-download`, `yd-upload` from the commands table
- Remove the "Task Types" section entirely (bash, cmd, docker, powershell, python examples)
- Remove "Automatic Upload of Local Files" section
- Remove the `inputs`, `outputs`, `uploadFiles`, `uploadTaskProcessOutput`, `verifyAtStart`, `verifyWait`, `executable`, `alwaysUpload`, `flattenInputPaths`, `flattenUploadPaths`, `docker*` rows from the work requirement properties table

**`config-template.toml`**:
- Remove `taskType` special-value comments (bash/docker examples)
- Remove all `docker*` property comments
- Remove `executable` property comment
- Remove `inputs`/`outputs`/`uploadFiles`/`uploadTaskProcessOutput`/`verifyAtStart`/`verifyWait` comments

**`CLAUDE.md`**:
- Remove `upload_utils.py` entry from the module descriptions table
- Update descriptions for `cloudwizard_aws.py`, `cloudwizard_azure.py`, `cloudwizard_gcp.py` entries

**`PYPI_README.md`**
- Remove `yd-delete`, `yd-download`, `yd-upload` from the commands table

- **`README_CLOUDWIZARD.md`**
- Remove all mentions of storage buckets and namespace storage configurations

---

## Suggested execution order

1. Phases 1–2 (delete files, remove entry points) — eliminates dead imports immediately
2. Phases 3–5 (constants, config types, settings) — establishes the new data model
3. Phases 6–9 (args, load_config, misc_utils, csv_data) — clears peripheral plumbing
4. Phases 10–11 (submit_utils, submit) — the bulk of the logic changes
5. Phases 12–15 (entity_utils, list, create, remove, cloudwizard) — remaining command modules and cloudwizard
6. Phase 16 (printing) — remove object-store output helpers
7. Phase 17 (tests) — update test suite
8. Phase 18 (docs) — documentation cleanup

Run `pytest -v` after phases 1–2 and again after phase 11 as the two main checkpoints. Run `pytest -v --run-system` after phase 17.