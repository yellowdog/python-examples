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
from yd_commands.settings import NAMESPACE_PREFIX_SEPARATOR


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
    return _find_id_by_name(worker_pool_name, client, get_all_worker_pools)


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


def _find_id_by_name(
    name: str, client: PlatformClient, find_function: callable
) -> Optional[str]:
    """
    Generic function to find an ID of entity by namespace and name.
    """
    ydids = []
    namespaces = []
    namespace, name = split_namespace_and_name(name)
    for entity in find_function(client):
        if entity.name == name:
            if namespace is not None and entity.namespace != namespace:
                continue
            ydids.append(entity.id)
            namespaces.append(entity.namespace)

    if len(ydids) == 0:
        return

    if len(ydids) == 1:
        return ydids[0]

    raise Exception(
        f"Name '{name}' is ambiguous: matching IDs are: {ydids}. "
        f"Please specify a namespace from {namespaces}."
    )


def find_compute_source_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find a Compute Source Template id by name.
    Compute Source Template names are unique within a namespace.
    """
    return _find_id_by_name(name, client, get_all_compute_source_templates)


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


def find_compute_requirement_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find the Compute Requirement Template ID that matches the
    provided name. Names are unique within a namespace.
    """
    return _find_id_by_name(name, client, get_all_compute_requirement_templates)


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


def get_all_worker_pools(client: PlatformClient) -> List[WorkerPoolSummary]:
    """
    Return all Worker Pool summaries.
    """
    return client.worker_pool_client.find_all_worker_pools()


@lru_cache()
def find_image_family_id_by_name(
    client: PlatformClient, image_family_name
) -> Optional[str]:
    """
    Find image family IDs by their name. Names are unique within a namespace.
    """
    namespace, image_family_name = split_namespace_and_name(image_family_name)
    if_search = MachineImageFamilySearch(
        familyName=image_family_name, namespace=namespace, includePublic=True
    )
    search_client: SearchClient = client.images_client.get_image_families(if_search)
    image_families: List[MachineImageFamilySummary] = search_client.list_all()

    # Partial names will match, so filter for exact matches
    image_families = [
        img_family
        for img_family in image_families
        if img_family.name == image_family_name
    ]

    if len(image_families) == 0:
        return
    if len(image_families) == 1:
        return image_families[0].id

    raise Exception(
        f"Ambiguous Image Family name '{image_family_name}': "
        f"{[img_fam.id for img_fam in image_families]}. "
        "Please specify a namespace."
    )


def clear_image_family_search_cache():
    """
    Clear the cache of Image Family name searches.
    """
    find_image_family_id_by_name.cache_clear()


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


def get_non_exact_namespace_matches(
    client: PlatformClient, namespace_to_match: str
) -> List[str]:
    """
    Find namespaces which contain 'namespace_to_match'.
    """
    all_namespaces = client.object_store_client.get_namespaces() + [
        nssc.namespace
        for nssc in client.object_store_client.get_namespace_storage_configurations()
    ]
    matching_namespaces = sorted(
        list(
            {  # Note: use set because duplicate namespaces can be returned
                ns for ns in all_namespaces if namespace_to_match in ns
            }
        )
    )
    return matching_namespaces


def split_namespace_and_name(reference: str) -> (Optional[str], str):
    """
    Split a name into an (optional) namespace and a name.
    """
    parts = reference.split(NAMESPACE_PREFIX_SEPARATOR)
    if len(parts) == 1:
        return None, reference
    if len(parts) == 2:
        return parts[0], parts[1]

    raise Exception(f"Malformed name '{reference}'")
