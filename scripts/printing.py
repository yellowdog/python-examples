"""
Functions focused on print outputs.
"""

import sys
from datetime import datetime
from typing import List, Optional, TypeVar

from yellowdog_client.model import (
    ComputeRequirementSummary,
    ConfiguredWorkerPool,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

from args import ARGS_PARSER
from object_utilities import Item, get_task_group_name


def print_string(msg: str = "") -> str:
    """
    Message output format.
    """
    return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {msg}"


def print_log(
    log_message: str,
    override_quiet: bool = False,
    flush: bool = True,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    print(
        print_string(log_message),
        flush=flush,
    )


ErrorObject = TypeVar(
    "ErrorObject",
    Exception,
    str,
)


def print_error(error_obj: ErrorObject):
    """
    Print an error message to stderr.
    """
    print(print_string(f"Error: {error_obj}"), file=sys.stderr, flush=True)


TYPE_MAP = {
    ConfiguredWorkerPool: "Configured Worker Pool",
    ProvisionedWorkerPool: "Provisioned Worker Pool",
    WorkerPoolSummary: "Worker Pool",
    ComputeRequirementSummary: "Compute Requirement",
    Task: "Task",
    TaskGroup: "Task Group",
    WorkRequirementSummary: "Work Requirement",
    ObjectPath: "Object Path",
}


def get_type_name(obj: Item) -> str:
    """
    Get the display name of an object's type
    """
    return TYPE_MAP.get(type(obj), "")


def print_numbered_object_list(
    objects: List[Item], parent: Optional[Item] = None, override_quiet: bool = False
) -> None:
    """
    Print a numbered list of objects.
    """
    if len(objects) == 0:
        return

    print_log(
        f"Displaying matching {get_type_name(objects[0])}(s):",
        override_quiet=override_quiet,
    )
    print()
    indent = " " * 3
    index_len = len(str(len(objects)))
    for index, obj in enumerate(objects):
        try:
            status = f" ({obj.status})"
        except:
            status = ""
        if (
            isinstance(obj, Task)
            and parent is not None
            and isinstance(parent, WorkRequirementSummary)
        ):
            # Special case for Task objects
            print(
                f"{indent}{str(index + 1).rjust(index_len)} : "
                f"[TaskGroup: '{get_task_group_name(parent, obj)}'] "
                f"{obj.name}{status}"
            )
        elif isinstance(obj, WorkerPoolSummary):
            try:
                obj_type = "[" + obj.type.split(".")[-1:][0] + "]"
            except IndexError:
                obj_type = ""
            print(
                f"{indent}{str(index + 1).rjust(index_len)} : "
                f"{obj.name}{status} {obj_type}"
            )
        else:
            print(f"{indent}{str(index + 1).rjust(index_len)} : {obj.name}{status}")
    print()


def sorted_objects(objects: List[Item], reverse: bool = False) -> List[Item]:
    return sorted(objects, key=lambda x: x.name, reverse=reverse)
