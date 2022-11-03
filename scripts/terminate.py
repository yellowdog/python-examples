#!/usr/bin/env python3

"""
An example script to terminate Compute Requirements.
"""

from typing import List

from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementStatus,
    ComputeRequirementSummary,
)

from common import ConfigCommon, link_entity, load_config_common, print_log
from interactive import confirmed, select
from wrapper import CLIENT, main_wrapper

# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()


@main_wrapper
def main():
    print_log(
        f"Terminating Compute Requirements matching "
        f"'namespace={CONFIG_COMMON.namespace}' and "
        f"'tag={CONFIG_COMMON.name_tag}'"
    )
    compute_requirement_summaries: List[
        ComputeRequirementSummary
    ] = CLIENT.compute_client.find_all_compute_requirements()
    terminated_count = 0
    selected_compute_requirement_summaries: List[ComputeRequirementSummary] = []

    for compute_summary in compute_requirement_summaries:
        if (
            compute_summary.tag == CONFIG_COMMON.name_tag
            and compute_summary.namespace == CONFIG_COMMON.namespace
            and compute_summary.status
            not in [
                ComputeRequirementStatus.TERMINATED,
                ComputeRequirementStatus.TERMINATING,
            ]
        ):
            selected_compute_requirement_summaries.append(compute_summary)

    if len(selected_compute_requirement_summaries) != 0:
        selected_compute_requirement_summaries = select(
            selected_compute_requirement_summaries
        )

    if len(selected_compute_requirement_summaries) != 0 and confirmed(
        f"Terminate {len(selected_compute_requirement_summaries)} "
        "Compute Requirement(s)?"
    ):
        for compute_summary in selected_compute_requirement_summaries:
            if (
                compute_summary.tag == CONFIG_COMMON.name_tag
                and compute_summary.namespace == CONFIG_COMMON.namespace
                and compute_summary.status
                not in [
                    ComputeRequirementStatus.TERMINATED,
                    ComputeRequirementStatus.TERMINATING,
                ]
            ):
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
    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
    else:
        print_log("Nothing to terminate")


# Entry point
if __name__ == "__main__":
    main()
