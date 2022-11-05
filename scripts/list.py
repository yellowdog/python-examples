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
from interactive import print_numbered_object_list, select, sorted_objects
from object_utilities import (
    get_filtered_work_requirements,
    get_task_groups_from_wr_summary,
)
from printing import print_error, print_log
from wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    """
    If multiple object types are selected, they're all listed.
    """
    if not check_for_valid_option():
        raise Exception("No object type options chosen")

    # Always use interactive mode for selections
    ARGS_PARSER.interactive = True

    if ARGS_PARSER.object_paths:
        list_object_paths()

    if ARGS_PARSER.work_requirements or ARGS_PARSER.task_groups or ARGS_PARSER.tasks:
        list_work_requirements()


def check_for_valid_option() -> bool:
    """
    At least one of the listing options must be selected.
    """
    return (
        ARGS_PARSER.object_paths
        or ARGS_PARSER.work_requirements
        or ARGS_PARSER.task_groups
        or ARGS_PARSER.tasks
        or ARGS_PARSER.worker_pools
        or ARGS_PARSER.compute_requirements)


def list_work_requirements():
    """
    List Work Requirements whenever --work-requirements, --task-groups or
    --tasks are selected.

    This function falls through from WRs to TGs to Tasks, depending on the
    options chosen.
    """
    print_log(
        f"Listing Work Requirements in 'namespace={CONFIG_COMMON.namespace}' "
        f"with 'tag={CONFIG_COMMON.name_tag}'",
        override_quiet=True,
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
    work_requirement_summaries = sorted_objects(work_requirement_summaries)
    if not (ARGS_PARSER.task_groups or ARGS_PARSER.tasks):
        print_numbered_object_list(work_requirement_summaries, override_quiet=True)
    else:
        selected_work_summaries = select(work_requirement_summaries)
        for work_summary in selected_work_summaries:
            print_log(f"Work Requirement {work_summary.name}", override_quiet=True)
            list_task_groups(work_summary)


def list_task_groups(work_summary: WorkRequirementSummary):
    task_groups: List[TaskGroup] = get_task_groups_from_wr_summary(work_summary.id)
    task_groups = sorted_objects(task_groups)
    if not ARGS_PARSER.tasks:
        print_numbered_object_list(task_groups, override_quiet=True)
    else:
        task_groups = select(task_groups, override_quiet=True)
        for task_group in task_groups:
            list_tasks(task_group, work_summary)


def list_tasks(task_group: TaskGroup, work_summary: WorkRequirementSummary):
    task_search = TaskSearch(
        workRequirementId=work_summary.id,
        taskGroupId=task_group.id,
    )
    tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
    tasks = sorted_objects(tasks)
    print_numbered_object_list(tasks, override_quiet=True)


def list_object_paths():
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


# Entry point
if __name__ == "__main__":
    main()
