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

from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_work_requirement_summary_by_name_or_id,
)
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.utils import link_entity
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON

START_ACTION = "Start"
HOLD_ACTION = "Hold"


def start_work_requirements():
    _start_or_hold_work_requirement(action=START_ACTION)


def hold_work_requirements():
    _start_or_hold_work_requirement(action=HOLD_ACTION)


def _start_or_hold_work_requirement(action: str):

    if action == START_ACTION:
        required_state = WorkRequirementStatus.HELD
        start_or_hold_function = CLIENT.work_client.start_work_requirement_by_id
    else:  # Action == HOLD_ACTION
        required_state = WorkRequirementStatus.RUNNING
        start_or_hold_function = CLIENT.work_client.hold_work_requirement_by_id

    if len(ARGS_PARSER.work_requirement_names) > 0:
        _start_or_hold_work_requirements_by_name_or_id(
            action=action,
            required_state=required_state,
            start_or_hold_function=start_or_hold_function,
            names_or_ids=ARGS_PARSER.work_requirement_names,
        )
        return

    print_log(
        f"Applying action '{action}' to Work Requirements with "
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

    processed_count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Apply action '{action}' to {len(selected_work_requirement_summaries)}"
        " Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status == required_state:
                start_or_hold_function(work_summary.id)
                work_requirement: WorkRequirement = (
                    CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                )
                processed_count += 1
                print_log(
                    f"Applied action '{action}' to {link_entity(CONFIG_COMMON.url, work_requirement)}"
                    f" ({work_summary.name})"
                )
            work_requirement_ids.append(work_summary.id)
        if processed_count > 1:
            print_log(
                f"Applied action '{action}' to {processed_count} Work Requirements"
            )

    else:
        print_log(
            f"No matching Work Requirements eligible for action '{action}'"
            f" (state must be '{required_state}')"
        )


def _start_or_hold_work_requirements_by_name_or_id(
    action: str,
    required_state: WorkRequirementStatus,
    start_or_hold_function: callable,
    names_or_ids: List[str],
):
    """
    Start or hold Work Requirements by their names or IDs.
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

        work_requirement_summaries.append(work_requirement_summary)
        if not confirmed(
            f"Apply action '{action}' to Work Requirement '{name_or_id}'?"
        ):
            continue

        try:
            start_or_hold_function(work_requirement_summary.id)
            print_log(f"Applied action '{action}' to Work Requirement '{name_or_id}'")
        except Exception as e:
            print_error(
                f"Failed to apply action '{action}' to Work Requirement '{name_or_id}': {e}"
            )
            continue
