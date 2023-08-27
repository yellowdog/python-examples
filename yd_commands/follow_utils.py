"""
Utility function to follow event streams.
"""
from typing import Optional

import requests

from yd_commands.id_utils import YDIDType
from yd_commands.printing import print_error, print_event, print_log
from yd_commands.wrapper import CONFIG_COMMON


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

    for event in response.iter_lines(decode_unicode=True):
        if event:
            print_event(event, ydid_type)

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
