#!/usr/bin/env python3

"""
A script to finish Work Requirements.
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
from yellowdog_cli.utils.printing import print_error, print_info, print_warning
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if len(ARGS_PARSER.work_requirement_names) > 0:
        _finish_work_requirements_by_name_or_id(ARGS_PARSER.work_requirement_names)
        return

    print_info(
        "Finishing Work Requirements in namespace "
        f"'{CONFIG_COMMON.namespace}' with tags "
        f"including '{CONFIG_COMMON.name_tag}'"
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
                WorkRequirementStatus.CANCELLING,
            ],
        )
    )

    finished_count = 0
    finishing_count = 0
    work_requirement_ids: List[str] = []

    if len(selected_work_requirement_summaries) > 0:
        selected_work_requirement_summaries = select(
            CLIENT, selected_work_requirement_summaries
        )

    if len(selected_work_requirement_summaries) > 0 and confirmed(
        f"Finish {len(selected_work_requirement_summaries)} Work Requirement(s)?"
    ):
        for work_summary in selected_work_requirement_summaries:
            if work_summary.status != WorkRequirementStatus.FINISHING:
                try:
                    CLIENT.work_client.finish_work_requirement_by_id(work_summary.id)
                    work_requirement: WorkRequirement = (
                        CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
                    )
                    finished_count += 1
                    print_info(
                        f"Finished {link_entity(CONFIG_COMMON.url, work_requirement)} "
                        f"('{work_summary.name}')"
                    )

                except Exception as e:
                    print_error(
                        f"Failed to finish Work Requirement '{work_summary.name}': {e}"
                    )

            elif work_summary.status == WorkRequirementStatus.FINISHING:
                print_info(
                    f"Work Requirement '{work_summary.name}' is already finishing"
                )
                finishing_count += 1
            work_requirement_ids.append(work_summary.id)

        if finished_count > 1:
            print_info(f"Finished {finished_count} Work Requirement(s)")
        elif finished_count == 0 and finishing_count == 0:
            print_info("No Work Requirements to finish")

        if ARGS_PARSER.follow:
            follow_ids(work_requirement_ids)

    else:
        print_info("No Work Requirements to finish")


def _finish_work_requirements_by_name_or_id(names_or_ids: List[str]):
    """
    Finish Work Requirements by their names or IDs.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = []

    for name_or_id in names_or_ids:

        work_requirement_summary: WorkRequirementSummary = (
            get_work_requirement_summary_by_name_or_id(
                CLIENT,
                name_or_id,
                namespace=CONFIG_COMMON.namespace,
            )
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
                f" ('{work_requirement_summary.status}') to be finished"
            )
            continue

        work_requirement_summaries.append(work_requirement_summary)
        if work_requirement_summary.status == WorkRequirementStatus.FINISHING:
            print_info(f"Work Requirement '{name_or_id}' is already finishing")
        else:
            if not confirmed(f"Finish Work Requirement '{name_or_id}'?"):
                continue
            try:
                CLIENT.work_client.finish_work_requirement_by_id(
                    work_requirement_summary.id
                )
                print_info(f"Finished Work Requirement '{name_or_id}'")
            except Exception as e:
                print_error(f"Failed to finish Work Requirement '{name_or_id}': {e}")

    if ARGS_PARSER.follow:
        follow_ids([wrs.id for wrs in work_requirement_summaries])


# Entry point
if __name__ == "__main__":
    main()
