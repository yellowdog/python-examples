#!/usr/bin/env python3

"""
A script to start held Work Requirements.
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
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if len(ARGS_PARSER.work_requirement_names) > 0:
        start_work_requirements_by_name_or_id(ARGS_PARSER.work_requirement_names)
        return

    print_log(
        "Starting Work Requirements with "
        f"'{CONFIG_COMMON.namespace}' in namespace and "
        f"'{CONFIG_COMMON.name_tag}' in tag"
    )

    selected_work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            client=CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            include_filter=[WorkRequirementStatus.HELD],
        )
    )

    started_count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Start {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status == WorkRequirementStatus.HELD:
                CLIENT.work_client.start_work_requirement_by_id(work_summary.id)
                work_requirement: WorkRequirement = (
                    CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                )
                started_count += 1
                print_log(
                    f"Starting {link_entity(CONFIG_COMMON.url, work_requirement)} "
                    f"({work_summary.name})"
                )
            work_requirement_ids.append(work_summary.id)
        if started_count > 0:
            print_log(f"Started {started_count} Work Requirement(s)")

    else:
        print_log("No Work Requirements to start")


def start_work_requirements_by_name_or_id(names_or_ids: List[str]):
    """
    Start a held Work Requirement by its name or ID.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = []
    for name_or_id in names_or_ids:
        work_requirement_summary: WorkRequirementSummary = (
            get_work_requirement_summary_by_name_or_id(CLIENT, name_or_id)
        )
        if work_requirement_summary is None:
            print_error(f"Work Requirement '{name_or_id}' not found")
            continue

        if work_requirement_summary.status != WorkRequirementStatus.HELD:
            print_warning(
                f"Work Requirement '{name_or_id}' is not in a 'HELD' state; not starting"
            )
            continue

        work_requirement_summaries.append(work_requirement_summary)
        if not confirmed(f"Start Work Requirement '{name_or_id}'?"):
            return
        try:
            CLIENT.work_client.start_work_requirement_by_id(work_requirement_summary.id)
            print_log(f"Started Work Requirement '{name_or_id}'")
        except Exception as e:
            raise Exception(f"Failed to start Work Requirement '{name_or_id}': {e}")


# Entry point
if __name__ == "__main__":
    main()
