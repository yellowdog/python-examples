#!/usr/bin/env python3

"""
A script to shut down Worker Pools and/or Nodes.
"""

from typing import List

from yellowdog_client.model import (
    ProvisionedWorkerPool,
    WorkerPool,
    WorkerPoolStatus,
    WorkerPoolSummary,
)

from yellowdog_cli.utils.entity_utils import (
    get_worker_pool_by_id,
    get_worker_pool_id_by_name,
)
from yellowdog_cli.utils.follow_utils import follow_ids
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import link_entity
from yellowdog_cli.utils.printing import print_error, print_log
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


@main_wrapper
def main():
    if len(ARGS_PARSER.worker_pool_nodes_list) > 0:
        shutdown_by_names_or_ids(ARGS_PARSER.worker_pool_nodes_list)
        return

    print_log(
        "Shutting down Worker Pools in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"names including '{CONFIG_COMMON.name_tag}'"
    )

    worker_pool_summaries: List[WorkerPoolSummary] = (
        CLIENT.worker_pool_client.find_all_worker_pools()
    )
    shutdown_count = 0

    selected_worker_pool_summaries: List[WorkerPoolSummary] = []
    for worker_pool_summary in worker_pool_summaries:
        if worker_pool_summary.status not in [
            WorkerPoolStatus.TERMINATED,
            WorkerPoolStatus.SHUTDOWN,
        ]:
            if (
                worker_pool_summary.name is not None
                and worker_pool_summary.namespace == CONFIG_COMMON.namespace
                and CONFIG_COMMON.name_tag in worker_pool_summary.name
            ):
                selected_worker_pool_summaries.append(worker_pool_summary)

    if len(selected_worker_pool_summaries) > 0:
        selected_worker_pool_summaries = select(CLIENT, selected_worker_pool_summaries)

    if len(selected_worker_pool_summaries) > 0 and confirmed(
        f"Shutdown {len(selected_worker_pool_summaries)} Worker Pool(s)?"
    ):
        for worker_pool_summary in selected_worker_pool_summaries:
            try:
                CLIENT.worker_pool_client.shutdown_worker_pool_by_id(
                    worker_pool_summary.id
                )
                shutdown_count += 1
                worker_pool: WorkerPool = get_worker_pool_by_id(
                    CLIENT, worker_pool_summary.id
                )
                print_log(f"Shut down {link_entity(CONFIG_COMMON.url, worker_pool)}")
                optionally_terminate_compute_requirement(worker_pool_summary.id)
            except Exception as e:
                print_error(f"Unable to shut down '{worker_pool_summary.name}': {e}")

    if shutdown_count > 0:
        print_log(f"Shut down {shutdown_count} Worker Pool(s)")
        if ARGS_PARSER.follow:
            follow_ids(
                [wp.id for wp in selected_worker_pool_summaries],
                auto_cr=ARGS_PARSER.auto_cr,
            )
    else:
        print_log("No Worker Pools shut down")


def shutdown_by_names_or_ids(names_or_ids: List[str]):
    """
    Shutdown Worker Pools and/or Nodes by their names or IDs.
    """
    worker_pool_ids: List[str] = []
    node_ids: List[str] = []
    for name_or_id in names_or_ids:
        if get_ydid_type(name_or_id) == YDIDType.NODE:
            node_ids.append(name_or_id)
            continue
        if get_ydid_type(name_or_id) == YDIDType.WORKER_POOL:
            worker_pool_id = name_or_id
        else:
            worker_pool_id = get_worker_pool_id_by_name(CLIENT, name_or_id)
            if worker_pool_id is None:
                print_error(f"Worker Pool '{name_or_id}' not found")
                continue
        worker_pool_ids.append(worker_pool_id)

    if len(worker_pool_ids) == 0 and len(node_ids) == 0:
        print_log("No Worker Pools or Nodes to shut down")
        return

    if not confirmed(
        f"Shut down {len(worker_pool_ids) + len(node_ids)} Worker Pool(s) and/or Node(s)?"
    ):
        return

    for worker_pool_id in worker_pool_ids:
        try:
            CLIENT.worker_pool_client.shutdown_worker_pool_by_id(worker_pool_id)
            print_log(f"Shut down Worker Pool '{worker_pool_id}'")
            optionally_terminate_compute_requirement(worker_pool_id)
        except Exception as e:
            print_error(f"Unable to shut down Worker Pool '{worker_pool_id}': ({e})")

    for node_id in node_ids:
        try:
            CLIENT.worker_pool_client.shutdown_node_by_id(node_id)
            print_log(f"Shut down Node '{node_id}'")
        except Exception as e:
            print_error(f"Unable to shut down Node '{node_id}': ({e})")

    if ARGS_PARSER.follow:
        follow_ids(worker_pool_ids, auto_cr=ARGS_PARSER.auto_cr)


def optionally_terminate_compute_requirement(worker_pool_id: str):
    """
    Optionally terminate the associated compute requirement.
    """
    if not ARGS_PARSER.terminate:
        return

    try:
        worker_pool: ProvisionedWorkerPool = (
            CLIENT.worker_pool_client.get_worker_pool_by_id(worker_pool_id)
        )
        CLIENT.compute_client.terminate_compute_requirement_by_id(
            worker_pool.computeRequirementId
        )
        print_log(
            f"Terminated associated Compute Requirement '{worker_pool.computeRequirementId}'"
        )
    except Exception as e:
        print_error(f"Error terminating Compute Requirement: ({e})")


# Entry point
if __name__ == "__main__":
    main()
