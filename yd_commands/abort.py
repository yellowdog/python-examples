#!/usr/bin/env python3

"""
A script to abort Tasks without cancelling their Work Requirements.
"""

from typing import List

from yellowdog_client.model import (
    Task,
    TaskSearch,
    TaskStatus,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_group_name,
)
from yd_commands.printing import print_error, print_log, print_warning, sorted_objects
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():

    if len(ARGS_PARSER.task_id_list) > 0:
        _abort_tasks_by_name_or_id(ARGS_PARSER.task_id_list)
        return

    print_log(
        "Finding active Work Requirements with "
        f"'{CONFIG_COMMON.namespace}' in namespace and "
        f"'{CONFIG_COMMON.name_tag}' in tag"
    )

    # Abort Tasks is always interactive
    ARGS_PARSER.interactive = True

    selected_work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=[
                WorkRequirementStatus.COMPLETED,
                WorkRequirementStatus.CANCELLED,
                WorkRequirementStatus.FAILED,
            ],
        )
    )

    if len(selected_work_requirement_summaries) != 0:
        selected_work_requirement_summaries = select(
            CLIENT,
            selected_work_requirement_summaries,
            single_result=True,
            override_quiet=True,
        )
    else:
        print_log("No matching Work Requirements found")

    if len(selected_work_requirement_summaries) == 1:
        abort_tasks_selectively(selected_work_requirement_summaries[0])


def abort_tasks_selectively(
    wr_summary: WorkRequirementSummary,
) -> None:
    """
    Abort selected Tasks in a Work Requirements
    """
    print_log(f"Aborting Tasks in Work Requirement '{wr_summary.name}'")

    task_search = TaskSearch(
        workRequirementId=wr_summary.id,
        statuses=[TaskStatus.EXECUTING],
    )
    tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)

    if len(tasks) > 0:
        tasks = select(
            CLIENT, sorted_objects(tasks), parent=wr_summary, override_quiet=True
        )
    else:
        print_log(
            "No currently executing Tasks in this Work Requirement",
            override_quiet=True,
        )

    aborted_tasks = 0
    if len(tasks) != 0 and confirmed(f"Abort {len(tasks)} Task(s)?"):
        for task in tasks:
            try:
                CLIENT.work_client.cancel_task(task, abort=True)
                print_log(
                    f"Aborted Task '{task.name}' in Task Group"
                    f" '{get_task_group_name(CLIENT, wr_summary, task)}' in Work"
                    f" Requirement '{wr_summary.name}'"
                )
                aborted_tasks += 1
            except Exception as e:
                print_error(f"Unable to abort Task '{task.name}': {e}")

    if aborted_tasks == 0:
        print_log("No Tasks Aborted")
    elif aborted_tasks > 1:
        print_log(f"Aborted {aborted_tasks} Tasks")


def _abort_tasks_by_name_or_id(task_id_list: List[str]):
    """
    Abort Tasks by their YDIDs.
    """
    aborted_count = 0
    for task_id in task_id_list:
        if "ydid:task:" not in task_id:
            print_warning(f"ID '{task_id}' is not a valid Task YDID")
            continue

        if not confirmed(f"Cancel and abort Task '{task_id}'?"):
            continue

        try:
            CLIENT.work_client.cancel_task_by_id(task_id, abort=True)
            print_log(f"Cancelled and aborted Task '{task_id}'")
            aborted_count += 1
        except Exception as e:
            print_error(f"Unable to cancel and abort Task '{task_id}': {e}")

    if aborted_count > 1:
        print_log(f"Cancelled and aborted {aborted_count} Tasks")
    elif aborted_count == 0:
        print_log("No Tasks cancelled and aborted")


# Entry point
if __name__ == "__main__":
    main()
