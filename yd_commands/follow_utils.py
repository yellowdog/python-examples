"""
Utility function to follow event streams.
"""

from threading import Thread
from typing import List, Optional

import requests

from yd_commands.id_utils import YDIDType, get_ydid_type
from yd_commands.object_utilities import get_compute_requirement_id_by_worker_pool_id
from yd_commands.printing import print_error, print_event, print_log, print_warning
from yd_commands.wrapper import CLIENT, CONFIG_COMMON


def follow_ids(ydids: List[str], auto_cr: bool = False):
    """
    Creates an event thread for each YDID passed on the command line.
    """
    if len(ydids) == 0:
        return

    ydids_set = set(ydids)  # Eliminate duplicates
    num_duplicates = len(ydids) - len(ydids_set)
    if num_duplicates > 0:
        print_warning(f"Ignoring {num_duplicates} duplicate YellowDog ID(s)")

    if auto_cr:
        # Automatically add Compute Requirement IDs for
        # Provisioned Worker Pools, to follow both
        cr_ydids = set()
        for ydid in ydids_set:
            if get_ydid_type(ydid) == YDIDType.WORKER_POOL:
                cr_ydid = get_compute_requirement_id_by_worker_pool_id(CLIENT, ydid)
                if cr_ydid is not None:
                    print_log(
                        f"Adding event stream for Compute Requirement '{cr_ydid}'"
                    )
                    cr_ydids.add(cr_ydid)
        ydids_set = ydids_set.union(cr_ydids)

    print_log(f"Following the event stream(s) for {len(ydids_set)} YellowDog ID(s)")

    threads: List[Thread] = []

    for ydid in ydids_set:
        ydid_type = get_ydid_type(ydid)
        if ydid_type not in [
            YDIDType.WORK_REQ,
            YDIDType.WORKER_POOL,
            YDIDType.COMPUTE_REQ,
        ]:
            print_error(
                f"Invalid YellowDog ID '{ydid}' (Must be valid YDID for Work"
                " Requirement, Worker Pool or Compute Requirement)"
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

    if len(threads) > 1:
        print_log("All event streams have concluded")


def follow_events(ydid: str, ydid_type: YDIDType):
    """
    Follow events.
    """
    response = requests.get(
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        url=get_event_url(ydid, ydid_type),
        stream=True,
    )

    if response.status_code != 200:
        print_error(f"'{ydid}': {response.json()['message']}")
        return

    if response.encoding is None:
        response.encoding = "utf-8"

    try:
        for event in response.iter_lines(decode_unicode=True):
            if event:
                print_event(event, ydid_type)
    except Exception as e:
        print_warning(f"Event stream error: {e}")

    print_log(f"Event stream concluded for '{ydid}'")


def get_event_url(ydid: str, ydid_type: YDIDType) -> Optional[str]:
    """
    Get the event stream URL.
    """
    if ydid_type is YDIDType.WORK_REQ:
        return f"{CONFIG_COMMON.url}/work/requirements/{ydid}/updates"
    if ydid_type == YDIDType.WORKER_POOL:
        return f"{CONFIG_COMMON.url}/workerPools/{ydid}/updates"
    if ydid_type == YDIDType.COMPUTE_REQ:
        return f"{CONFIG_COMMON.url}/compute/requirements/{ydid}/updates"
