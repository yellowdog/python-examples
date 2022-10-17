#!/usr/bin/env python3

"""
An example script to terminate Compute Requirements.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ComputeRequirement,
    ComputeRequirementStatus,
    ComputeRequirementSummary,
    ServicesSchema,
)

from common import ConfigCommon, link_entity, load_config_common, print_log

# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()

# Initialise the client
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def main():
    """
    The main, high-level program flow.
    """
    print_log(
        f"Terminating Compute Requirements matching "
        f"NAMESPACE={CONFIG_COMMON.namespace} and "
        f"NAME_TAG={CONFIG_COMMON.name_tag}"
    )
    compute_requirement_summaries: List[
        ComputeRequirementSummary
    ] = CLIENT.compute_client.find_all_compute_requirements()
    terminated_count = 0
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
            CLIENT.compute_client.terminate_compute_requirement_by_id(
                compute_summary.id
            )
            compute_requirement: ComputeRequirement = (
                CLIENT.compute_client.get_compute_requirement_by_id(compute_summary.id)
            )
            terminated_count += 1
            print_log(
                f"Terminated {link_entity(CONFIG_COMMON.url, compute_requirement)}"
            )
    if terminated_count > 0:
        print_log(f"Terminated {terminated_count} Compute Requirement(s)")
    else:
        print_log("Nothing to terminate")
    # Clean up
    CLIENT.close()


# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log(f"Error: {e}")
        exit(1)
    exit(0)
