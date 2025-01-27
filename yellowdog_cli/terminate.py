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

from yellowdog_cli.utils.entity_utils import get_compute_requirement_id_by_name
from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import link_entity
from yellowdog_cli.utils.printing import print_error, print_log
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type

VALID_TERMINATION_STATUSES = [
    ComputeRequirementStatus.NEW,
    ComputeRequirementStatus.PROVISIONING,
    ComputeRequirementStatus.STARTING,
    ComputeRequirementStatus.RUNNING,
    ComputeRequirementStatus.STOPPING,
]  # Excludes TERMINATED, TERMINATING


@main_wrapper
def main():
    if len(ARGS_PARSER.compute_requirement_names) > 0:
        terminate_cr_by_name_or_id(ARGS_PARSER.compute_requirement_names)
        return

    print_log(
        "Terminating Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and tag "
        f"starting with '{CONFIG_COMMON.name_tag}'"
    )

    cr_search = ComputeRequirementSearch(
        namespace=CONFIG_COMMON.namespace,
        statuses=VALID_TERMINATION_STATUSES,
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
            except Exception as e:
                print_error(f"Unable to terminate '{compute_requirement.name}': {e}")

    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
        if ARGS_PARSER.follow:
            follow_ids([cr.id for cr in selected_compute_requirements])
    else:
        print_log("No Compute Requirements terminated")


def terminate_cr_by_name_or_id(names_or_ids: List[str]):
    """
    Terminate Compute Requirements by their names or IDs.
    """
    compute_requirement_ids: List[str] = []
    for name_or_id in names_or_ids:
        if get_ydid_type(name_or_id) == YDIDType.COMPUTE_REQUIREMENT:
            compute_requirement_id = name_or_id
        else:
            compute_requirement_id = get_compute_requirement_id_by_name(
                CLIENT, name_or_id, VALID_TERMINATION_STATUSES
            )
            if compute_requirement_id is None:
                print_error(f"Valid Compute Requirement not found for '{name_or_id}'")
                continue
            else:
                print_log(f"Found Compute Requirement ID: {compute_requirement_id}")
        compute_requirement_ids.append(compute_requirement_id)

    if len(compute_requirement_ids) == 0:
        print_log("No Compute Requirements to terminate")
        return

    if not confirmed(
        f"Terminate {len(compute_requirement_ids)} Compute Requirement(s)?"
    ):
        return

    for compute_requirement_id in compute_requirement_ids:
        try:
            CLIENT.compute_client.terminate_compute_requirement_by_id(
                compute_requirement_id
            )
            print_log(f"Terminated '{compute_requirement_id}'")
        except Exception as e:
            print_error(f"Unable to terminate '{compute_requirement_id}': ({e})")

    if ARGS_PARSER.follow:
        follow_ids(compute_requirement_ids)


# Entry point
if __name__ == "__main__":
    main()
