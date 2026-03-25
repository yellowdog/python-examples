#!/usr/bin/env python3

"""
Delete files or directories from a remote data client.
"""

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.config_types import ConfigDataClient
from yellowdog_cli.utils.dataclient_utils import delete_remote, resolve_remote_path
from yellowdog_cli.utils.dataclient_wrapper import dataclient_wrapper
from yellowdog_cli.utils.interactive import confirmed
from yellowdog_cli.utils.load_config import load_config_data_client
from yellowdog_cli.utils.printing import print_info

CONFIG_DATA_CLIENT: ConfigDataClient = load_config_data_client()


@dataclient_wrapper
def main():
    """ """
    recursive = ARGS_PARSER.recursive or False
    dry_run = ARGS_PARSER.dry_run or False
    remote_paths = ARGS_PARSER.remote_paths or []

    if not remote_paths:
        # No paths supplied: operate on the entire default prefix
        remote_path = resolve_remote_path(CONFIG_DATA_CLIENT)
        if not recursive:
            print_info(
                "No remote paths specified. "
                f"Use --recursive to delete the entire prefix: '{remote_path}'"
            )
            return
        _delete_one(remote_path, recursive=True, dry_run=dry_run)
    else:
        for path_str in remote_paths:
            remote_path = resolve_remote_path(
                CONFIG_DATA_CLIENT, relative_path=path_str
            )
            _delete_one(remote_path, recursive=recursive, dry_run=dry_run)


def _delete_one(remote_path: str, recursive: bool, dry_run: bool) -> None:
    """ """
    if dry_run:
        action = "recursively delete" if recursive else "delete"
        print_info(f"Dry-run: Would {action} '{remote_path}'")
        return
    action = "Recursively delete" if recursive else "Delete"
    if confirmed(f"{action} '{remote_path}'?"):
        delete_remote(CONFIG_DATA_CLIENT, remote_path, recursive=recursive)


if __name__ == "__main__":
    main()
