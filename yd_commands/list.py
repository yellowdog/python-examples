#!/usr/bin/env python3

"""
Command to list YellowDog entities.
"""

from typing import List

from requests import HTTPError
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    ObjectDetail,
    ObjectPath,
    ObjectPathsRequest,
    Task,
    TaskGroup,
    TaskSearch,
    WorkerPool,
    WorkerPoolStatus,
    WorkerPoolSummary,
    WorkRequirementStatus,
    WorkRequirementSummary,
)
from yellowdog_client.model.exceptions import ObjectNotFoundException

from yd_commands.args import ARGS_PARSER
from yd_commands.config import unpack_namespace_in_prefix
from yd_commands.interactive import select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_groups_from_wr_summary,
)
from yd_commands.printing import (
    print_log,
    print_numbered_object_list,
    print_object_detail,
    sorted_objects,
)
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


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

    if ARGS_PARSER.worker_pools:
        list_worker_pools()

    if ARGS_PARSER.compute_requirements:
        list_compute_requirements()


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
        or ARGS_PARSER.compute_requirements
    )


def list_work_requirements():
    """
    List Work Requirements whenever --work-requirements, --task-groups or
    --tasks are selected.

    This function falls through from WRs to TGs to Tasks, depending on the
    options chosen.
    """
    print_log(
        (
            f"Listing Work Requirements in 'namespace={CONFIG_COMMON.namespace}' "
            f"and names starting with 'tag={CONFIG_COMMON.name_tag}'"
        ),
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
    work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=exclude_filter,
        )
    )
    work_requirement_summaries = sorted_objects(work_requirement_summaries)
    if not (ARGS_PARSER.task_groups or ARGS_PARSER.tasks):
        print_numbered_object_list(CLIENT, work_requirement_summaries)
    else:
        selected_work_summaries = select(
            CLIENT, work_requirement_summaries, single_result=True
        )
        for work_summary in selected_work_summaries:
            print_log(f"Work Requirement {work_summary.name}")
            list_task_groups(work_summary)


def list_task_groups(work_summary: WorkRequirementSummary):
    task_groups: List[TaskGroup] = get_task_groups_from_wr_summary(
        CLIENT, work_summary.id
    )
    task_groups = sorted_objects(task_groups)
    if not ARGS_PARSER.tasks:
        print_numbered_object_list(CLIENT, task_groups)
    else:
        task_groups = select(CLIENT, task_groups, single_result=True)
        for task_group in task_groups:
            list_tasks(task_group, work_summary)


def list_tasks(task_group: TaskGroup, work_summary: WorkRequirementSummary):
    task_search = TaskSearch(
        workRequirementId=work_summary.id,
        taskGroupId=task_group.id,
    )
    tasks: List[Task] = CLIENT.work_client.find_tasks(task_search)
    tasks = sorted_objects(tasks)
    print_numbered_object_list(CLIENT, tasks, parent=work_summary)


def list_object_paths():
    namespace, tag = unpack_namespace_in_prefix(
        CONFIG_COMMON.namespace, CONFIG_COMMON.name_tag
    )
    print_log(
        f"Listing Object Paths in namespace '{namespace}' and "
        f"names starting with '{tag}'"
    )
    if ARGS_PARSER.all and not ARGS_PARSER.details:
        print_log("Listing all Objects")
    object_paths: List[ObjectPath] = (
        CLIENT.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(
                namespace=namespace,
                prefix=tag,
                flat=ARGS_PARSER.all,
            )
        )
    )
    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(object_paths))
        return

    # Print object details for selected objects
    # Skip interactive selection if there are five or fewer results
    if len(object_paths) > 5:
        object_paths = select(CLIENT, object_paths, override_quiet=True)
    if len(object_paths) != 0:
        print_log(f"Showing Object details for {len(object_paths)} Object(s)")
    for index, object_path in enumerate(object_paths):
        try:
            if index == 0:
                print()
            object_detail: ObjectDetail = CLIENT.object_store_client.get_object_detail(
                namespace=namespace, name=object_path.name
            )
            print_object_detail(object_detail)
        except ObjectNotFoundException:
            print_log(f"Note: '{object_path.name}' is a prefix not an object")
        print()


def list_worker_pools():
    print_log(
        "Listing Provisioned Worker Pools with Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"names starting with '{CONFIG_COMMON.name_tag}'"
    )
    worker_pool_summaries: List[WorkerPoolSummary] = (
        CLIENT.worker_pool_client.find_all_worker_pools()
    )

    selected_worker_pool_summaries: List[WorkerPoolSummary] = []
    excluded_states = (
        [WorkerPoolStatus.TERMINATED, WorkerPoolStatus.SHUTDOWN]
        if ARGS_PARSER.live_only
        else []
    )
    for worker_pool_summary in worker_pool_summaries:
        if (
            "ProvisionedWorkerPool" in worker_pool_summary.type
            and not worker_pool_summary.status in excluded_states
        ):
            worker_pool: WorkerPool = CLIENT.worker_pool_client.get_worker_pool_by_id(
                worker_pool_summary.id
            )
            try:
                compute_requirement: ComputeRequirement = (
                    CLIENT.compute_client.get_compute_requirement_by_id(
                        worker_pool.computeRequirementId
                    )
                )
            except HTTPError:
                continue
            if compute_requirement.tag is not None:
                if (
                    compute_requirement.tag.startswith(CONFIG_COMMON.name_tag)
                    and compute_requirement.namespace == CONFIG_COMMON.namespace
                ):
                    selected_worker_pool_summaries.append(worker_pool_summary)
            else:
                selected_worker_pool_summaries.append(worker_pool_summary)

    selected_worker_pool_summaries = sorted_objects(selected_worker_pool_summaries)
    print_numbered_object_list(CLIENT, selected_worker_pool_summaries)


def list_compute_requirements():
    print_log(
        "Listing Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f" names starting with '{CONFIG_COMMON.name_tag}'"
    )

    cr_search = ComputeRequirementSearch(
        namespace=CONFIG_COMMON.namespace,
    )
    search_client: SearchClient = CLIENT.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    filtered_compute_requirements: List[ComputeRequirement] = []
    excluded_states = (
        [ComputeRequirementStatus.TERMINATED, ComputeRequirementStatus.TERMINATING]
        if ARGS_PARSER.live_only
        else []
    )
    for compute_requirement in compute_requirements:
        compute_requirement.tag = (
            "" if compute_requirement.tag is None else compute_requirement.tag
        )
        if (
            compute_requirement.tag.startswith(CONFIG_COMMON.name_tag)
            and compute_requirement.namespace == CONFIG_COMMON.namespace
            and compute_requirement.status not in excluded_states
        ):
            filtered_compute_requirements.append(compute_requirement)

    print_numbered_object_list(
        CLIENT,
        sorted_objects(filtered_compute_requirements),
    )


# Entry point
if __name__ == "__main__":
    main()
