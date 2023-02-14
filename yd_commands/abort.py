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

from yd_commands.config import ARGS_PARSER
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_group_name,
)
from yd_commands.printing import print_error, print_log, sorted_objects
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Finding Work Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"tag starting with '{CONFIG_COMMON.name_tag}'"
    )

    # Abort Tasks is always interactive
    ARGS_PARSER.interactive = True

    selected_work_requirement_summaries: List[
        WorkRequirementSummary
    ] = get_filtered_work_requirements(
        CLIENT,
        namespace=CONFIG_COMMON.namespace,
        tag=CONFIG_COMMON.name_tag,
        exclude_filter=[
            WorkRequirementStatus.COMPLETED,
            WorkRequirementStatus.CANCELLED,
            WorkRequirementStatus.FAILED,
        ],
    )

    if len(selected_work_requirement_summaries) != 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries, override_quiet=True
        )
    else:
        print_log("No matching Work Requirements found")

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
        print_log(
            f"Aborting Tasks in Work Requirement '{wr_summary.name}'",
            override_quiet=True,
        )
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
                "No currently running Tasks in this Work Requirement",
                override_quiet=True,
            )
        if len(tasks) != 0 and confirmed(f"Abort {len(tasks)} Tasks?"):
            for task in tasks:
                try:
                    CLIENT.work_client.cancel_task(task, abort=True)
                    print_log(
                        f"Aborting Task '{task.name}' "
                        f"in Task Group '{get_task_group_name(CLIENT, wr_summary, task)}' "
                        f"in Work Requirement '{wr_summary.name}'"
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
