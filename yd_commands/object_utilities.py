"""
Various utility functions for finding objects, etc.
"""

from functools import lru_cache
from typing import List, Optional, TypeVar

from yellowdog_client import PlatformClient
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    ConfiguredWorkerPool,
    Instance,
    KeyringSummary,
    MachineImageFamilySummary,
    NamespaceStorageConfiguration,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    WorkerPool,
    WorkerPoolSummary,
    WorkRequirementStatus,
    WorkRequirementSummary,
)


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
    and status.
    A WR will match the filter if it's in the included list OR
    if it's not in the excluded list.
    """

    # Avoid mutable keyword argument defaults
    include_filter = [] if include_filter is None else include_filter
    exclude_filter = [] if exclude_filter is None else exclude_filter

    filtered_work_summaries: List[WorkRequirementSummary] = []

    work_requirement_summaries: List[WorkRequirementSummary] = (
        client.work_client.find_all_work_requirements()
    )

    for work_summary in work_requirement_summaries:
        work_summary.tag = "" if work_summary.tag is None else work_summary.tag
        work_summary.namespace = (
            "" if work_summary.namespace is None else work_summary.namespace
        )
        if (
            work_summary.status in include_filter
            or not work_summary.status in exclude_filter
            and namespace in work_summary.namespace
            and tag in work_summary.tag
        ):
            filtered_work_summaries.append(work_summary)

    return filtered_work_summaries


Item = TypeVar(
    "Item",
    ConfiguredWorkerPool,
    ComputeRequirement,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    Instance,
    MachineImageFamilySummary,
    KeyringSummary,
    NamespaceStorageConfiguration,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    WorkerPoolSummary,
    WorkRequirementSummary,
)


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


def find_compute_source_id_by_name(client: PlatformClient, name: str) -> Optional[str]:
    """
    Find a compute source id by its name.
    """
    for source in get_all_compute_sources(client):
        if source.name == name:
            return source.id


@lru_cache()
def get_all_compute_sources(
    client: PlatformClient,
) -> List[ComputeSourceTemplateSummary]:
    """
    Cache the list of Sources.
    """
    return client.compute_client.find_all_compute_source_templates()


def find_compute_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find a Compute Template ID by name.
    """
    for template in get_all_compute_templates(client):
        if template.name == name:
            return template.id


@lru_cache()
def get_all_compute_templates(
    client: PlatformClient,
) -> List[ComputeRequirementTemplateSummary]:
    """
    Cache the list of Compute Templates
    """
    return client.compute_client.find_all_compute_requirement_templates()


def get_compreq_id_by_worker_pool_id(
    client: PlatformClient, worker_pool_id: str
) -> Optional[str]:
    """
    Get a compute requirement ID from a Provisioned Worker Pool ID.
    """
    worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id
    )
    if isinstance(worker_pool, ProvisionedWorkerPool):
        return worker_pool.computeRequirementId
