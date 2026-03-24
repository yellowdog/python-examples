"""
Utility functions for use with the submit command.
"""

import logging
import os
import platform
import re
import sys
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from functools import cache
from os import chdir, getcwd
from os.path import abspath, exists
from pathlib import Path

from rclone_api import Config, Rclone

from yellowdog_cli.utils.printing import print_error, print_info, print_warning
from yellowdog_cli.utils.property_names import (
    DATA_CLIENT_LOCAL_PATH,
    DATA_CLIENT_UPLOAD_PATH,
    TASK_DATA_SOURCE,
)
from yellowdog_cli.utils.wrapper import ARGS_PARSER


@contextmanager
def _suppress_rclone_download_output():
    """
    Silence rclone-api's binary-download output.

    rclone_api/install.py calls logging.basicConfig(level=DEBUG) and writes
    to the root logger, and the 'download' package it uses emits a tqdm
    progress bar to stderr. Neither can be quieted via the Rclone() API, so
    we suppress them here by temporarily replacing the root logger's handlers
    with a NullHandler and redirecting sys.stdout/sys.stderr to /dev/null.
    """
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers = [logging.NullHandler()]
    old_stdout, old_stderr = sys.stdout, sys.stderr
    devnull = open(os.devnull, "w")
    sys.stdout = sys.stderr = devnull
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        devnull.close()
        root.handlers = old_handlers


def _find_rclone_conf() -> Path:
    """
    Locate the system rclone configuration file.

    Respects the RCLONE_CONFIG environment variable; otherwise falls back to
    the platform-default location (~/.config/rclone/rclone.conf on Linux/macOS,
    %APPDATA%\\rclone\\rclone.conf on Windows).

    Raises an exception if no config file is found.
    """
    if env_path := os.environ.get("RCLONE_CONFIG"):
        p = Path(env_path)
        if p.exists():
            return p
        raise Exception(f"RCLONE_CONFIG points to missing file: '{env_path}'")

    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", "")
        p = Path(appdata) / "rclone" / "rclone.conf"
    else:
        p = Path.home() / ".config" / "rclone" / "rclone.conf"

    if p.exists():
        return p
    raise Exception(f"No rclone config file found at '{p}'")


def _make_rclone(config: Config | None) -> Rclone:
    """
    Instantiate Rclone, suppressing download output when --quiet is active.
    Passing None causes rclone to use the system rclone.conf (for locally
    configured remotes).
    """
    rclone_conf: Config | Path = _find_rclone_conf() if config is None else config
    ctx = _suppress_rclone_download_output() if ARGS_PARSER.quiet else nullcontext()
    with ctx:
        return Rclone(rclone_conf)


@dataclass
class RcloneUploadedFile:
    """
    Capture the local and destination state of an rcloned file.
    """

    local_file_path: str
    upload_file_path: str


class RcloneUploadedFiles:
    """
    Upload and manage uploaded files from taskData.inputs.
    """

    def __init__(
        self,
        files_directory: str = ".",
    ):
        self._rcloned_files: list[RcloneUploadedFile] = []
        self._files_directory = abspath(files_directory)
        self._working_directory = getcwd()

    def upload_dataclient_input_files(self, task_data_inputs: list[dict] | None):
        """
        Extract files to be uploaded from a task_data_inputs objects, and
        upload them. Important: removes any 'localFile' and 'uploadPath'
        properties.
        """
        if task_data_inputs is None:
            return

        for task_data_input in task_data_inputs:
            if (
                local_file := task_data_input.pop(DATA_CLIENT_LOCAL_PATH, None)
            ) is None:
                continue
            if (
                upload_path := task_data_input.pop(DATA_CLIENT_UPLOAD_PATH, None)
            ) is None:
                if (upload_path := task_data_input.get(TASK_DATA_SOURCE, None)) is None:
                    continue
            self._upload_rclone_file(local_file, upload_path)

    def _upload_rclone_file(self, local_file: str, rclone_upload_path: str):
        """
        Rclone a DataClient inputs file if it hasn't already been uploaded to
        the same location.
        """
        chdir(self._files_directory)

        if not exists(local_file):
            raise Exception(
                f"File '{Path(self._files_directory)/local_file}' does not exist "
                "and cannot be uploaded"
            )

        rclone_uploaded_file = RcloneUploadedFile(local_file, rclone_upload_path)
        if rclone_uploaded_file in self._rcloned_files:
            # Duplicate
            return

        if not ARGS_PARSER.dry_run:
            try:
                self._upload_rclone_file_core(rclone_uploaded_file)
            except Exception as e:
                raise Exception(
                    f"Unable to upload '{local_file}' -> '{rclone_upload_path}': {e}"
                )
        else:
            print_info(
                f"Dry-run: Would upload '{local_file}' -> "
                f"'{self._bucket_and_prefix(rclone_uploaded_file)}'"
            )

        self._rcloned_files.append(rclone_uploaded_file)

        chdir(self._working_directory)

    def _upload_rclone_file_core(self, rclone_upload_file: RcloneUploadedFile):
        """
        Core upload method for a single file.
        """

        remote_name, config_section, remote_path = self._parse_rclone_connection_string(
            rclone_upload_file.upload_file_path
        )

        # Auto-downloads rclone binary if missing (~20-40 MB, only once)
        rclone = _make_rclone(
            Config(config_section) if config_section is not None else None
        )

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
            raise Exception(f"Upload failed: {result.stderr}")

    def delete(self):
        """
        Delete all files that have been rcloned. Note: can't delete
        a list of files in one rclone-api call because they may be
        stored in different places. This can be optimised later by
        grouping into batches of files with the same connection info.
        """
        for rcloned_file in self._rcloned_files:
            self._delete_rcloned_file(rcloned_file.upload_file_path)

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
        rclone = _make_rclone(
            Config(config_section) if config_section is not None else None
        )

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
    ) -> tuple[str, str | None, str]:
        """
        Parses rclone connection strings in two forms:

        Inline config (all parameters embedded in the string):
          'rclone:NAME,type=...,key=val...:bucket/path/to/file.txt'

        Local rclone.conf remote (remote name only, no inline parameters):
          'rclone:yds3:/path/to/file.txt'

        The leading 'rclone:' is optional in both forms.

        Returns:
            (remote_name, config_ini_section_str_or_None, bucket_and_path_prefix)
            config_ini_section_str is None for locally configured remotes,
            indicating that the system rclone.conf should be used.
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
    def _parse_rclone_config(config_str: str) -> tuple[str, str | None]:
        """
        Parses the config portion of an rclone connection string.

        Returns:
            (remote_name, config_ini_section_str_or_None)
            Returns None for the config when there are no inline parameters,
            indicating that the remote should be looked up in the system
            rclone.conf rather than using an inline config.
        """
        if "," not in config_str:
            # No inline params: remote is defined in the system rclone.conf
            remote_name = config_str.strip() or "remote"
            return remote_name, None

        remote_name, params_str = config_str.split(",", 1)
        remote_name = remote_name.strip() or "remote"

        # Parse params (simple comma split - assumes no commas inside values)
        params = {}
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
                rclone_uploaded_file.upload_file_path.split(":")
            )
            return bucket_name_and_object
        except Exception:
            return rclone_uploaded_file.upload_file_path


def upgrade_rclone():
    """
    Upgrade the rclone binary.
    """
    print_info("Downloading / upgrading the rclone binary")
    Rclone.upgrade_rclone()
