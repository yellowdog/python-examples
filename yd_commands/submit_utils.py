"""
Utility functions for use with the submit command.
"""

import re
from dataclasses import dataclass
from glob import glob
from typing import List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.model import ObjectPath, TaskInput, TaskInputVerification

from yd_commands.config_types import (
    NAMESPACE_SEPARATOR,
    ConfigCommon,
    ConfigWorkRequirement,
)
from yd_commands.printing import print_error, print_log
from yd_commands.upload_utils import unique_upload_pathname, upload_file_core
from yd_commands.variables import substitute_variable_str
from yd_commands.wrapper import ARGS_PARSER


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
        file_parts = file.split(NAMESPACE_SEPARATOR)

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

    def __init__(self, client: PlatformClient, wr_name: str, config: ConfigCommon):
        self._client = client
        self._wr_name = wr_name
        self._config = config
        self._uploaded_files: List[UploadedFile] = []

    def add_upload_file(self, upload_file: str, upload_path: str):
        """
        Upload a file if it hasn't already been uploaded to the same location.
        Handle wildcards.
        """

        # Handle wildcard expansion
        expanded_files = glob(pathname=upload_file, recursive=True)
        if len(expanded_files) > 1:
            if not upload_path.endswith("*"):
                raise Exception(
                    "'uploadPath' must end in '*' when using'uploadFiles' wildcards"
                )

        for upload_file in expanded_files:
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
                    f" '{namespace}::{uploaded_file_path}'"
                )

            self._uploaded_files.append(
                UploadedFile(
                    local_file_path=upload_file,
                    upload_namespace=namespace,
                    uploaded_file_path=uploaded_file_path,
                )
            )

    def add_input_file(self, filename: str, flatten_upload_paths: bool) -> List[str]:
        """
        Add a filename from the inputs list, processing wildcards if present.
        Return the expanded list of filenames.
        """

        # Expand wildcards
        expanded_files = glob(pathname=filename, recursive=True)

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
            self.add_upload_file(filename, f"{NAMESPACE_SEPARATOR}{upload_file_name}")

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


def format_yd_name(yd_name: str) -> str:
    """
    Format a string to be consistent with YellowDog naming requirements.
    """
    # Make obvious substitutions
    yd_name = yd_name.replace("/", "-").replace(" ", "_").lower()
    # Enforce acceptable regex and name length
    yd_name = re.sub("[^a-z0-9_-]", "", yd_name)
    if not yd_name[0].isalpha():
        yd_name = f"yd_{yd_name}"
    return yd_name[:60]


def update_config_work_requirement(config_wr: ConfigWorkRequirement):
    """
    Update a ConfigWorkRequirement Object with the current dictionary of
    variable substitutions. Returns the updated object.
    """
    config_wr_str_processed = substitute_variable_str(str(config_wr))
    # Note: 'literal_eval' doesn't work here
    return eval(config_wr_str_processed)
