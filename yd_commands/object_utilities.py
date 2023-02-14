"""
Various utility functions for finding objects, etc.
"""

from functools import lru_cache
from typing import List, Optional, TypeVar

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ComputeRequirementSummary,
    ConfiguredWorkerPool,
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

    work_requirement_summaries: List[
        WorkRequirementSummary
    ] = client.work_client.find_all_work_requirements()

    for work_summary in work_requirement_summaries:
        work_summary.tag = "" if work_summary.tag is None else work_summary.tag
        if (
            work_summary.status in include_filter
            or not work_summary.status in exclude_filter
            and work_summary.namespace == namespace
            and work_summary.tag.startswith(tag)
        ):
            filtered_work_summaries.append(work_summary)

    return filtered_work_summaries


Item = TypeVar(
    "Item",
    ConfiguredWorkerPool,
    ComputeRequirementSummary,
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
