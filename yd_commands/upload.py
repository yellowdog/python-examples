#!/usr/bin/env python3

"""
A script to upload files to the YellowDog Object Store.
"""

from os import walk as os_walk
from os.path import join as os_path_join
from pathlib import Path

from yd_commands.args import ARGS_PARSER
from yd_commands.printing import print_log
from yd_commands.upload_utils import upload_file
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Using Object Store namespace '{CONFIG_COMMON.namespace}' "
        f"and directory '{ARGS_PARSER.directory}'"
    )

    files_set = set(ARGS_PARSER.files)
    added_files_set = set()
    removed_dirs_set = set()

    for file_or_dir in files_set:
        pathname = Path(file_or_dir)
        if not pathname.exists():
            raise Exception(f"'{file_or_dir}' doesn't exist")
        if pathname.is_dir():
            if not ARGS_PARSER.recursive:
                raise Exception(
                    f"'{file_or_dir}' is a directory; please use '--recursive/-r'"
                )
            else:
                removed_dirs_set.add(file_or_dir)
                for dir_path, dirs, files in os_walk(file_or_dir):
                    for file in files:
                        added_files_set.add(os_path_join(dir_path, file))

    files_set = files_set.union(added_files_set).difference(removed_dirs_set)

    if ARGS_PARSER.flatten:
        print_log("Flattening upload paths")
    for file in files_set:
        upload_file(
            client=CLIENT,
            filename=file,
            id=ARGS_PARSER.directory,
            namespace=CONFIG_COMMON.namespace,
            url=CONFIG_COMMON.url,
            flatten_upload_paths=ARGS_PARSER.flatten,
        )
    print_log(f"Uploaded {len(files_set)} files")


# Standalone entry point
if __name__ == "__main__":
    main()
