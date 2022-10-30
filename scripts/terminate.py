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

from common import ARGS_PARSER, ConfigCommon, link_entity, load_config_common, print_log
from interactive import confirmed, select

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
            f"Terminating Compute Requirements matching "
            f"NAMESPACE={CONFIG_COMMON.namespace} and "
            f"TAG={CONFIG_COMMON.name_tag}"
        )
        compute_requirement_summaries: List[
            ComputeRequirementSummary
        ] = CLIENT.compute_client.find_all_compute_requirements()
        terminated_count = 0
        selected_compute_requirement_summaries: List[ComputeRequirementSummary] = []

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
                selected_compute_requirement_summaries.append(compute_summary)

        if len(selected_compute_requirement_summaries) != 0 and ARGS_PARSER.interactive:
            selected_compute_requirement_summaries = select(
                selected_compute_requirement_summaries
            )

        if len(selected_compute_requirement_summaries) != 0 and confirmed(
            f"Terminate {len(selected_compute_requirement_summaries)} "
            "Compute Requirement(s)?"
        ):
            for compute_summary in selected_compute_requirement_summaries:
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
                        CLIENT.compute_client.get_compute_requirement_by_id(
                            compute_summary.id
                        )
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
    except Exception as e:
        print_log(f"Error: {e}")

    print_log("Done")


# Entry point
if __name__ == "__main__":
    main()
