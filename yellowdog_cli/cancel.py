#!/usr/bin/env python3

"""
A script to cancel Work Requirements and optionally abort Tasks.
"""

from typing import List

from yellowdog_client.model import (
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yellowdog_cli.utils.entity_utils import (
    get_filtered_work_requirements,
    get_work_requirement_summary_by_name_or_id,
)
from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import link_entity
from yellowdog_cli.utils.printing import print_error, print_log, print_warning
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


@main_wrapper
def main():
    if len(ARGS_PARSER.work_requirement_names) > 0:
        _cancel_work_requirements_by_name_or_id(ARGS_PARSER.work_requirement_names)
        return

    print_log(
        "Cancelling Work Requirements with "
        f"'{CONFIG_COMMON.namespace}' in namespace and "
        f"'{CONFIG_COMMON.name_tag}' in tag"
    )

    selected_work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            client=CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=[
                WorkRequirementStatus.COMPLETED,
                WorkRequirementStatus.CANCELLED,
                WorkRequirementStatus.FAILED,
            ],
        )
    )

    cancelled_count = 0
    cancelling_count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Cancel {len(selected_work_requirement_summaries)} "
        f"Work Requirement(s)"
        f"{'' if not ARGS_PARSER.abort else ' and abort all allocated tasks'}?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status != WorkRequirementStatus.CANCELLING:
                try:
                    CLIENT.work_client.cancel_work_requirement_by_id(
                        work_summary.id, ARGS_PARSER.abort
                    )
                    work_requirement: WorkRequirement = (
                        CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                    )
                    cancelled_count += 1
                    print_log(
                        f"Cancelled {link_entity(CONFIG_COMMON.url, work_requirement)} "
                        f"('{work_summary.name}')"
                        f"{'' if not ARGS_PARSER.abort else ' and aborted all allocated tasks'}"
                    )

                except Exception as e:
                    print_error(
                        f"Failed to cancel Work Requirement '{work_summary.name}': {e}"
                    )

            elif work_summary.status == WorkRequirementStatus.CANCELLING:
                print_log(
                    f"Work Requirement '{work_summary.name}' is already cancelling"
                )
                cancelling_count += 1
            work_requirement_ids.append(work_summary.id)

        if cancelled_count > 1:
            print_log(f"Cancelled {cancelled_count} Work Requirement(s)")
        elif cancelled_count == 0 and cancelling_count == 0:
            print_log("No Work Requirements to cancel")

        if ARGS_PARSER.follow:
            follow_ids(work_requirement_ids)

    else:
        print_log("No Work Requirements to cancel")


def _cancel_work_requirements_by_name_or_id(names_or_ids: List[str]):
    """
    Cancel Work Requirements by their names or IDs.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = []

    for name_or_id in names_or_ids:

        # Handle a task ID
        if get_ydid_type(name_or_id) == YDIDType.TASK:
            if not confirmed(
                f"Cancel {'' if not ARGS_PARSER.abort else 'and abort '}"
                f"Task '{name_or_id}'?"
            ):
                continue
            try:
                CLIENT.work_client.cancel_task_by_id(name_or_id, ARGS_PARSER.abort)
            except Exception as e:
                print_error(f"Failed to cancel Task '{name_or_id}': {e}")
            continue

        work_requirement_summary: WorkRequirementSummary = (
            get_work_requirement_summary_by_name_or_id(CLIENT, name_or_id)
        )
        if work_requirement_summary is None:
            print_error(f"Work Requirement '{name_or_id}' not found")
            continue

        if work_requirement_summary.status not in [
            WorkRequirementStatus.RUNNING,
            WorkRequirementStatus.HELD,
        ]:
            print_warning(
                f"Work Requirement '{name_or_id}' is not in a valid state"
                f" ('{work_requirement_summary.status}') for cancellation"
            )
            continue

        work_requirement_summaries.append(work_requirement_summary)
        if work_requirement_summary.status == WorkRequirementStatus.CANCELLING:
            print_log(f"Work Requirement '{name_or_id}' is already cancelling")
        else:
            if not confirmed(
                f"Cancel Work Requirement '{name_or_id}'"
                f"{'' if not ARGS_PARSER.abort else ' and abort all allocated tasks'}?"
            ):
                continue
            try:
                CLIENT.work_client.cancel_work_requirement_by_id(
                    work_requirement_summary.id, ARGS_PARSER.abort
                )
                print_log(
                    f"Cancelled Work Requirement '{name_or_id}'"
                    f"{'' if not ARGS_PARSER.abort else ' and aborted all allocated tasks'}"
                )
            except Exception as e:
                print_error(f"Failed to cancel Work Requirement '{name_or_id}': {e}")

    if ARGS_PARSER.follow:
        follow_ids([wrs.id for wrs in work_requirement_summaries])


# Entry point
if __name__ == "__main__":
    main()
