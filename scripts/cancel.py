#!/usr/bin/env python3

"""
An example script to cancel Work Requirements.
"""

from typing import List

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
    work_requirement_summaries: List[
        WorkRequirementSummary
    ] = CLIENT.work_client.find_all_work_requirements()
    cancelled_count = 0
    cancelling_count = 0
    selected_work_requirement_summaries: List[WorkRequirementSummary] = []
    ignored_states = [
        WorkRequirementStatus.COMPLETED,
        WorkRequirementStatus.CANCELLED,
        WorkRequirementStatus.FAILED,
    ]
    for work_summary in work_requirement_summaries:
        if (
            work_summary.status not in ignored_states
            and work_summary.tag == CONFIG.name_tag
            and work_summary.namespace == CONFIG.namespace
        ):
            selected_work_requirement_summaries.append(work_summary)

    if len(selected_work_requirement_summaries) != 0:
        selected_work_requirement_summaries = select(
            selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) != 0 and confirmed(
        f"Cancel {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status not in ignored_states + [
                WorkRequirementStatus.CANCELLING
            ]:
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
                    f"Work Requirement '{work_summary.name}' " f"is already cancelling"
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

    def _task_group_name(wr_summary: WorkRequirementSummary, task: Task) -> str:
        """
        Helper function to find the Task Group Name for a given Task
        within a Work Requirement.
        """
        for task_group in CLIENT.work_client.get_work_requirement_by_id(
            wr_summary.id
        ).taskGroups:
            if task.taskGroupId == task_group.id:
                return task_group.name
        return ""  # Shouldn't get here

    aborted_tasks = 0
    for wr_summary in CLIENT.work_client.find_all_work_requirements():
        if (
            wr_summary.tag == CONFIG.name_tag
            and wr_summary.namespace == CONFIG.namespace
            and wr_summary.status == WorkRequirementStatus.CANCELLING
        ) and wr_summary.id in [x.id for x in selected_work_requirement_summaries]:
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
                        f"in Task Group '{_task_group_name(wr_summary, task)}' "
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


# Entry point
if __name__ == "__main__":
    main()
