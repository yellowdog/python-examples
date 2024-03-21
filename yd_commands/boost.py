#!/usr/bin/env python3

"""
A script to boost allowances.
"""

from yd_commands.interactive import confirmed
from yd_commands.printing import print_log
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():
    if not confirmed(
        f"Boost Allowance {ARGS_PARSER.allowance} by {ARGS_PARSER.boost_hours} hours?"
    ):
        return

    try:
        CLIENT.allowances_client.boost_allowance_by_id(
            ARGS_PARSER.allowance, ARGS_PARSER.boost_hours
        )
    except Exception as e:
        raise Exception(f"Unable to boost Allowance {ARGS_PARSER.allowance}: {e}")

    print_log(
        f"Boosted Allowance {ARGS_PARSER.allowance} by {ARGS_PARSER.boost_hours} hours"
    )


# Standalone entry point
if __name__ == "__main__":
    main()
