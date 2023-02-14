#!/usr/bin/env python3

"""
A script to cancel Work Requirements and optionally abort Tasks.
"""

from time import sleep
from typing import List

from yellowdog_client.model import (
    Task,
    TaskSearch,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yd_commands.args import ARGS_PARSER
from yd_commands.config import link_entity
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_group_name,
)
from yd_commands.printing import print_log
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Cancelling Work Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"tag starting with '{CONFIG_COMMON.name_tag}'"
    )

    selected_work_requirement_summaries: List[
        WorkRequirementSummary
    ] = get_filtered_work_requirements(
        client=CLIENT,
        namespace=CONFIG_COMMON.namespace,
        tag=CONFIG_COMMON.name_tag,
        exclude_filter=[
            WorkRequirementStatus.COMPLETED,
            WorkRequirementStatus.CANCELLED,
            WorkRequirementStatus.FAILED,
        ],
    )

    cancelled_count = 0
    cancelling_count = 0

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Cancel {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status != WorkRequirementStatus.CANCELLING:
                CLIENT.work_client.cancel_work_requirement_by_id(work_summary.id)
                work_requirement: WorkRequirement = (
                    CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                )
                cancelled_count += 1
                print_log(
                    f"Cancelling {link_entity(CONFIG_COMMON.url, work_requirement)} "
                    f"({work_summary.name})"
                )
            elif work_summary.status == WorkRequirementStatus.CANCELLING:
                print_log(
                    f"Work Requirement '{work_summary.name}' is already cancelling"
                )
                cancelling_count += 1
        if cancelled_count > 0:
            print_log(f"Cancelled {cancelled_count} Work Requirement(s)")
        elif cancelling_count == 0:
            print_log("No Work Requirements to cancel")

        if ARGS_PARSER.abort:
            if cancelled_count == 0 and cancelling_count == 0:
                print_log("No Tasks to abort")
            else:
                print_log("Aborting all currently running Tasks")
                abort_attempts = 12
                for attempt in range(1, abort_attempts + 1):
                    print_log(
                        f"Collecting Tasks to abort (attempt {attempt}/{abort_attempts})"
                    )
                    if abort_all_tasks(selected_work_requirement_summaries) == 0:
                        break
                    sleep(5)

    else:
        print_log("No Work Requirements to cancel")


def abort_all_tasks(
    selected_work_requirement_summaries: List[WorkRequirementSummary],
) -> int:
    """
    Abort all Tasks in CANCELLING Work Requirements.
    """
    aborted_tasks = 0
    for wr_summary in get_filtered_work_requirements(
        client=CLIENT,
        namespace=CONFIG_COMMON.namespace,
        tag=CONFIG_COMMON.name_tag,
        include_filter=[WorkRequirementStatus.CANCELLING],
    ):
        if wr_summary.id in [x.id for x in selected_work_requirement_summaries]:
            task_search = TaskSearch(
                workRequirementId=wr_summary.id,
                statuses=[TaskStatus.EXECUTING],
            )
            tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
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
                    print_log(f"Error: {e}")
                    continue
    if aborted_tasks == 0:
        print_log("No Tasks to abort")
    else:
        print_log(f"Aborted {aborted_tasks} Task(s)")
    return aborted_tasks


# Entry point
if __name__ == "__main__":
    main()
