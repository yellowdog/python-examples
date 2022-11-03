#!/usr/bin/env python3

"""
A script to abort Tasks without cancelling their Work Requirements.
"""

from typing import List, Optional

from yellowdog_client.model import (
    Task,
    TaskSearch,
    TaskStatus,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from cancel import get_filtered_work_requirements, get_task_group_name
from common import ARGS_PARSER, print_log
from interactive import confirmed, select
from wrapper import CLIENT, CONFIG, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Finding Work Requirements matching 'namespace={CONFIG.namespace}' "
        f"and with 'tag={CONFIG.name_tag}'"
    )

    # Abort Tasks is always interactive
    ARGS_PARSER.interactive = True

    selected_work_requirement_summaries: List[
        WorkRequirementSummary
    ] = get_filtered_work_requirements(
        namespace=CONFIG.namespace,
        tag=CONFIG.name_tag,
        exclude_filter=[
            WorkRequirementStatus.COMPLETED,
            WorkRequirementStatus.CANCELLED,
            WorkRequirementStatus.FAILED,
        ],
    )

    if len(selected_work_requirement_summaries) != 0:
        selected_work_requirement_summaries = select(
            selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) != 0:
        abort_tasks_selectively(selected_work_requirement_summaries)


def abort_tasks_selectively(
    selected_work_requirement_summaries: List[WorkRequirementSummary],
) -> None:
    """
    Abort selected Tasks in a list of Work Requirements.
    """
    aborted_tasks = 0
    for wr_summary in selected_work_requirement_summaries:
        print_log(f"Aborting Tasks in Work Requirement '{wr_summary.name}'")
        task_search = TaskSearch(
            workRequirementId=wr_summary.id,
            statuses=[TaskStatus.RUNNING],
        )
        tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
        if len(tasks) > 0:
            tasks = select(tasks)
        else:
            print_log("No running Tasks")
        if len(tasks) != 0 and confirmed(f"Abort {len(tasks)} Tasks?"):
            for task in tasks:
                try:
                    CLIENT.work_client.cancel_task(task, abort=True)
                    print_log(
                        f"Aborting Task '{task.name}' "
                        f"in Task Group '{get_task_group_name(wr_summary, task)}' "
                        f"in Work Requirement '{wr_summary.name}'"
                    )
                    aborted_tasks += 1
                except Exception as e:
                    print_log(f"Error: {e}")
                    continue
    if aborted_tasks == 0:
        print_log("No Tasks Aborted")
    else:
        print_log(f"Aborted {aborted_tasks} Task(s)")


# Entry point
if __name__ == "__main__":
    main()
