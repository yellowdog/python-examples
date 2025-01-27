#!/usr/bin/env python3

"""
A script to resize Worker Pools and Compute Requirements.
"""

from typing import List

from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    WorkerPool,
)

from yellowdog_cli.utils.entity_utils import get_worker_pool_id_by_name
from yellowdog_cli.utils.follow_utils import follow_events, follow_ids
from yellowdog_cli.utils.interactive import confirmed
from yellowdog_cli.utils.printing import print_log, print_warning
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


@main_wrapper
def main():
    if ARGS_PARSER.compute_req_resize:
        _resize_compute_requirement()
    else:
        _resize_worker_pool()


def _resize_worker_pool():
    """
    Resize a Worker Pool
    """
    print_log(
        f"Resizing Worker Pool '{ARGS_PARSER.worker_pool_name}' to"
        f" {ARGS_PARSER.worker_pool_size:,d} node(s)"
    )
    if get_ydid_type(ARGS_PARSER.worker_pool_name) == YDIDType.WORKER_POOL:
        worker_pool_id = ARGS_PARSER.worker_pool_name
    else:
        worker_pool_id = get_worker_pool_id_by_name(
            CLIENT, ARGS_PARSER.worker_pool_name
        )
        if worker_pool_id is None:
            raise Exception(f"Worker Pool '{ARGS_PARSER.worker_pool_name}' not found")

    worker_pool: WorkerPool = CLIENT.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id=worker_pool_id
    )
    if not confirmed(
        f"Confirm resize Worker Pool to {ARGS_PARSER.worker_pool_size} node(s)?"
    ):
        return

    CLIENT.worker_pool_client.resize_worker_pool(
        worker_pool=worker_pool, size=ARGS_PARSER.worker_pool_size
    )

    if ARGS_PARSER.follow:
        print_log("Following event stream(s)")
        follow_ids([worker_pool.id], auto_cr=ARGS_PARSER.auto_cr)


def _resize_compute_requirement():
    """
    Resize a Compute Requirement
    """
    print_log(
        f"Resizing Compute Requirement '{ARGS_PARSER.worker_pool_name}' to"
        f" {ARGS_PARSER.worker_pool_size:,d} instance(s)"
    )
    print_log(
        f"Finding Compute Requirement in Namespace '{CONFIG_COMMON.namespace}' with"
        f" Tag starting with '{CONFIG_COMMON.name_tag}'"
    )
    cr_search = ComputeRequirementSearch(
        namespace=CONFIG_COMMON.namespace,
    )
    search_client: SearchClient = CLIENT.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    for compute_requirement in compute_requirements:
        tag = "" if compute_requirement.tag is None else compute_requirement.tag
        if tag.startswith(CONFIG_COMMON.name_tag):
            if (
                compute_requirement.name == ARGS_PARSER.worker_pool_name
                or compute_requirement.id == ARGS_PARSER.worker_pool_name
            ):
                if compute_requirement.status != ComputeRequirementStatus.RUNNING:
                    raise Exception(
                        "Compute Requirement status must be"
                        f" '{ComputeRequirementStatus.RUNNING}' (actual status:"
                        f" '{compute_requirement.status}') "
                    )
                print_log(
                    "Current target/expected instance counts ="
                    f" {compute_requirement.targetInstanceCount:,d}/"
                    f"{compute_requirement.expectedInstanceCount:,d}"
                )
                if (
                    compute_requirement.targetInstanceCount
                    == ARGS_PARSER.worker_pool_size
                ):
                    print_log(
                        "No resize attempted: target instance count would be unchanged"
                    )
                    return
                compute_requirement.targetInstanceCount = ARGS_PARSER.worker_pool_size
                if confirmed(
                    f"Confirm resize Compute Requirement '{compute_requirement.name}'"
                    f" to {compute_requirement.targetInstanceCount:,d} instance(s)?"
                ):
                    CLIENT.compute_client.update_compute_requirement(
                        compute_requirement
                    )
                    print_log(
                        "Resizing complete: new target instance count ="
                        f" {compute_requirement.targetInstanceCount}"
                    )
                    if ARGS_PARSER.follow:
                        if ARGS_PARSER.auto_cr:
                            print_warning(
                                "Option '--auto-follow-compute-requirements/-a' is"
                                " ignored when resizing Compute Requirements"
                            )
                        print_log("Following event stream")
                        follow_events(
                            compute_requirement.id, YDIDType.COMPUTE_REQUIREMENT
                        )
                return
    else:
        raise Exception(
            f"Compute Requirement '{ARGS_PARSER.worker_pool_name}' not found"
        )


# Standalone entry point
if __name__ == "__main__":
    main()
