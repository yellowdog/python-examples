#!/usr/bin/env python3

"""
Command to list YellowDog entities.
"""

from typing import List

from yellowdog_client.model import (
    ObjectPath,
    ObjectPathsRequest,
    Task,
    TaskGroup,
    TaskSearch,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from args import ARGS_PARSER
from interactive import print_numbered_object_list, select
from object_utilities import (
    get_filtered_work_requirements,
    get_task_groups_from_wr_summary,
)
from printing import print_error, print_log
from wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():

    if not (
        ARGS_PARSER.object_paths
        or ARGS_PARSER.work_requirements
        or ARGS_PARSER.task_groups
        or ARGS_PARSER.tasks
        or ARGS_PARSER.worker_pools
        or ARGS_PARSER.compute_requirements
    ):
        raise Exception("No object type options chosen")

    ARGS_PARSER.interactive = True

    if ARGS_PARSER.object_paths:
        print_log(
            f"Listing Object Paths in 'namespace={CONFIG_COMMON.namespace}' with "
            f"names starting with 'tag={CONFIG_COMMON.name_tag}'"
        )
        object_paths: List[
            ObjectPath
        ] = CLIENT.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(CONFIG_COMMON.namespace)
        )
        print_numbered_object_list(object_paths)

    if ARGS_PARSER.work_requirements or ARGS_PARSER.task_groups or ARGS_PARSER.tasks:
        print_log(
            f"Listing Work Requirements in 'namespace={CONFIG_COMMON.namespace}' "
            f"with 'tag={CONFIG_COMMON.name_tag}'"
        )

        exclude_filter = (
            [
                WorkRequirementStatus.COMPLETED,
                WorkRequirementStatus.CANCELLED,
                WorkRequirementStatus.FAILED,
            ]
            if ARGS_PARSER.live_only
            else []
        )

        work_requirement_summaries: List[
            WorkRequirementSummary
        ] = get_filtered_work_requirements(
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=exclude_filter,
        )
        if ARGS_PARSER.task_groups or ARGS_PARSER.tasks:
            selected_work_summaries = select(work_requirement_summaries)
            for work_summary in selected_work_summaries:
                print_log(f"Work Requirement {work_summary.name}", override_quiet=True)
                task_groups: List[TaskGroup] = get_task_groups_from_wr_summary(
                    work_summary.id
                )
                if ARGS_PARSER.tasks:
                    task_search = TaskSearch(
                        workRequirementId=work_summary.id,
                    )
                    tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
                    print_numbered_object_list(
                        sorted(tasks, key=lambda x: x.name), override_quiet=True
                    )
                else:
                    print_numbered_object_list(task_groups, override_quiet=True)
        else:
            print_numbered_object_list(work_requirement_summaries, override_quiet=True)


# Entry point
if __name__ == "__main__":
    main()
