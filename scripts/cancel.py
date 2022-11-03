#!/usr/bin/env python3

"""
A script to cancel Work Requirements and optionally abort Tasks.
"""

from typing import List, Optional

from yellowdog_client.model import (
    Task,
    TaskSearch,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from common import ARGS_PARSER, link_entity, print_log
from interactive import confirmed, select
from wrapper import CLIENT, CONFIG, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Cancelling Work Requirements matching 'namespace={CONFIG.namespace}' "
        f"and with 'tag={CONFIG.name_tag}'"
    )

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

    cancelled_count = 0
    cancelling_count = 0

    if len(selected_work_requirement_summaries) != 0:
        selected_work_requirement_summaries = select(
            selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) != 0 and confirmed(
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
                    f"Cancelling {link_entity(CONFIG.url, work_requirement)} "
                    f"({work_summary.name})"
                )
            elif work_summary.status == WorkRequirementStatus.CANCELLING:
                print_log(
                    f"Work Requirement '{work_summary.name} is already cancelling"
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
                abort_all_tasks(selected_work_requirement_summaries)
    else:
        print_log("No Work Requirements to cancel")


def abort_all_tasks(
    selected_work_requirement_summaries: List[WorkRequirementSummary],
) -> None:
    """
    Abort all Tasks in CANCELLING Work Requirements.
    """

    aborted_tasks = 0
    for wr_summary in get_filtered_work_requirements(
        namespace=CONFIG.namespace,
        tag=CONFIG.name_tag,
        include_filter=[WorkRequirementStatus.CANCELLING],
    ):
        if wr_summary.id in [x.id for x in selected_work_requirement_summaries]:
            task_search = TaskSearch(
                workRequirementId=wr_summary.id,
                statuses=[TaskStatus.RUNNING],
            )
            tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
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
        print_log("No Tasks to abort")
    else:
        print_log(f"Aborted {aborted_tasks} Task(s)")


def get_task_group_name(wr_summary: WorkRequirementSummary, task: Task) -> str:
    """
    Function to find the Task Group Name for a given Task
    within a Work Requirement.
    """
    for task_group in CLIENT.work_client.get_work_requirement_by_id(
        wr_summary.id
    ).taskGroups:
        if task.taskGroupId == task_group.id:
            return task_group.name
    return ""  # Shouldn't get here


def get_filtered_work_requirements(
    namespace: str,
    tag: str,
    include_filter: Optional[List[WorkRequirementStatus]] = None,
    exclude_filter: Optional[List[WorkRequirementStatus]] = None,
) -> List[WorkRequirementSummary]:
    """
    Get a list of Work Requirements filtered by namespace, tag
    and status
    """

    # Avoid mutable keyword argument defaults
    include_filter = [] if include_filter is None else include_filter
    exclude_filter = [] if exclude_filter is None else exclude_filter

    filtered_work_summaries: List[WorkRequirementSummary] = []

    work_requirement_summaries: List[
        WorkRequirementSummary
    ] = CLIENT.work_client.find_all_work_requirements()

    for work_summary in work_requirement_summaries:
        if (
            work_summary.status in include_filter
            or not work_summary.status in exclude_filter
            and work_summary.namespace == namespace
            and work_summary.tag == tag
        ):
            filtered_work_summaries.append(work_summary)

    return filtered_work_summaries


# Entry point
if __name__ == "__main__":
    main()
