#!/usr/bin/env python3

"""
A script to follow event streams.
"""

from threading import Thread
from typing import List

from yd_commands.follow_utils import follow_events
from yd_commands.id_utils import YDIDType, get_ydid_type
from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import ARGS_PARSER, main_wrapper


@main_wrapper
def main():
    """
    Creates an event thread for each ydid passed on the command line.
    """
    ydids = set(ARGS_PARSER.yellowdog_ids)  # Eliminate duplicates
    print_log(f"Following the event stream(s) for {len(ydids)} YellowDog ID(s)")

    threads: List[Thread] = []

    for ydid in ydids:
        ydid_type = get_ydid_type(ydid)
        if ydid_type not in [
            YDIDType.WORK_REQ,
            YDIDType.WORKER_POOL,
            YDIDType.COMPUTE_REQ,
        ]:
            print_error(
                f"Invalid YellowDog ID '{ydid}' (Must be Work Requirement, Worker Pool"
                " or Compute Requirement)"
            )
            continue

        thread = Thread(target=follow_events, args=(ydid, ydid_type), daemon=True)
        try:
            thread.start()
        except RuntimeError as e:
            print_error(f"Unable to start event thread for '{ydid}': ({e})")
            continue
        threads.append(thread)

    for thread in threads:
        thread.join()

    print_log("All event streams have finished")


# Standalone entry point
if __name__ == "__main__":
    main()
