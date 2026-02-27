#!/usr/bin/env python3

"""
A script to terminate Compute Requirements and Nodes.
"""

from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementStatus,
    ComputeRequirementSummary,
    Instance,
    Node,
)

from yellowdog_cli.utils.entity_utils import (
    get_compute_requirement_id_by_name,
    get_compute_requirement_id_by_worker_pool_id,
    get_compute_requirement_summaries,
    get_instance_id_by_id,
)
from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import link_entity
from yellowdog_cli.utils.printing import print_error, print_info, print_warning
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
    if len(ARGS_PARSER.compute_requirements_instances_or_nodes) > 0:
        terminate_by_name_or_id(ARGS_PARSER.compute_requirements_instances_or_nodes)
        return

    print_info(
        "Terminating Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' with tags "
        f"including '{CONFIG_COMMON.name_tag}'"
    )

    compute_requirement_summaries: list[ComputeRequirementSummary] = (
        get_compute_requirement_summaries(
            CLIENT,
            CONFIG_COMMON.namespace,
            CONFIG_COMMON.name_tag,
            VALID_TERMINATION_STATUSES,
        )
    )

    terminated_count = 0
    selected_compute_requirement_summaries: list[ComputeRequirementSummary] = select(
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
                print_info(
                    f"Terminated {link_entity(CONFIG_COMMON.url, compute_requirement_summary)}"
                )
            except Exception as e:
                print_error(
                    f"Failed to terminate '{compute_requirement_summary.name}': {e}"
                )

    if terminated_count > 0:
        print_info(f"Terminated {terminated_count} Compute Requirement(s)")
        if ARGS_PARSER.follow:
            follow_ids([cr.id for cr in selected_compute_requirement_summaries])
    else:
        print_info("No Compute Requirements terminated")


def terminate_by_name_or_id(names_or_ids: list[str]):
    """
    Terminate Compute Requirements by their names or IDs, or
    node IDs by their ID, or instances by 'cr_id.instance_id'.
    """
    compute_requirement_ids: list[str] = []
    node_or_instance_cr_ids: list[str] = []
    for name_or_id in names_or_ids:
        # Is this a cr_id.instance_id specification?
        if len(cr_id_instance_id := name_or_id.split(".")) == 2:
            if (
                cr_id := _terminate_instance(cr_id_instance_id[0], cr_id_instance_id[1])
            ) is not None:
                node_or_instance_cr_ids.append(cr_id)
        elif (ydid_type := get_ydid_type(name_or_id)) == YDIDType.COMPUTE_REQUIREMENT:
            compute_requirement_ids.append(name_or_id)
        elif ydid_type == YDIDType.NODE:
            if (cr_id := _terminate_node_instance_by_id(name_or_id)) is not None:
                node_or_instance_cr_ids.append(cr_id)
        else:  # Let's see if it's a compute requirement name
            compute_requirement_id = get_compute_requirement_id_by_name(
                CLIENT, name_or_id, VALID_TERMINATION_STATUSES
            )
            if compute_requirement_id is None:
                print_warning(
                    f"Compute Requirement in valid state not found for '{name_or_id}'"
                )
                continue
            else:
                print_info(f"Found Compute Requirement ID: {compute_requirement_id}")
                compute_requirement_ids.append(compute_requirement_id)

    if len(compute_requirement_ids) > 0:
        if not confirmed(
            f"Terminate {len(compute_requirement_ids)} Compute Requirement(s)?"
        ):
            return
        for compute_requirement_id in compute_requirement_ids:
            try:
                CLIENT.compute_client.terminate_compute_requirement_by_id(
                    compute_requirement_id
                )
                print_info(f"Terminated '{compute_requirement_id}'")
            except Exception as e:
                print_error(f"Failed to terminate '{compute_requirement_id}': ({e})")

    if ARGS_PARSER.follow:
        follow_ids(compute_requirement_ids + node_or_instance_cr_ids)


def _terminate_node_instance_by_id(node_id: str) -> str | None:
    """
    Terminate a node's instance by its ID.
    Returns the compute requirement ID or None.
    """
    try:
        node: Node = CLIENT.worker_pool_client.get_node_by_id(node_id)
    except Exception as e:
        if "404" in str(e):
            print_error(f"Cannot find Node with ID {node_id}")
            return None
        else:
            print_error(f"Error for Node ID {node_id}: {e}")
            return None

    cr_id: str = get_compute_requirement_id_by_worker_pool_id(CLIENT, node.workerPoolId)
    instance: Instance = get_instance_id_by_id(CLIENT, cr_id, node.details.instanceId)

    if instance is None:
        print_error(
            f"Cannot find Instance ID for Node ID {node_id} "
            f"in Compute Requirement {cr_id}"
        )
        return None

    return _terminate_instance(cr_id, instance.id.instanceId, node_id)


def _terminate_instance(
    cr_id: str, instance_id: str, node_id: str | None = None
) -> str | None:
    """
    Terminate instance_id within cr_id.
    Returns the compute requirement ID or None.
    """

    if get_ydid_type(cr_id) != YDIDType.COMPUTE_REQUIREMENT:
        print_error(f"Invalid Compute Requirement ID {cr_id}")
        return None

    try:
        compute_requirement = CLIENT.compute_client.get_compute_requirement_by_id(cr_id)
    except:
        print_error(f"Cannot find Compute Requirement {cr_id}")
        return None

    instance: Instance = get_instance_id_by_id(CLIENT, cr_id, instance_id)
    if instance is None:
        print_error(
            f"Cannot find Instance ID '{instance_id}' in Compute Requirement {cr_id}"
        )
        return None

    node_id_msg = "" if node_id is None else f" (Node ID {node_id})"
    if not confirmed(
        f"Immediately terminate {instance.status} Instance ID '{instance_id}' "
        f"in Compute Requirement {cr_id}{node_id_msg}?"
    ):
        return None

    try:
        CLIENT.compute_client.terminate_instances(compute_requirement, [instance])
    except Exception as e:
        if "InvalidComputeRequirementStatusException" in str(e):
            print_error(
                f"Unable to terminate Instance ID '{instance_id}': "
                f"Compute Requirement {cr_id} is in invalid status"
                f" '{compute_requirement.status}'"
            )
        else:
            print_error(
                f"Failed to terminate Instance '{instance_id}' in "
                f"Compute Requirement {cr_id}: {e}"
            )
        return None

    print_info(f"Terminated Instance '{instance_id}' in Compute Requirement {cr_id}")
    return cr_id


# Entry point
if __name__ == "__main__":
    main()
