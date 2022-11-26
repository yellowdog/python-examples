#!/usr/bin/env python3

"""
A script to upload files to the YellowDog Object Store.
"""

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
    if ARGS_PARSER.flatten:
        print_log("Flattening upload paths")
    for file in ARGS_PARSER.files():
        upload_file(
            client=CLIENT,
            filename=file,
            id=ARGS_PARSER.directory,
            namespace=CONFIG_COMMON.namespace,
            url=CONFIG_COMMON.url,
            flatten_upload_paths=ARGS_PARSER.flatten,
        )


# Standalone entry point
if __name__ == "__main__":
    main()
