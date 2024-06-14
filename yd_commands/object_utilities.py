"""
Various utility functions for finding objects, etc.
"""

from functools import lru_cache
from typing import List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    AllowanceSearch,
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplateSummary,
    MachineImageFamilySearch,
    MachineImageFamilySummary,
    ObjectPath,
    ObjectPathsRequest,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    TaskSearch,
    WorkerPool,
    WorkerPoolSummary,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_log


@lru_cache()
def get_task_groups_from_wr_summary(
    client: PlatformClient, wr_summary_id: str
) -> List[TaskGroup]:
    """
    Get the list of the Work Requirement's Task Groups.
    Cache results to avoid repeatedly hitting the API for the same thing.
    """
    work_requirement = client.work_client.get_work_requirement_by_id(wr_summary_id)
    return work_requirement.taskGroups


def get_task_group_name(
    client: PlatformClient, wr_summary: WorkRequirementSummary, task: Task
) -> str:
    """
    Function to find the Task Group Name for a given Task
    within a Work Requirement.
    """
    for task_group in get_task_groups_from_wr_summary(client, wr_summary.id):
        if task.taskGroupId == task_group.id:
            return task_group.name
    return ""  # Shouldn't get here


def get_filtered_work_requirements(
    client: PlatformClient,
    namespace: str,
    tag: str,
    include_filter: Optional[List[WorkRequirementStatus]] = None,
    exclude_filter: Optional[List[WorkRequirementStatus]] = None,
) -> List[WorkRequirementSummary]:
    """
    Get a list of Work Requirements filtered by namespace, tag
    and status. Populate either include_filter OR exclude_filter
    """
    filtered_work_summaries: List[WorkRequirementSummary] = []

    work_requirement_summaries: List[WorkRequirementSummary] = (
        client.work_client.find_all_work_requirements()
    )

    for work_summary in work_requirement_summaries:
        work_summary.tag = "" if work_summary.tag is None else work_summary.tag
        work_summary.namespace = (
            "" if work_summary.namespace is None else work_summary.namespace
        )
        if namespace in work_summary.namespace and tag in work_summary.tag:
            if include_filter is not None:
                if work_summary.status in include_filter:
                    filtered_work_summaries.append(work_summary)
                    continue
            if exclude_filter is not None:
                if work_summary.status not in exclude_filter:
                    filtered_work_summaries.append(work_summary)
                    continue

    return filtered_work_summaries


@lru_cache()
def get_worker_pool_by_id(client: PlatformClient, worker_pool_id: str) -> WorkerPool:
    """
    Pass-through function to cache results.
    """
    return client.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id=worker_pool_id
    )


def get_worker_pool_id_by_name(
    client: PlatformClient, worker_pool_name: str
) -> Optional[str]:
    """
    Find a Worker Pool ID by its name.
    """
    worker_pool_summaries: List[WorkerPoolSummary] = (
        client.worker_pool_client.find_all_worker_pools()
    )
    for wp_summary in worker_pool_summaries:
        if wp_summary.name == worker_pool_name:
            return wp_summary.id


def get_compute_requirement_id_by_name(
    client: PlatformClient,
    compute_requirement_name: str,
    statuses: List[ComputeRequirementStatus],
) -> Optional[str]:
    """
    Find a Compute Requirement ID by its name.
    Restrict search by status.
    """
    cr_search = ComputeRequirementSearch(statuses=statuses)
    search_client: SearchClient = client.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    for compute_requirement in compute_requirements:
        if compute_requirement.name == compute_requirement_name:
            return compute_requirement.id


def get_work_requirement_summary_by_name_or_id(
    client: PlatformClient, work_requirement_name_or_id: str
) -> Optional[WorkRequirementSummary]:
    """
    Get a Work Requirement Summary by its name or ID.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = (
        client.work_client.find_all_work_requirements()
    )
    for work_requirement_summary in work_requirement_summaries:
        if (
            work_requirement_summary.name == work_requirement_name_or_id
            or work_requirement_summary.id == work_requirement_name_or_id
        ):
            return work_requirement_summary


def find_compute_source_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find a Compute Source Template id by name.
    Compute Source Template names are unique.
    """
    for source in get_all_compute_source_templates(client):
        if source.name == name:
            return source.id


@lru_cache()
def get_all_compute_source_templates(
    client: PlatformClient,
) -> List[ComputeSourceTemplateSummary]:
    """
    Cache the list of Sources.
    """
    return client.compute_client.find_all_compute_source_templates()


def clear_compute_source_template_cache():
    """
    Clear the cache of Compute Source Templates.
    """
    get_all_compute_source_templates.cache_clear()


def find_compute_requirement_template_ids_by_name(
    client: PlatformClient, name: str
) -> List[str]:
    """
    Find Compute Template IDs that match the provided name.
    (Compute Requirement Template names don't currently need
    to be unique.)
    """
    compute_template_ids = []
    for template in get_all_compute_requirement_templates(client):
        if template.name == name:
            compute_template_ids.append(template.id)
    return compute_template_ids


@lru_cache()
def get_all_compute_requirement_templates(
    client: PlatformClient,
) -> List[ComputeRequirementTemplateSummary]:
    """
    Cache the list of Compute Requirement Templates.
    """
    return client.compute_client.find_all_compute_requirement_templates()


def clear_compute_requirement_template_cache():
    """
    Clear the cache of Compute Requirement Templates.
    """
    get_all_compute_requirement_templates.cache_clear()


def get_compute_requirement_id_by_worker_pool_id(
    client: PlatformClient, worker_pool_id: str
) -> Optional[str]:
    """
    Get a Compute Requirement ID from a Provisioned Worker Pool ID.
    """
    worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id
    )
    if isinstance(worker_pool, ProvisionedWorkerPool):
        return worker_pool.computeRequirementId


@lru_cache()
def find_image_family_ids_by_name(
    client: PlatformClient, image_family_name
) -> List[str]:
    """
    Find image family IDs by their name.
    """
    if_search = MachineImageFamilySearch(
        familyName=image_family_name, includePublic=True
    )
    search_client: SearchClient = client.images_client.get_image_families(if_search)
    image_families: List[MachineImageFamilySummary] = search_client.list_all()

    return [
        image_family.id
        for image_family in image_families
        if image_family.name == image_family_name
    ]


def clear_image_family_search_cache():
    """
    Clear the cache of Image Family name searches.
    """
    find_image_family_ids_by_name.cache_clear()


def remove_allowances_matching_description(
    client: PlatformClient, description: str
) -> int:
    """
    Remove Allowances that match on the description property.
    Return the number of allowances removed.
    """
    allowances = client.allowances_client.get_allowances(
        AllowanceSearch(description=description)
    ).list_all()

    if len(allowances) > 1:
        print_log(f"Multiple Allowances match the description '{description}'")
        print_log("Please select which Allowance(s) to remove")
        allowances = select(
            client=client,
            objects=allowances,
            object_type_name="Allowance",
            single_result=False,
            force_interactive=True,
        )

    for allowance in allowances:
        if confirmed(f"Remove Allowance with YellowDog ID {allowance.id}?"):
            client.allowances_client.delete_allowance_by_id(allowance.id)
            print_log(f"Removed Allowance with YellowDog ID {allowance.id}")

    return len(allowances)


def list_matching_object_paths(
    client: PlatformClient, namespace: str, prefix: str, flat: bool
) -> List[ObjectPath]:
    """
    List object paths matching the namespace and starting with the prefix.
    """
    object_paths: List[ObjectPath] = (
        client.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(namespace=namespace, prefix=prefix, flat=flat)
        )
    )

    if object_paths is None:
        return []

    # Check the prefix actually matches!
    return [
        object_path
        for object_path in object_paths
        if object_path.name.startswith(prefix)
    ]


def get_task_by_id(
    client: PlatformClient, wr_id: str, task_group_id: str, task_id: str
) -> Optional[Task]:
    """
    Find a task by its ID.
    """
    tasks: List[Task] = get_tasks(client, wr_id, task_group_id)
    for task in tasks:
        if task.id == task_id:
            return task


@lru_cache()
def get_tasks(client: PlatformClient, wr_id: str, task_group_id: str) -> List[Task]:
    """
    Return all the tasks in a task group, with caching.
    There is no native way to search for a task by its id.
    """
    task_search = TaskSearch(
        workRequirementId=wr_id,
        taskGroupId=task_group_id,
    )
    tasks: List[Task] = client.work_client.find_tasks(task_search)
    return tasks
