#!/usr/bin/env python3

"""
Command to list YellowDog entities.
"""

from typing import List

from yellowdog_client.model import ObjectPath, ObjectPathsRequest

from args import ARGS_PARSER
from interactive import print_numbered_object_list, select
from printing import print_error, print_log
from wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():

    if not (
        ARGS_PARSER.object_paths
        or ARGS_PARSER.work_requirements
        or ARGS_PARSER.task_groups
        or ARGS_PARSER.tasks
        or ARGS_PARSER.worker_pools
        or ARGS_PARSER.compute_requirements
    ):
        raise Exception("No object type options chosen")

    if ARGS_PARSER.object_paths:
        print_log(
            f"Listing Object Paths in 'namespace={CONFIG_COMMON.namespace}' with "
            f"names starting with 'tag={CONFIG_COMMON.name_tag}'"
        )
        object_paths: List[
            ObjectPath
        ] = CLIENT.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(CONFIG_COMMON.namespace)
        )
        print_numbered_object_list(object_paths)


# Entry point
if __name__ == "__main__":
    main()
