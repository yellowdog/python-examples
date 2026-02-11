#!/usr/bin/env python3

"""
A script to follow event streams.
"""

from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.printing import print_info
from yellowdog_cli.utils.wrapper import ARGS_PARSER, main_wrapper


@main_wrapper
def main():
    if len(ARGS_PARSER.yellowdog_ids) == 0:
        print_info("No YellowDog IDs to follow")
        return

    follow_ids(ARGS_PARSER.yellowdog_ids, ARGS_PARSER.auto_cr)


# Standalone entry point
if __name__ == "__main__":
    main()
