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

from yd_commands.follow_utils import follow_ids
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_group_name,
    get_work_requirement_summary_by_name_or_id,
)
from yd_commands.printing import print_error, print_log
from yd_commands.settings import TASK_ABORT_CHECK_INTERVAL
from yd_commands.utils import link_entity
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if len(ARGS_PARSER.work_requirement_names) > 0:
        _cancel_work_requirements_by_name_or_id(ARGS_PARSER.work_requirement_names)
        return

    print_log(
        "Cancelling Work Requirements with "
        f"'{CONFIG_COMMON.namespace}' in namespace and "
        f"'{CONFIG_COMMON.name_tag}' in tag"
    )

    selected_work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            client=CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=[
                WorkRequirementStatus.COMPLETED,
                WorkRequirementStatus.CANCELLED,
                WorkRequirementStatus.FAILED,
            ],
        )
    )

    cancelled_count = 0
    cancelling_count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Cancel {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status != WorkRequirementStatus.CANCELLING:
                try:
                    CLIENT.work_client.cancel_work_requirement_by_id(work_summary.id)
                    work_requirement: WorkRequirement = (
                        CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                    )
                    cancelled_count += 1
                    print_log(
                        f"Cancelled {link_entity(CONFIG_COMMON.url, work_requirement)} "
                        f"('{work_summary.name}')"
                    )
                except Exception as e:
                    print_error(
                        f"Failed to cancel Work Requirement '{work_summary.name}': {e}"
                    )

            elif work_summary.status == WorkRequirementStatus.CANCELLING:
                print_log(
                    f"Work Requirement '{work_summary.name}' is already cancelling"
                )
                cancelling_count += 1
            work_requirement_ids.append(work_summary.id)

        if cancelled_count > 1:
            print_log(f"Cancelled {cancelled_count} Work Requirement(s)")
        elif cancelled_count == 0 and cancelling_count == 0:
            print_log("No Work Requirements to cancel")

        if ARGS_PARSER.abort:
            if cancelled_count == 0 and cancelling_count == 0:
                print_log("No Tasks to abort")
            else:
                _abort_and_follow(selected_work_requirement_summaries)

        if ARGS_PARSER.follow:
            follow_ids(work_requirement_ids)

    else:
        print_log("No Work Requirements to cancel")


def _abort_all_tasks(
    selected_work_requirement_summaries: List[WorkRequirementSummary],
) -> int:
    """
    Abort all Tasks in selected Work Requirements.
    """
    aborted_tasks = 0
    for wr_summary in selected_work_requirement_summaries:
        task_search = TaskSearch(
            workRequirementId=wr_summary.id,
            statuses=[
                TaskStatus.EXECUTING,
                TaskStatus.DOWNLOADING,
                TaskStatus.UPLOADING,
            ],
        )
        tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
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
                print_error(f"Error aborting Task '{task.name}': {e}")

    if aborted_tasks == 0:
        print_log("No Tasks to abort")
    if aborted_tasks <= 5:
        pass
    else:
        print_log(f"Aborting {aborted_tasks} Task(s)")
    return aborted_tasks


def _cancel_work_requirements_by_name_or_id(names_or_ids: List[str]):
    """
    Cancel Work Requirements by their names or IDs.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = []
    for name_or_id in names_or_ids:
        work_requirement_summary: WorkRequirementSummary = (
            get_work_requirement_summary_by_name_or_id(CLIENT, name_or_id)
        )
        if work_requirement_summary is None:
            print_error(f"Work Requirement '{name_or_id}' not found")
            continue

        if work_requirement_summary.status not in [
            WorkRequirementStatus.RUNNING,
            WorkRequirementStatus.HELD,
        ]:
            raise Exception(
                f"Work Requirement '{name_or_id}' is not in a valid state"
                f" ('{work_requirement_summary.status}') for cancellation"
            )

        work_requirement_summaries.append(work_requirement_summary)
        if work_requirement_summary.status == WorkRequirementStatus.CANCELLING:
            print_log(f"Work Requirement '{name_or_id}' is already cancelling")
        else:
            if not confirmed(f"Cancel Work Requirement '{name_or_id}'?"):
                continue
            try:
                CLIENT.work_client.cancel_work_requirement_by_id(
                    work_requirement_summary.id
                )
                print_log(f"Cancelled Work Requirement '{name_or_id}'")
            except Exception as e:
                print_error(f"Failed to cancel Work Requirement '{name_or_id}': {e}")

    if ARGS_PARSER.abort:
        _abort_and_follow(work_requirement_summaries)

    if ARGS_PARSER.follow:
        follow_ids([wrs.id for wrs in work_requirement_summaries])


def _abort_and_follow(work_requirement_summaries: List[WorkRequirementSummary]):
    """
    Abort Tasks in one or more Work Requirements and optionally follow
    abort progress.
    """
    if ARGS_PARSER.follow:
        attempt = 0
        while True:
            attempt += 1
            print_log(f"Collecting Tasks to abort (attempt {attempt})")
            if _abort_all_tasks(work_requirement_summaries) == 0:
                break
            print_log(
                f"Waiting {TASK_ABORT_CHECK_INTERVAL}s for abort confirmation ..."
            )
            sleep(TASK_ABORT_CHECK_INTERVAL)
    else:
        print_log("Aborting all currently running Tasks")
        _abort_all_tasks(work_requirement_summaries)


# Entry point
if __name__ == "__main__":
    main()
