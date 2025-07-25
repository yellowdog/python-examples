"""
Utility functions for use with the submit command.
"""

from dataclasses import dataclass
from glob import glob
from os import chdir, getcwd
from os.path import exists
from time import sleep
from typing import Dict, List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ObjectPath,
    TaskData,
    TaskDataInput,
    TaskDataOutput,
    TaskErrorMatcher,
    TaskInput,
    TaskInputVerification,
    TaskStatus,
)

from yellowdog_cli.utils.config_types import ConfigCommon, ConfigWorkRequirement
from yellowdog_cli.utils.printing import print_error, print_log
from yellowdog_cli.utils.property_names import (
    ERROR_TYPES,
    PROCESS_EXIT_CODES,
    RETRYABLE_ERRORS,
    STATUSES_AT_FAILURE,
)
from yellowdog_cli.utils.settings import NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR
from yellowdog_cli.utils.type_check import check_list
from yellowdog_cli.utils.upload_utils import unique_upload_pathname, upload_file_core
from yellowdog_cli.utils.variables import process_variable_substitutions_insitu
from yellowdog_cli.utils.wrapper import ARGS_PARSER


def generate_task_input_list(
    files: List[str],
    verification: Optional[TaskInputVerification],
    wr_name: Optional[str],
) -> List[TaskInput]:
    """
    Generate a TaskInput list.
    """
    task_input_list: List[TaskInput] = []
    for file in files:
        task_input_list.append(generate_task_input(file, verification, wr_name))
    return task_input_list


def generate_task_input(
    file: str, verification: Optional[TaskInputVerification], wr_name: str
) -> TaskInput:
    """
    Generate a TaskInput, accommodating files located relative to the root of
    the namespace, relative to the root of a different namespace,
    and relative to the directory specific to this Work Requirement.
    """
    namespace, filepath = get_namespace_and_filepath(file, wr_name)
    filepath = filepath.lstrip("/")
    if namespace is None:
        return TaskInput.from_task_namespace(
            object_name_pattern=filepath, verification=verification
        )
    else:
        return TaskInput.from_namespace(
            namespace=namespace, object_name_pattern=filepath, verification=verification
        )


def get_namespace_and_filepath(
    file: str, wr_name: Optional[str] = None
) -> (Optional[str], str):
    """
    Find the namespace and path, using the namespace separator.
    """
    try:
        file_parts = file.split(NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR)

        if len(file_parts) == 1:
            # Use the Work Requirement ID, if supplied, as the directory
            # within the current namespace
            if wr_name is not None:
                return None, f"{wr_name}/{file_parts[0]}"
            else:
                return None, file_parts[0]

        if len(file_parts) == 2:
            # Start at the root of the current namespace
            if file_parts[0] == "":
                return None, file_parts[1]

            # Start at the root of a different namespace
            elif len(file_parts[0]) > 0:
                return file_parts[0], file_parts[1]

        raise Exception

    except:
        raise Exception(f"Malformed file specification: '{file}'")


@dataclass
class UploadedFile:
    local_file_path: str
    upload_namespace: str
    uploaded_file_path: str


class UploadedFiles:
    """
    Upload and manage uploaded files from the 'inputs' and
    'uploadFiles' lists.
    """

    def __init__(
        self,
        client: PlatformClient,
        wr_name: str,
        config: ConfigCommon,
        files_directory: str = "",
    ):
        self._client = client
        self._wr_name = wr_name
        self._config = config
        self._uploaded_files: List[UploadedFile] = []
        self.files_directory = files_directory
        self.working_directory = getcwd()

    def add_upload_file(self, upload_file: str, upload_path: str):
        """
        Upload a file if it hasn't already been uploaded to the same location.
        Handle wildcards.
        """

        if self.files_directory != "":
            chdir(self.files_directory)

        # Handle wildcard expansion
        expanded_files = glob(pathname=upload_file, recursive=True)
        if len(expanded_files) > 1:
            if not upload_path.endswith("*"):
                raise Exception(
                    "'uploadPath' must end in '*' when using 'uploadFiles' wildcards"
                )

        for upload_file in expanded_files:
            if not exists(upload_file):
                print_error(f"File '{upload_file}' does not exist")
                continue

            namespace, uploaded_file_path = get_namespace_and_filepath(
                upload_path, self._wr_name
            )
            namespace = self._config.namespace if namespace is None else namespace

            # Adjust upload file path for a wildcard upload
            if "*" in uploaded_file_path:
                uploaded_file_path = uploaded_file_path.replace(
                    "*", upload_file.split("/")[-1]
                )

            uploaded_file_path = uploaded_file_path.lstrip("/")

            duplicate = False
            for uploaded_file in self._uploaded_files:
                if (
                    upload_file == uploaded_file.local_file_path
                    and uploaded_file_path == uploaded_file.uploaded_file_path
                    and namespace == uploaded_file.upload_namespace
                ):
                    duplicate = True
                    break
            if duplicate:
                continue

            if not ARGS_PARSER.dry_run:
                upload_file_core(
                    client=self._client,
                    url=self._config.url,
                    local_file=upload_file,
                    namespace=namespace,
                    remote_file=uploaded_file_path,
                )
            else:
                print_log(
                    f"Dry-run: Would upload '{upload_file}' to"
                    f" '{namespace}{NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR}{uploaded_file_path}'"
                )

            self._uploaded_files.append(
                UploadedFile(
                    local_file_path=upload_file,
                    upload_namespace=namespace,
                    uploaded_file_path=uploaded_file_path,
                )
            )

        chdir(self.working_directory)

    def add_input_file(self, filename: str, flatten_upload_paths: bool) -> List[str]:
        """
        Add a filename from the inputs list, processing wildcards if present.
        Return the expanded list of filenames.
        """

        # Expand wildcards ... in the correct directory
        if self.files_directory != "":
            chdir(self.files_directory)

        expanded_files = glob(pathname=filename, recursive=True)

        if len(expanded_files) == 0:
            raise Exception(f"File or files '{filename}' not found")

        chdir(self.working_directory)

        for filename in expanded_files:
            # Apply Work Requirement name prefix, etc.
            upload_file_name = unique_upload_pathname(
                filename=filename,
                id=self._wr_name,
                inputs_folder_name=None,
                urlencode_forward_slash=False,
                flatten_upload_paths=flatten_upload_paths,
            )
            # Force 'uploaded_file_name' to be at the root of the namespace
            self.add_upload_file(
                filename, f"{NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR}{upload_file_name}"
            )

        return expanded_files

    def delete(self):
        """
        Delete all files that have been uploaded.
        """
        for namespace in {uf.upload_namespace for uf in self._uploaded_files}:
            object_paths = [
                ObjectPath(uf.uploaded_file_path)
                for uf in self._uploaded_files
                if uf.upload_namespace == namespace
            ]
            print_log(
                f"Deleting {len(object_paths)} uploaded object(s) in "
                f"namespace '{namespace}'"
            )
            try:
                self._client.object_store_client.delete_objects(namespace, object_paths)
            except:
                print_error(
                    "Failed to delete one or more objects "
                    "(may already have been deleted)"
                )
        self._uploaded_files = []


def update_config_work_requirement_object(
    config_wr: ConfigWorkRequirement,
) -> ConfigWorkRequirement:
    """
    Update a ConfigWorkRequirement Object using the current
    variable substitutions. Returns the updated object.
    """
    config_wr_dict = config_wr.__dict__
    process_variable_substitutions_insitu(config_wr_dict)
    return ConfigWorkRequirement(**config_wr_dict)


def pause_between_batches(task_batch_size: int, batch_number: int, num_tasks: int):
    """
    Process a pause between Task batches.
    """
    if ARGS_PARSER.pause_between_batches is None:
        return

    first_batch: bool = batch_number == 0
    task_num_start = (task_batch_size * batch_number) + 1
    task_num_end = min(task_batch_size * (batch_number + 1), num_tasks)
    task_range_str = (
        f"Tasks {task_num_start}-{task_num_end}"
        if task_num_start != task_num_end
        else f"Task {task_num_start}"
    )

    if ARGS_PARSER.pause_between_batches <= 0:  # Manual delay
        print_log(
            (
                f"Submitting batch number {batch_number + 1} ({task_range_str})"
                if first_batch
                else (
                    "Pausing before submitting batch number"
                    f" {batch_number + 1} ({task_range_str}). Press enter to continue:"
                )
            ),
            override_quiet=True,
        )
        if not first_batch:
            input()

    elif ARGS_PARSER.pause_between_batches > 0:  # Automatic delay
        print_log(
            f"Submitting batch number {batch_number + 1} ({task_range_str})"
            if first_batch
            else (
                f"Pausing for {ARGS_PARSER.pause_between_batches} seconds before"
                f" submitting batch number {batch_number + 1}"
                f" ({task_range_str})"
            )
        )
        if not first_batch:
            sleep(ARGS_PARSER.pause_between_batches)


def generate_taskdata_object(
    task_data_inputs: Optional[List[Dict]], task_data_outputs: Optional[List[Dict]]
) -> Optional[TaskData]:
    """
    Generate a TaskData object based on task data inputs/outputs.
    """
    if task_data_inputs is None and task_data_outputs is None:
        return None

    try:
        return TaskData(
            inputs=(
                None
                if task_data_inputs is None
                else [TaskDataInput(**x) for x in task_data_inputs]
            ),
            outputs=(
                None
                if task_data_outputs is None
                else [TaskDataOutput(**x) for x in task_data_outputs]
            ),
        )
    except TypeError as e:
        raise Exception(
            f"Unable to generate 'taskDataInputs' or 'taskDataOutputs' list: {str(e)}"
        )


def generate_task_error_matchers_list(
    config_wr: ConfigWorkRequirement, wr_data: dict, tg_data: dict
) -> Optional[List[TaskErrorMatcher]]:
    """
    Generate a list of TaskErrorMatcher objects.
    """
    error_matchers: Optional[List[Dict]] = check_list(
        tg_data.get(
            RETRYABLE_ERRORS,
            wr_data.get(RETRYABLE_ERRORS, config_wr.retryable_errors),
        )
    )

    return (
        None
        if error_matchers is None
        else [
            _generate_task_error_matcher(task_error_matcher_data)
            for task_error_matcher_data in error_matchers
        ]
    )


def _generate_task_error_matcher(task_error_matcher_data: Dict) -> TaskErrorMatcher:
    """
    Generate a TaskErrorMatcher object.
    """
    try:

        exit_codes_str: Optional[List[int]] = check_list(
            task_error_matcher_data.get(PROCESS_EXIT_CODES, None)
        )
        try:
            # Ensure ints
            exit_codes = (
                None
                if exit_codes_str is None
                else [int(exit_code_str) for exit_code_str in exit_codes_str]
            )
        except Exception as e:
            raise Exception(f"Unable to process error exit codes: {e}")

        statuses_str: Optional[List[str]] = check_list(
            task_error_matcher_data.get(STATUSES_AT_FAILURE, None)
        )
        try:
            statuses = (
                None
                if statuses_str is None
                else [TaskStatus(status) for status in statuses_str]
            )
        except Exception as e:
            raise Exception(f"Unable to process error status: {e}")

        error_types: Optional[List[str]] = check_list(
            task_error_matcher_data.get(ERROR_TYPES, None)
        )

        return TaskErrorMatcher(
            errorTypes=error_types,
            statusesAtFailure=statuses,
            processExitCodes=exit_codes,
        )

    except Exception as e:
        raise Exception(
            f"Unable to process task retry error matcher data '{task_error_matcher_data}': {e}"
        )
