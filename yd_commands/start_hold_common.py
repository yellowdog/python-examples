#!/usr/bin/env python3

"""
Core functionality for starting and holding Work Requirements.
"""

from typing import List

from yellowdog_client.model import (
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yd_commands.follow_utils import follow_ids
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_work_requirement_summary_by_name_or_id,
)
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.utils import link_entity
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON


def start_work_requirements():
    required_state = WorkRequirementStatus.HELD
    action_function = CLIENT.work_client.start_work_requirement_by_id
    wr_ids = _start_or_hold_work_requirements("Start", required_state, action_function)
    if ARGS_PARSER.follow:
        follow_ids(wr_ids)


def hold_work_requirements():
    required_state = WorkRequirementStatus.RUNNING
    action_function = CLIENT.work_client.hold_work_requirement_by_id
    wr_ids = _start_or_hold_work_requirements("Hold", required_state, action_function)
    if ARGS_PARSER.follow:
        follow_ids(wr_ids)


def _start_or_hold_work_requirements(
    action: str, required_state: WorkRequirementStatus, action_function: callable
) -> List[str]:

    if len(ARGS_PARSER.work_requirement_names) > 0:
        return _start_or_hold_work_requirements_by_name_or_id(
            action=action,
            required_state=required_state,
            action_function=action_function,
            names_or_ids=ARGS_PARSER.work_requirement_names,
        )

    print_log(
        f"{action}ing Work Requirements with "
        f"'{CONFIG_COMMON.namespace}' in namespace and "
        f"'{CONFIG_COMMON.name_tag}' in tag"
    )

    selected_work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            client=CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            include_filter=[required_state],
        )
    )

    count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"{action} {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status == required_state:
                try:
                    action_function(work_summary.id)
                    work_requirement: WorkRequirement = (
                        CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                    )
                    count += 1
                    print_log(
                        f"Applied {action} to "
                        f"{link_entity(CONFIG_COMMON.url, work_requirement)} "
                        f"('{work_summary.name}')"
                    )
                except Exception as e:
                    print_error(
                        f"Failed to {action} Work Requirement '{work_summary.name}': {e}"
                    )
            work_requirement_ids.append(work_summary.id)

        if count > 0:
            print_log(f"{action} applied to {count} Work Requirement(s)")
        else:
            print_log(f"No Work Requirements to {action}")

    else:
        print_log(f"No Work Requirements available to {action}")

    return work_requirement_ids


def _start_or_hold_work_requirements_by_name_or_id(
    action: str,
    required_state: WorkRequirementStatus,
    action_function: callable,
    names_or_ids: List[str],
) -> List[str]:
    """
    Start or hold Work Requirements by their names or IDs.
    Return the list actioned of YDIDs.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = []

    for name_or_id in names_or_ids:
        work_requirement_summary: WorkRequirementSummary = (
            get_work_requirement_summary_by_name_or_id(CLIENT, name_or_id)
        )

        if work_requirement_summary is None:
            print_error(f"Work Requirement '{name_or_id}' not found")
            continue

        if work_requirement_summary.status != required_state:
            print_warning(
                f"Work Requirement '{name_or_id}' is not in the required '{required_state}'"
                f" state for action '{action}'"
            )
            continue

        try:
            action_function(work_requirement_summary.id)
            print_log(f"Applied action '{action}' to Work Requirement '{name_or_id}'")
            work_requirement_summaries.append(work_requirement_summary)
        except Exception as e:
            print_error(
                f"Failed to apply action '{action}' to Work Requirement '{name_or_id}': {e}"
            )

    return [wr.id for wr in work_requirement_summaries]
