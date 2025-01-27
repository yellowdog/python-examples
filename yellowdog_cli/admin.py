#!/usr/bin/env python3

"""
Skeleton CLI for admin commands (YellowDog only)
"""

import requests

from yellowdog_cli.utils.printing import print_error, print_log
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    """
    Refresh Work Requirements. Note that the Application must be a member
    of the 'yellowdog' account (which confers admin rights).
    """
    for wr_id in ARGS_PARSER.wr_ids:
        response = requests.post(
            url=f"{CONFIG_COMMON.url}/admin/work/requirements/{wr_id}/refresh",
            headers={
                "Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"
            },
        )
        if response.status_code == 200:
            print_log(f"Refreshed Work Requirement '{wr_id}'")
        else:
            print_error(f"Failed to refresh Work Requirement '{wr_id}'")
            raise Exception(f"{response.text}")


# Standalone entry point
if __name__ == "__main__":
    main()
