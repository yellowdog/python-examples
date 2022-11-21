"""
Functions focused on print outputs.
"""

import sys
from datetime import datetime
from typing import List, Optional, TypeVar

from tabulate import tabulate
from yellowdog_client import PlatformClient
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

from yd_commands.args import ARGS_PARSER
from yd_commands.object_utilities import Item


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
    Get the display name of an object's type.
    """
    return TYPE_MAP.get(type(obj), "")


def compute_requirement_table(
    cr_summary_list: List[ComputeRequirementSummary],
) -> List[List]:
    table = []
    for index, cr_summary in enumerate(cr_summary_list):
        table.append(
            [
                index + 1,
                ":",
                cr_summary.name,
                f"[{cr_summary.status}]",
            ]
        )
    return table


def work_requirement_table(
    wr_summary_list: List[WorkRequirementSummary],
) -> List[List]:
    table = []
    for index, wr_summary in enumerate(wr_summary_list):
        table.append(
            [
                index + 1,
                ":",
                wr_summary.name,
                f"[{wr_summary.status}]",
            ]
        )
    return table


def task_group_table(
    task_group_list: List[TaskGroup],
) -> List[List]:
    table = []
    for index, task_group in enumerate(task_group_list):
        table.append(
            [
                index + 1,
                ":",
                task_group.name,
                f"[{task_group.status}]",
            ]
        )
    return table


def task_table(task_list: List[Task]) -> List[List]:
    table = []
    for index, task in enumerate(task_list):
        table.append(
            [
                index + 1,
                ":",
                task.name,
                f"[{task.status}]",
            ]
        )
    return table


def worker_pool_table(worker_pool_summaries: List[WorkerPoolSummary]) -> List[List]:
    table = []
    for index, worker_pool_summary in enumerate(worker_pool_summaries):
        table.append(
            [
                index + 1,
                ":",
                worker_pool_summary.name,
                f"[{worker_pool_summary.status}]",
                f"[{worker_pool_summary.type.split('.')[-1:][0]}]",
            ]
        )
    return table


def print_numbered_object_list(
    client: PlatformClient,
    objects: List[Item],
    parent: Optional[Item] = None,
    override_quiet: bool = False,
) -> None:
    """
    Print a numbered list of objects.
    Assume that the list supplied is already sorted.
    """
    if len(objects) == 0:
        return

    print_log(
        f"Displaying matching {get_type_name(objects[0])}(s):",
        override_quiet=override_quiet,
    )
    print()

    if isinstance(objects[0], ComputeRequirementSummary):
        table = compute_requirement_table(objects)
    elif isinstance(objects[0], WorkRequirementSummary):
        table = work_requirement_table(objects)
    elif isinstance(objects[0], TaskGroup):
        table = task_group_table(objects)
    elif isinstance(objects[0], Task):
        table = task_table(objects)
    elif isinstance(objects[0], WorkerPoolSummary):
        table = worker_pool_table(objects)
    else:
        table = []
        for index, obj in enumerate(objects):
            table.append([index + 1, ":", obj.name])

    print(indent(tabulate(table, tablefmt="plain"), indent_width=4))
    print()


def sorted_objects(objects: List[Item], reverse: bool = False) -> List[Item]:
    """
    Sort objects by their 'name' property.
    """
    return sorted(objects, key=lambda x: x.name, reverse=reverse)


def indent(txt: str, indent_width: int = 4) -> str:
    """
    Indent lines of text.
    """
    return "\n".join(" " * indent_width + ln for ln in txt.splitlines())
