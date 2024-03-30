#!/usr/bin/env python3

"""
A script to boost allowances.
"""

from yd_commands.interactive import confirmed
from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():

    count = 0
    for allowance in ARGS_PARSER.allowance_list:
        if not confirmed(
            f"Boost Allowance {allowance} by {ARGS_PARSER.boost_hours} hours?"
        ):
            continue
        try:
            CLIENT.allowances_client.boost_allowance_by_id(
                allowance, ARGS_PARSER.boost_hours
            )
            print_log(
                f"Boosted Allowance {allowance} by {ARGS_PARSER.boost_hours} hours"
            )
            count += 1
        except Exception as e:
            print_error(f"Unable to boost Allowance {allowance}: {e}")

    if count > 1:
        print_log(f"Boosted {count} allowances by {ARGS_PARSER.boost_hours} hours")


# Standalone entry point
if __name__ == "__main__":
    main()
