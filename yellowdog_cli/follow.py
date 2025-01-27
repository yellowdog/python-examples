#!/usr/bin/env python3

"""
A script to follow event streams.
"""

from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.wrapper import ARGS_PARSER, main_wrapper


@main_wrapper
def main():
    follow_ids(ARGS_PARSER.yellowdog_ids, ARGS_PARSER.auto_cr)


# Standalone entry point
if __name__ == "__main__":
    main()
