#!/usr/bin/env python3

"""
An example script to shut down Provisioned Worker Pools.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ComputeRequirement,
    ComputeRequirementStatus,
    ServicesSchema,
    WorkerPool,
    WorkerPoolStatus,
    WorkerPoolSummary,
)

from common import ARGS_PARSER, ConfigCommon, link_entity, load_config_common, print_log
from selector import select

# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()

# Initialise the client
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def main():
    try:
        print_log(
            f"Shutting down Worker Pools with Compute Requirements matching "
            f"NAMESPACE={CONFIG_COMMON.namespace} and "
            f"TAG={CONFIG_COMMON.name_tag}"
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
                selected_worker_pool_summaries.append(worker_pool_summary)

        if len(selected_worker_pool_summaries) != 0 and ARGS_PARSER.items:
            selected_worker_pool_summaries = select(selected_worker_pool_summaries)

        for worker_pool_summary in selected_worker_pool_summaries:
            if (
                "ProvisionedWorkerPool" not in worker_pool_summary.type
                or worker_pool_summary.status
                in [WorkerPoolStatus.TERMINATED, WorkerPoolStatus.SHUTDOWN]
            ):
                continue
            worker_pool: WorkerPool = CLIENT.worker_pool_client.get_worker_pool_by_id(
                worker_pool_summary.id
            )
            compute_requirement: ComputeRequirement = (
                CLIENT.compute_client.get_compute_requirement_by_id(
                    worker_pool.computeRequirementId
                )
            )
            if (
                compute_requirement.tag == CONFIG_COMMON.name_tag
                and compute_requirement.namespace == CONFIG_COMMON.namespace
                and compute_requirement.status
                not in [
                    ComputeRequirementStatus.TERMINATED,
                    ComputeRequirementStatus.TERMINATING,
                ]
            ):
                CLIENT.worker_pool_client.shutdown_worker_pool_by_id(worker_pool.id)
                shutdown_count += 1
                print_log(f"Shut down {link_entity(CONFIG_COMMON.url, worker_pool)}")
        if shutdown_count > 0:
            print_log(f"Shut down {shutdown_count} Worker Pool(s)")
        else:
            print_log("Nothing to shut down")
        # Clean up
        CLIENT.close()
    except Exception as e:
        print_log(f"Error: {e}")

    print_log("Done")


# Entry point
if __name__ == "__main__":
    main()
