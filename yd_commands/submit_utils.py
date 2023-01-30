"""
Utility functions for use with the submit command
"""

from dataclasses import dataclass
from typing import List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.model import TaskInput, TaskInputVerification

from yd_commands.config import ConfigCommon
from yd_commands.upload_utils import upload_file, upload_file_core
from yd_commands.wrapper import ARGS_PARSER

NAMESPACE_SEPARATOR = "::"


def generate_task_input_list(
    files: List[str], verification: TaskInputVerification, wr_name: str
) -> List[TaskInput]:
    """
    Generate a TaskInput list.
    """
    task_input_list: List[TaskInput] = []
    for file in files:
        task_input_list.append(generate_task_input(file, verification, wr_name))
    return task_input_list


def generate_task_input(
    file: str, verification: TaskInputVerification, wr_name: str
) -> TaskInput:
    """
    Generate a TaskInput, accommodating files located relative to the root of
    the namespace, relative to the root of a different namespace,
    and relative to the directory specific to this Work Requirement.
    """
    namespace, filepath = get_namespace_and_filepath(file, wr_name)
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


def upload_input_file(
    client: PlatformClient,
    config: ConfigCommon,
    input_file: str,
    wr_id: str,
    uploaded_files: List[str],
    input_folder_name: Optional[str],
    flatten_upload_paths: bool,
):
    """
    Upload an input file, if not already uploaded.
    Add the file to the list of uploaded files
    """
    if ARGS_PARSER.dry_run or input_file in uploaded_files:
        return

    upload_file(
        client=client,
        filename=input_file,
        namespace=config.namespace,
        id=wr_id,
        url=config.url,
        input_folder_name=input_folder_name,
        flatten_upload_paths=flatten_upload_paths,
    )
    uploaded_files.append(input_file)


@dataclass
class UploadedFile:
    original_file_path: str
    namespace: Optional[str]
    uploaded_file_path: str


class UploadedFiles:
    """
    Upload and keep track of uploaded files.
    """

    def __init__(self, client: PlatformClient, wr_name: str, config: ConfigCommon):
        self._client = client
        self._wr_name = wr_name
        self._config = config
        self._uploaded_files: List[UploadedFile] = []

    def add_upload_file(self, upload_file: str, upload_path: str):
        """
        Upload a file if it hasn't already been uploaded to the same location.
        """
        if ARGS_PARSER.dry_run:
            return

        if upload_file in [
            f.original_file_path for f in self._uploaded_files
        ] and upload_path in [f.uploaded_file_path for f in self._uploaded_files]:
            return

        namespace, uploaded_file_path = get_namespace_and_filepath(
            upload_path, self._wr_name
        )

        upload_file_core(
            client=self._client,
            url=self._config.url,
            local_file=upload_file,
            namespace=self._config.namespace if namespace is None else namespace,
            remote_file=uploaded_file_path,
        )

        self._uploaded_files.append(UploadedFile(upload_file, namespace, upload_path))
