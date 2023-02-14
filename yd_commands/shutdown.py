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

from yd_commands.config import link_entity
from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import get_worker_pool_by_id
from yd_commands.printing import print_error, print_log
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Shutting down Worker Pools with Compute Requirements in "
        f"namespace '{CONFIG_COMMON.namespace}' and "
        f"tag starting with '{CONFIG_COMMON.name_tag}'"
    )
    worker_pool_summaries: List[
        WorkerPoolSummary
    ] = CLIENT.worker_pool_client.find_all_worker_pools()
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
    else:
        print_log("No Worker Pools shut down")


# Entry point
if __name__ == "__main__":
    main()
