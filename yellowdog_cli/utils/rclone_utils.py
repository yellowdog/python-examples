"""
Utility functions for use with the submit command.
"""

import re
from dataclasses import dataclass
from functools import cache
from os import chdir, getcwd
from os.path import exists
from pathlib import Path

from rclone_api import Config, Rclone

from yellowdog_cli.utils.printing import print_error, print_info, print_warning
from yellowdog_cli.utils.property_names import (
    LOCAL_PATH,
    TASK_DATA_SOURCE,
)
from yellowdog_cli.utils.wrapper import ARGS_PARSER


@dataclass
class RcloneUploadedFile:
    """
    Capture the local and destination state of an rcloned file.
    (The destination is actually the 'source' in the
    'taskData.input', hence 'rclone_source'.)
    """

    local_file_path: str
    rclone_source: str


class RcloneUploadedFiles:
    """
    Upload and manage uploaded files from taskData.inputs.
    """

    def __init__(
        self,
        files_directory: str = "",
    ):
        self._rcloned_files: list[RcloneUploadedFile] = []
        self._files_directory = files_directory
        self._working_directory = getcwd()
        self._reported_duplicates: list[RcloneUploadedFile] = []

    def upload_dataclient_input_files(self, task_data_inputs: list[dict] | None):
        """
        Extract files to be uploaded from a task_data_inputs objects, and
        upload them. Important: removes any 'localFile' properties.
        """
        if task_data_inputs is None:
            return

        for task_data_input in task_data_inputs:
            if (local_file := task_data_input.pop(LOCAL_PATH, None)) is not None and (
                source := task_data_input.get(TASK_DATA_SOURCE)
            ) is not None:
                self._upload_rclone_file(local_file, source)

    def _upload_rclone_file(self, local_file: str, rclone_source: str):
        """
        Rclone a DataClient inputs file if it hasn't already been uploaded to
        the same location.
        """
        if self._files_directory != "":
            chdir(self._files_directory)

        if not exists(local_file):
            print_error(f"File '{local_file}' does not exist and cannot be uploaded")
            return

        rclone_uploaded_file = RcloneUploadedFile(local_file, rclone_source)
        if rclone_uploaded_file in self._rcloned_files:
            if rclone_uploaded_file not in self._reported_duplicates:
                print_info(
                    f"Ignoring duplicate file upload '{local_file}' -> "
                    f"'{self._bucket_and_prefix(rclone_uploaded_file)}'"
                )
                self._reported_duplicates.append(rclone_uploaded_file)
            return

        if not ARGS_PARSER.dry_run:
            try:
                self._upload_rclone_file_core(rclone_uploaded_file)
            except Exception as e:
                print_error(
                    f"Unable to upload '{local_file}' -> '{rclone_source}': {e}"
                )
                return
        else:
            print_info(
                f"Dry-run: Would upload '{local_file}' -> "
                f"'{self._bucket_and_prefix(rclone_uploaded_file)}'"
            )

        self._rcloned_files.append(rclone_uploaded_file)

        if self._files_directory != "":
            chdir(self._working_directory)

    def _upload_rclone_file_core(self, rclone_upload_file: RcloneUploadedFile):
        """
        Core upload method for a single file.
        """

        remote_name, config, remote_path = self._parse_rclone_connection_string(
            rclone_upload_file.rclone_source
        )

        # Auto-downloads rclone binary if missing (~20-40 MB, only once)
        rclone = Rclone(Config(config))

        local_file = Path(rclone_upload_file.local_file_path).resolve()
        print_info(
            f"Uploading '{rclone_upload_file.local_file_path}' → "
            f"'{self._bucket_and_prefix(rclone_upload_file)}'"
        )

        result = rclone.copy_to(
            src=str(local_file),
            dst=f"{remote_name}:{remote_path}",
            other_args=[],
        )

        if result.returncode != 0:
            print_error(f"Upload failed: {result.stderr}")

    def delete(self):
        """
        Delete all files that have been rcloned. Note: can't delete
        a list of files in one rclone-api call because they may be
        stored in different places. This can be optimised later by
        grouping into batches of files with the same connection info.
        """
        for rcloned_file in self._rcloned_files:
            self._delete_rcloned_file(rcloned_file.rclone_source)

        self._rcloned_files = []

    def _delete_rcloned_file(self, conn_str: str):
        """
        Deletes exactly one rcloned file specified in the connection string.

        Example:
            conn_str = "rclone:S3,type=s3,provider=AWS,env_auth=true,\
                        region=eu-west-2,location_constraint=eu-west-2:\
                        tech.yellowdog.devsandbox.dev-platform/yd-demo/pwt/file.txt"
            delete_single_s3_object(conn_str)
        """
        remote_name, config_section, remote_path = self._parse_rclone_connection_string(
            conn_str
        )

        # Auto-downloads rclone binary if missing (~20-40 MB, only once)
        rclone = Rclone(Config(config_section))

        rcloned_file = f"{remote_name}:{remote_path}"
        print_info(f"Deleting rcloned file '{rcloned_file}'")
        if not rclone.exists(rcloned_file):
            print_warning(f"Rcloned file does not exist: '{rcloned_file}'")
            return

        result = rclone.delete_files([rcloned_file])

        if result.returncode != 0:
            print_error(
                f"Failed to delete rcloned file '{remote_path}' ({result.stderr})"
            )

    def _parse_rclone_connection_string(
        self, connection_str: str
    ) -> tuple[str, str, str]:
        """
        Parses rclone connection strings like:
        'rclone:NAME,type=...,key=val...:bucket/path/to/file.txt'
        with or without 'rclone:'

        Returns:
            (remote_name, config_ini_section_str, bucket_and_path_prefix)
        """
        # Remove optional leading 'rclone:'
        if connection_str.startswith("rclone:"):
            connection_str = connection_str[7:]

        if ":" not in connection_str:
            raise ValueError("No colon separator found in connection string")

        # Split on LAST colon → config vs path
        remote_part, path_part = connection_str.rsplit(":", 1)
        remote_name, config_section = self._parse_rclone_config(remote_part)
        path_part = path_part.strip()  # keep internal slashes

        return remote_name, config_section, path_part

    @staticmethod
    @cache  # Break into a separate method to facilitate caching
    def _parse_rclone_config(config_str: str) -> tuple[str, str]:
        """
        Parses rclone connection strings like:
        'rclone:NAME,type=...,key=val...' with or without 'rclone:'

        Returns:
            (remote_name, config_ini_section_str)
        """
        if "," not in config_str:
            remote_name = config_str.strip()
            params_str = ""
        else:
            remote_name, params_str = config_str.split(",", 1)
            remote_name = remote_name.strip()

        remote_name = remote_name or "remote"  # fallback

        # Parse params (simple comma split - assumes no commas inside values)
        params = {}
        if params_str:
            # Split on comma only when followed by key=
            param_list = re.split(r",(?=[a-zA-Z_0-9]+=)", params_str)
            for param in param_list:
                param = param.strip()
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key.strip()] = value.strip().strip("'\"")

        # Build valid rclone INI section
        lines = [f"[{remote_name}]"]
        for key, value in params.items():
            lines.append(f"{key} = {value}")
        config_section = "\n".join(lines)

        return remote_name, config_section

    @staticmethod
    def _bucket_and_prefix(rclone_uploaded_file: RcloneUploadedFile):
        """
        Remove everything except the service, bucket name and object name.
        """
        try:
            service, rclone_details, bucket_name_and_object = (
                rclone_uploaded_file.rclone_source.split(":")
            )
            return bucket_name_and_object
        except:
            return rclone_uploaded_file.rclone_source


def upgrade_rclone():
    """
    Upgrade the rclone binary.
    """
    print_info("Downloading / upgrading the rclone binary")
    Rclone.upgrade_rclone()
