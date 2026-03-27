#!/usr/bin/env python3

"""
Download files from a remote data client.
"""

from pathlib import Path

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.config_types import ConfigDataClient
from yellowdog_cli.utils.dataclient_utils import download_files, resolve_remote_path
from yellowdog_cli.utils.dataclient_wrapper import dataclient_wrapper
from yellowdog_cli.utils.load_config import load_config_data_client
from yellowdog_cli.utils.rclone_utils import upgrade_rclone, which_rclone

CONFIG_DATA_CLIENT: ConfigDataClient = load_config_data_client()


@dataclient_wrapper
def main():
    if ARGS_PARSER.upgrade_rclone:
        upgrade_rclone()
        return

    if ARGS_PARSER.which_rclone:
        which_rclone()
        return

    sync = ARGS_PARSER.sync or False
    flatten = ARGS_PARSER.flatten or False
    dry_run = ARGS_PARSER.dry_run or False
    explicit_destination = ARGS_PARSER.destination

    for remote_path_str in ARGS_PARSER.remote_paths:
        remote_path = resolve_remote_path(
            CONFIG_DATA_CLIENT, relative_path=remote_path_str
        )
        if explicit_destination:
            destination = Path(explicit_destination)
        elif any(c in remote_path_str for c in "*?["):
            # Glob pattern: download into the current directory so the matched
            # items land here rather than inside a dir literally named 'pyex*'
            destination = Path(".")
        else:
            # Mirror the remote directory name locally so that downloading
            # 'mydir' creates './mydir/' rather than spilling contents into './'
            basename = remote_path_str.rstrip("/").rsplit("/", 1)[-1]
            destination = Path(basename)
        download_files(
            CONFIG_DATA_CLIENT,
            remote_path,
            destination,
            flatten=flatten,
            sync=sync,
            dry_run=dry_run,
        )


if __name__ == "__main__":
    main()
