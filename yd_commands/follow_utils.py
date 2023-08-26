#!/usr/bin/env python3

"""
Utility function to follow event streams.
"""

from enum import Enum
from json import loads as json_loads
from typing import Dict, Optional

import requests

from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import CONFIG_COMMON


class YDIDType(Enum):
    WORK_REQ = "Work Requirement"
    WORKER_POOL = "Worker Pool"
    COMPUTE_REQ = "Compute Requirement"


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


def print_event(event: str, id_type: YDIDType):
    """
    Print a YellowDog event.
    """
    data_prefix = "data:"

    # Ignore events that don't have a 'data:' payload
    if not event.startswith(data_prefix):
        return

    event_data: Dict = json_loads(event.replace(data_prefix, ""))

    indent = "\n                      --> "

    if id_type == YDIDType.WORK_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        for task_group in event_data["taskGroups"]:
            msg += (
                f"{indent}Task Group '{task_group['name']}':"
                f" {task_group['taskSummary']['statusCounts']['COMPLETED']} of"
                f" {task_group['taskSummary']['taskCount']} Task(s) completed"
            )

    elif id_type == YDIDType.WORKER_POOL:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += (
            f"{indent}{event_data['nodeSummary']['statusCounts']['RUNNING']} Node(s)"
            " running"
        )
        msg += (
            f"{indent}Worker(s):"
            f" {event_data['workerSummary']['statusCounts']['DOING_TASK']} working,"
            f" {event_data['workerSummary']['statusCounts']['SLEEPING']} sleeping"
        )

    elif id_type == YDIDType.COMPUTE_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += (
            f"{indent}{event_data['targetInstanceCount']} Target Instance(s),"
            f" {event_data['expectedInstanceCount']} Expected Instance(s)"
        )

    else:
        return

    print_log(msg, override_quiet=True, no_fill=True)


def get_ydid_type(ydid: str) -> Optional[YDIDType]:
    """
    Find the type of a YDID.
    """
    if ":workreq:" in ydid:
        return YDIDType.WORK_REQ
    elif ":wrkrpool:" in ydid:
        return YDIDType.WORKER_POOL
    elif ":compreq:" in ydid:
        return YDIDType.COMPUTE_REQ
    else:
        return None


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
