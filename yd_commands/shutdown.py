#!/usr/bin/env python3

"""
A script to shut down Provisioned Worker Pools.
"""

from typing import List

from yellowdog_client.model import (
    ComputeRequirement,
    ComputeRequirementStatus,
    WorkerPool,
    WorkerPoolStatus,
    WorkerPoolSummary,
)

from yd_commands.follow_utils import follow_ids
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import (
    get_worker_pool_by_id,
    get_worker_pool_id_by_name,
)
from yd_commands.printing import print_error, print_log
from yd_commands.utils import link_entity
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if len(ARGS_PARSER.worker_pool_list) > 0:
        shutdown_by_names_or_ids(ARGS_PARSER.worker_pool_list)
        return

    print_log(
        "Shutting down Worker Pools with Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"tag starting with '{CONFIG_COMMON.name_tag}'"
    )
    worker_pool_summaries: List[WorkerPoolSummary] = (
        CLIENT.worker_pool_client.find_all_worker_pools()
    )
    shutdown_count = 0

    selected_worker_pool_summaries: List[WorkerPoolSummary] = []
    for worker_pool_summary in worker_pool_summaries:
        if not (
            "ProvisionedWorkerPool" not in worker_pool_summary.type
            or worker_pool_summary.status
            in [WorkerPoolStatus.TERMINATED, WorkerPoolStatus.SHUTDOWN]
        ):
            worker_pool: WorkerPool = get_worker_pool_by_id(
                CLIENT, worker_pool_summary.id
            )
            compute_requirement: ComputeRequirement = (
                CLIENT.compute_client.get_compute_requirement_by_id(
                    worker_pool.computeRequirementId
                )
            )
            compute_requirement.tag = (
                "" if compute_requirement.tag is None else compute_requirement.tag
            )
            if (
                compute_requirement.tag.startswith(CONFIG_COMMON.name_tag)
                and compute_requirement.namespace == CONFIG_COMMON.namespace
                and compute_requirement.status
                not in [
                    ComputeRequirementStatus.TERMINATED,
                    ComputeRequirementStatus.TERMINATING,
                ]
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
            except:
                print_error(f"Unable to shut down '{worker_pool_summary.name}'")

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
    Shutdown Worker Pools by their names or IDs.
    """
    worker_pool_ids: List[str] = []
    for name_or_id in names_or_ids:
        if "ydid:wrkrpool:" in name_or_id:
            worker_pool_id = name_or_id
        else:
            worker_pool_id = get_worker_pool_id_by_name(CLIENT, name_or_id)
            if worker_pool_id is None:
                print_error(f"Worker Pool '{name_or_id}' not found")
                continue
        worker_pool_ids.append(worker_pool_id)

    if len(worker_pool_ids) == 0:
        print_log("No Worker Pools to shut down")
        return

    if not confirmed(f"Shut down {len(worker_pool_ids)} Worker Pool(s)?"):
        return

    for worker_pool_id in worker_pool_ids:
        try:
            CLIENT.worker_pool_client.shutdown_worker_pool_by_id(worker_pool_id)
            print_log(f"Shut down Worker Pool '{worker_pool_id}'")
        except Exception as e:
            print_error(f"Unable to shut down Worker Pool '{worker_pool_id}' ({e})")

    if ARGS_PARSER.follow:
        follow_ids(worker_pool_ids, auto_cr=ARGS_PARSER.auto_cr)


# Entry point
if __name__ == "__main__":
    main()
