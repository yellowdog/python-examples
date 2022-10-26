#!/usr/bin/env python3

"""
An example script to cancel Work Requirements.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ServicesSchema,
    Task,
    TaskSearch,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from common import ARGS_PARSER, ConfigCommon, link_entity, load_config_common, print_log

# Import the configuration from the TOML file
CONFIG: ConfigCommon = load_config_common()

CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main():
    try:
        print_log(
            f"Cancelling Work Requirements matching NAMESPACE={CONFIG.namespace} "
            f"and with TAG={CONFIG.name_tag}"
        )
        work_requirement_summaries: List[
            WorkRequirementSummary
        ] = CLIENT.work_client.find_all_work_requirements()
        cancelled_count = 0
        cancelling_count = 0
        for work_summary in work_requirement_summaries:
            if (
                work_summary.tag == CONFIG.name_tag
                and work_summary.namespace == CONFIG.namespace
                and work_summary.status
                not in [
                    WorkRequirementStatus.COMPLETED,
                    WorkRequirementStatus.CANCELLED,
                    WorkRequirementStatus.FAILED,
                ]
            ):
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
                else:
                    print_log(
                        f"Work Requirement '{work_summary.name}' "
                        f"is already cancelling"
                    )
                    cancelling_count += 1
        if cancelled_count > 0:
            print_log(f"Cancelled {cancelled_count} Work Requirement(s)")
        elif cancelling_count == 0:
            print_log("No Work Requirements to cancel")

        if ARGS_PARSER.abort:
            print_log("Aborting all currently running Tasks")
            abort_all_tasks()

        CLIENT.close()
    except Exception as e:
        print_log(f"Exception: {e}")
    print_log("Done")


def abort_all_tasks() -> None:
    """
    Abort all Tasks in CANCELLING Work Requirements.
    """

    def _task_group_name(wr_summary: WorkRequirementSummary, task: Task) -> str:
        """
        Helper function to find the Task Group Name for a given Task
        within a Work Requirement.
        """
        task_group_name = ""
        for task_group in CLIENT.work_client.get_work_requirement_by_id(
            wr_summary.id
        ).taskGroups:
            if task.taskGroupId == task_group.id:
                return task_group.name
        else:
            return task_group_name

    for wr_summary in CLIENT.work_client.find_all_work_requirements():
        if (
            wr_summary.tag == CONFIG.name_tag
            and wr_summary.namespace == CONFIG.namespace
            and wr_summary.status == WorkRequirementStatus.CANCELLING
        ):
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
                except Exception as e:
                    print_log(f"Error: {e}")
                    continue


# Entry point
if __name__ == "__main__":
    main()
