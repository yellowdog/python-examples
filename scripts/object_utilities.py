from functools import lru_cache
from typing import List, Optional

from yellowdog_client.model import (
    Task,
    TaskGroup,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from wrapper import CLIENT


@lru_cache()
def get_task_groups_from_wr_summary(
    wr_summary_id: str,
) -> List[TaskGroup]:
    """
    Get the list of the Work Requirement's Task Groups.
    Cached results to avoid hitting the API too often
    """
    work_requirement = CLIENT.work_client.get_work_requirement_by_id(wr_summary_id)
    return work_requirement.taskGroups


def get_task_group_name(wr_summary: WorkRequirementSummary, task: Task) -> str:
    """
    Function to find the Task Group Name for a given Task
    within a Work Requirement.
    """
    for task_group in get_task_groups_from_wr_summary(wr_summary.id):
        if task.taskGroupId == task_group.id:
            return task_group.name
    return ""  # Shouldn't get here


def get_filtered_work_requirements(
    namespace: str,
    tag: str,
    include_filter: Optional[List[WorkRequirementStatus]] = None,
    exclude_filter: Optional[List[WorkRequirementStatus]] = None,
) -> List[WorkRequirementSummary]:
    """
    Get a list of Work Requirements filtered by namespace, tag
    and status
    """

    # Avoid mutable keyword argument defaults
    include_filter = [] if include_filter is None else include_filter
    exclude_filter = [] if exclude_filter is None else exclude_filter

    filtered_work_summaries: List[WorkRequirementSummary] = []

    work_requirement_summaries: List[
        WorkRequirementSummary
    ] = CLIENT.work_client.find_all_work_requirements()

    for work_summary in work_requirement_summaries:
        if (
            work_summary.status in include_filter
            or not work_summary.status in exclude_filter
            and work_summary.namespace == namespace
            and work_summary.tag == tag
        ):
            filtered_work_summaries.append(work_summary)

    return filtered_work_summaries
