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
from yd_commands.printing import print_error, print_log, sorted_objects
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
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
    aborted_tasks = 0
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
    if len(tasks) != 0 and confirmed(f"Abort {len(tasks)} Tasks?"):
        for task in tasks:
            try:
                CLIENT.work_client.cancel_task(task, abort=True)
                print_log(
                    f"Aborting Task '{task.name}' in Task Group"
                    f" '{get_task_group_name(CLIENT, wr_summary, task)}' in Work"
                    f" Requirement '{wr_summary.name}'"
                )
                aborted_tasks += 1
            except Exception as e:
                print_error(e)
                continue
    if aborted_tasks == 0:
        print_log("No Tasks Aborted")
    else:
        print_log(f"Aborted {aborted_tasks} Task(s)")


# Entry point
if __name__ == "__main__":
    main()
