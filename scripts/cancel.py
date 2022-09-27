#!python3

"""
A minimal, example script to cancel Work Requirements. No error-checking
is performed.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ServicesSchema,
    WorkRequirement,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from common import ConfigCommon, link_entity, load_config_common, print_log

# Import the configuration from the TOML file
CONFIG: ConfigCommon = load_config_common()

CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main():
    print_log(
        f"Cancelling Work Requirements matching NAMESPACE={CONFIG.namespace} "
        f"and with NAME_TAG={CONFIG.name_tag}"
    )
    work_requirement_summaries: List[
        WorkRequirementSummary
    ] = CLIENT.work_client.find_all_work_requirements()
    cancelled_count = 0
    for work_summary in work_requirement_summaries:
        if (
            work_summary.tag == CONFIG.name_tag
            and work_summary.namespace == CONFIG.namespace
            and work_summary.status
            not in [
                WorkRequirementStatus.COMPLETED,
                WorkRequirementStatus.CANCELLED,
                WorkRequirementStatus.CANCELLING,
                WorkRequirementStatus.FAILED,
            ]
        ):
            CLIENT.work_client.cancel_work_requirement_by_id(work_summary.id)
            work_requirement: WorkRequirement = (
                CLIENT.work_client.get_work_requirement_by_id(work_summary.id)
            )
            cancelled_count += 1
            print_log(f"Cancelling {link_entity(CONFIG.url, work_requirement)}")
    if cancelled_count > 0:
        print_log(f"Cancelled {cancelled_count} Work Requirement(s)")
    else:
        print_log("Nothing to cancel")
    CLIENT.close()
    print_log("Done")


# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log(f"Error: {e}")
        exit(1)
    exit(0)
