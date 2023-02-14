#!/usr/bin/env python3

"""
A script to terminate Compute Requirements.
"""

from typing import List

from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementStatus,
    ComputeRequirementSummary,
)

from yd_commands.config import link_entity
from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Terminating Compute Requirements matching "
        f"'namespace={CONFIG_COMMON.namespace}' and tag "
        f"starting with '{CONFIG_COMMON.name_tag}'"
    )

    compute_requirement_summaries: List[
        ComputeRequirementSummary
    ] = CLIENT.compute_client.find_all_compute_requirements()

    terminated_count = 0
    selected_compute_requirement_summaries: List[ComputeRequirementSummary] = []

    for compute_summary in compute_requirement_summaries:
        compute_summary.tag = "" if compute_summary.tag is None else compute_summary.tag
        if (
            compute_summary.tag.startswith(CONFIG_COMMON.name_tag)
            and compute_summary.namespace == CONFIG_COMMON.namespace
            and compute_summary.status
            not in [
                ComputeRequirementStatus.TERMINATED,
                ComputeRequirementStatus.TERMINATING,
            ]
        ):
            selected_compute_requirement_summaries.append(compute_summary)

    if len(selected_compute_requirement_summaries) > 0:
        selected_compute_requirement_summaries = select(
            CLIENT, selected_compute_requirement_summaries
        )

    if len(selected_compute_requirement_summaries) > 0 and confirmed(
        f"Terminate {len(selected_compute_requirement_summaries)} "
        "Compute Requirement(s)?"
    ):
        for compute_summary in selected_compute_requirement_summaries:
            try:
                CLIENT.compute_client.terminate_compute_requirement_by_id(
                    compute_summary.id
                )
                compute_requirement: ComputeRequirement = (
                    CLIENT.compute_client.get_compute_requirement_by_id(
                        compute_summary.id
                    )
                )
                terminated_count += 1
                print_log(
                    f"Terminated {link_entity(CONFIG_COMMON.url, compute_requirement)}"
                )
            except:
                print_error(f"Unable to terminate '{compute_summary.name}'")

    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
    else:
        print_log("No Compute Requirements terminated")


# Entry point
if __name__ == "__main__":
    main()
