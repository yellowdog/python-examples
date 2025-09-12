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

from yellowdog_cli.utils.entity_utils import (
    get_compute_requirement_id_by_name,
    get_compute_requirement_summaries,
)
from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import link_entity
from yellowdog_cli.utils.printing import print_error, print_log, print_warning
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
        f"including '{CONFIG_COMMON.name_tag}'"
    )

    compute_requirement_summaries: List[ComputeRequirementSummary] = (
        get_compute_requirement_summaries(
            CLIENT,
            CONFIG_COMMON.namespace,
            CONFIG_COMMON.name_tag,
            VALID_TERMINATION_STATUSES,
        )
    )

    terminated_count = 0
    selected_compute_requirement_summaries: List[ComputeRequirementSummary] = select(
        CLIENT, compute_requirement_summaries
    )

    if len(selected_compute_requirement_summaries) > 0 and confirmed(
        f"Terminate {len(selected_compute_requirement_summaries)} Compute Requirement(s)?"
    ):
        for compute_requirement_summary in selected_compute_requirement_summaries:
            try:
                CLIENT.compute_client.terminate_compute_requirement_by_id(
                    compute_requirement_summary.id
                )
                compute_requirement_summary: ComputeRequirement = (
                    CLIENT.compute_client.get_compute_requirement_by_id(
                        compute_requirement_summary.id
                    )
                )
                terminated_count += 1
                print_log(
                    f"Terminated {link_entity(CONFIG_COMMON.url, compute_requirement_summary)}"
                )
            except Exception as e:
                print_error(
                    f"Unable to terminate '{compute_requirement_summary.name}': {e}"
                )

    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
        if ARGS_PARSER.follow:
            follow_ids([cr.id for cr in selected_compute_requirement_summaries])
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
                print_warning(
                    f"Compute Requirement in valid state not found for '{name_or_id}'"
                )
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
