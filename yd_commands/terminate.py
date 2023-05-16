#!/usr/bin/env python3

"""
A script to terminate Compute Requirements.
"""

from typing import List

from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
)

from yd_commands.config import link_entity
from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        "Terminating Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and tag "
        f"starting with '{CONFIG_COMMON.name_tag}'"
    )

    cr_search = ComputeRequirementSearch(
        namespace=CONFIG_COMMON.namespace,
        statuses=[
            ComputeRequirementStatus.NEW,
            ComputeRequirementStatus.PROVISIONING,
            ComputeRequirementStatus.STARTING,
            ComputeRequirementStatus.RUNNING,
            ComputeRequirementStatus.STOPPING,
        ],
        # Excludes TERMINATED, TERMINATING
    )
    search_client: SearchClient = CLIENT.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    terminated_count = 0
    selected_compute_requirements: List[ComputeRequirement] = []

    for compute_requirement in compute_requirements:
        compute_requirement.tag = (
            "" if compute_requirement.tag is None else compute_requirement.tag
        )
        if compute_requirement.tag.startswith(CONFIG_COMMON.name_tag):
            selected_compute_requirements.append(compute_requirement)

    if len(selected_compute_requirements) > 0:
        selected_compute_requirements = select(CLIENT, selected_compute_requirements)

    if len(selected_compute_requirements) > 0 and confirmed(
        f"Terminate {len(selected_compute_requirements)} Compute Requirement(s)?"
    ):
        for compute_requirement in selected_compute_requirements:
            try:
                CLIENT.compute_client.terminate_compute_requirement_by_id(
                    compute_requirement.id
                )
                compute_requirement: ComputeRequirement = (
                    CLIENT.compute_client.get_compute_requirement_by_id(
                        compute_requirement.id
                    )
                )
                terminated_count += 1
                print_log(
                    f"Terminated {link_entity(CONFIG_COMMON.url, compute_requirement)}"
                )
            except:
                print_error(f"Unable to terminate '{compute_requirement.name}'")

    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
    else:
        print_log("No Compute Requirements terminated")


# Entry point
if __name__ == "__main__":
    main()
