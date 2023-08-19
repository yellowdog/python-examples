#!/usr/bin/env python3

"""
A script to follow event streams.
"""

from enum import Enum
from json import loads as json_loads
from threading import Thread
from typing import Callable, Dict, List

import requests

from yd_commands.printing import print_error, print_json, print_log
from yd_commands.wrapper import ARGS_PARSER, CONFIG_COMMON, main_wrapper


class IdType(Enum):
    WORK_REQ = "Work Requirement"
    WORKER_POOL = "Worker Pool"
    COMPUTE_REQ = "Compute Requirement"


@main_wrapper
def main():
    """
    Creates an event thread for each ydid passed on the command line.
    """
    print_log(
        f"Following the event stream(s) for {len(ARGS_PARSER.yellowdog_ids)} YellowDog"
        " ID(s)"
    )

    threads: List[Thread] = []

    for ydid in ARGS_PARSER.yellowdog_ids:
        if ":workreq:" in ydid:
            target = follow_events
            url = f"{CONFIG_COMMON.url}/work/requirements/{ydid}/updates"
            id_type = IdType.WORK_REQ
            event_processor = print_event
        elif ":wrkrpool:" in ydid:
            target = follow_events
            url = f"{CONFIG_COMMON.url}/workerPools/{ydid}/updates"
            id_type = IdType.WORKER_POOL
            event_processor = print_event
        elif ":compreq:" in ydid:
            target = follow_events
            url = f"{CONFIG_COMMON.url}/compute/requirements/{ydid}/updates"
            id_type = IdType.COMPUTE_REQ
            event_processor = print_event
        else:
            print_error(
                f"Invalid YellowDog ID '{ydid}' (Must be Work Requirement, Worker Pool"
                " or Compute Requirement)"
            )
            continue
        thread = Thread(
            target=target, args=(url, event_processor, id_type), daemon=True
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def follow_events(url: str, event_handler: Callable, id_type: IdType):
    """
    Follow events.
    """
    response = requests.get(
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        url=url,
        stream=True,
    )
    if response.status_code != 200:
        print_error(f"{response.json()['message']}")
        return
    if response.encoding is None:
        response.encoding = "utf-8"
    for event in response.iter_lines(decode_unicode=True):
        if event:
            event_handler(event, id_type)


def print_event(event: str, id_type: IdType):
    """
    Print a YellowDog event.
    """
    data_prefix = "data:"

    # Ignore events that don't have a 'data:' payload
    if not event.startswith(data_prefix):
        return

    event_data: Dict = json_loads(event.replace(data_prefix, ""))

    indent = "\n                      --> "

    if id_type == IdType.WORK_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        for task_group in event_data["taskGroups"]:
            msg += (
                f"{indent}Task Group '{task_group['name']}':"
                f" {task_group['taskSummary']['statusCounts']['COMPLETED']} of"
                f" {task_group['taskSummary']['taskCount']} Task(s) completed"
            )

    elif id_type == IdType.WORKER_POOL:
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

    elif id_type == IdType.COMPUTE_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += (
            f"{indent}{event_data['targetInstanceCount']} Target Instance(s),"
            f" {event_data['expectedInstanceCount']} Expected Instance(s)"
        )

    else:
        return

    print_log(msg, override_quiet=True, no_fill=True)


# Standalone entry point
if __name__ == "__main__":
    main()
