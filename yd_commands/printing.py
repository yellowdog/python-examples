"""
Functions focused on print outputs.
"""

import sys
from datetime import datetime
from json import dumps as json_dumps
from textwrap import indent as text_indent
from typing import Dict, List, Optional, TypeVar

from tabulate import tabulate
from yellowdog_client import PlatformClient
from yellowdog_client.common.json import Json
from yellowdog_client.model import (
    ComputeRequirementSummary,
    ComputeRequirementTemplateUsage,
    ConfiguredWorkerPool,
    ObjectPath,
    ProvisionedWorkerPool,
    ProvisionedWorkerPoolProperties,
    Task,
    TaskGroup,
    WorkerPoolSummary,
    WorkRequirement,
    WorkRequirementSummary,
)

from yd_commands.args import ARGS_PARSER
from yd_commands.compact_json import CompactJSONEncoder
from yd_commands.object_utilities import Item

JSON_INDENT = 2


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


def print_numbered_strings(objects: List[str], override_quiet: bool = False):
    """
    Print a simple list of strings with numbering
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    table = []
    for index, obj in enumerate(objects):
        table.append([index + 1, ":", obj])
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
    return text_indent(txt, prefix=" " * indent_width)


def print_json(
    data: Dict,
    initial_indent: int = 0,
    drop_first_line: bool = False,
    with_final_comma: bool = False,
):
    """
    Print a dictionary as a JSON data structure, using the compact JSON
    encoder.
    """
    json_string = indent(
        json_dumps(data, indent=JSON_INDENT, cls=CompactJSONEncoder), initial_indent
    )
    if drop_first_line:
        json_string = "\n".join(json_string.splitlines()[1:])
    if with_final_comma:
        print(json_string, end=",\n")
    else:
        print(json_string)


def print_yd_object(
    yd_object: object,
    initial_indent: int = 0,
    drop_first_line: bool = False,
    with_final_comma: bool = False,
):
    """
    Print a YellowDog object as a JSON data structure,
    using the compact JSON encoder
    """
    print_json(Json.dump(yd_object), initial_indent, drop_first_line, with_final_comma)


def print_worker_pool(
    crtu: ComputeRequirementTemplateUsage, pwpp: ProvisionedWorkerPoolProperties
):
    """
    Reconstruct and print the JSON-formatted Worker Pool specification.
    """
    print_log("Dry-run: Printing JSON Worker Pool specification")
    wp_data = {
        "provisionedProperties": Json.dump(pwpp),
        "requirementTemplateUsage": Json.dump(crtu),
    }
    print_json(wp_data)
    print_log("Dry run: Complete")


class WorkRequirementSnapshot:
    """
    Represent a complete Work Requirement, with Tasks included within
    Task Group definitions. Note, this is not an 'official' representation
    of a Work Requirement.
    """

    def __init__(self):
        self.wr_data: Dict = {}

    def set_work_requirement(self, wr: WorkRequirement):
        """
        Set the Work Requirement to be represented, processed to
        comply with the API.
        """
        self.wr_data = Json.dump(wr)  # Dictionary holding the complete WR

    def add_tasks(self, task_group_name: str, tasks: List[Task]):
        """
        Add the list of Tasks to a named Task Group within the
        Work Requirement. Cumulative.
        """
        for task_group in self.wr_data["taskGroups"]:
            if task_group["name"] == task_group_name:
                task_group["tasks"] = task_group.get("tasks", [])
                task_group["tasks"] += [Json.dump(task) for task in tasks]
                return

    def print(self):
        """
        Print the JSON representation
        """
        print_log("Dry-run: Printing JSON Work Requirement specification:")
        print_json(self.wr_data)
        print_log("Dry-run: Complete")
