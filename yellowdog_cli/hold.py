#!/usr/bin/env python3

"""
A script to hold Work Requirements.
"""

from yellowdog_cli.utils.start_hold_common import hold_work_requirements
from yellowdog_cli.utils.wrapper import main_wrapper


@main_wrapper
def main():
    hold_work_requirements()


# Entry point
if __name__ == "__main__":
    main()
