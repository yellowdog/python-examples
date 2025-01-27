#!/usr/bin/env python3

"""
A script to start held Work Requirements.
"""

from yellowdog_cli.utils.start_hold_common import start_work_requirements
from yellowdog_cli.utils.wrapper import main_wrapper


@main_wrapper
def main():
    start_work_requirements()


# Entry point
if __name__ == "__main__":
    main()
