#!/usr/bin/env python3

"""
Command to show the JSON details of YellowDog entities via their IDs.
"""

from typing import Optional

from yellowdog_client.model import ConfiguredWorkerPool, Task

from yd_commands.entity_utils import get_task_by_id
from yd_commands.list import get_keyring
from yd_commands.printing import print_error, print_log, print_yd_object
from yd_commands.settings import (
    RESOURCE_PROPERTY_NAME,
    RN_ALLOWANCE,
    RN_CONFIGURED_POOL,
    RN_IMAGE_FAMILY,
    RN_KEYRING,
    RN_REQUIREMENT_TEMPLATE,
    RN_SOURCE_TEMPLATE,
)
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper
from yd_commands.ydid_utils import YDIDType, get_ydid_type


@main_wrapper
def main():

    # Generate a JSON list of resources if there are multiple YDIDs
    # and the 'quiet' option is enabled
    generate_json_list = len(ARGS_PARSER.yellowdog_ids) > 1 and ARGS_PARSER.quiet

    if generate_json_list:
        print("[")

    for index, ydid in enumerate(ARGS_PARSER.yellowdog_ids):
        if generate_json_list:
            if index < len(ARGS_PARSER.yellowdog_ids) - 1:
                show_details(ydid, initial_indent=2, with_final_comma=True)
            else:
                show_details(ydid, initial_indent=2, with_final_comma=False)
        else:
            show_details(ydid)

    if generate_json_list:
        print("]")


def show_details(ydid: str, initial_indent: int = 0, with_final_comma: bool = False):
    """
    Show the details for a given YDID.
    """
    try:
        if get_ydid_type(ydid) == YDIDType.COMPUTE_SOURCE_TEMPLATE:
            print_log(f"Showing details of Compute Source Template ID '{ydid}'")
            print_yd_object(
                CLIENT.compute_client.get_compute_source_template(ydid),
                initial_indent=initial_indent,
                with_final_comma=with_final_comma,
                add_fields=({RESOURCE_PROPERTY_NAME: RN_SOURCE_TEMPLATE}),
            )

        elif get_ydid_type(ydid) == YDIDType.COMPUTE_REQUIREMENT_TEMPLATE:
            print_log(f"Showing details of Compute Requirement Template ID '{ydid}'")
            print_yd_object(
                CLIENT.compute_client.get_compute_requirement_template(ydid),
                initial_indent=initial_indent,
                with_final_comma=with_final_comma,
                add_fields=({RESOURCE_PROPERTY_NAME: RN_REQUIREMENT_TEMPLATE}),
            )

        elif get_ydid_type(ydid) == YDIDType.COMPUTE_REQUIREMENT:
            print_log(f"Showing details of Compute Requirement ID '{ydid}'")
            print_yd_object(CLIENT.compute_client.get_compute_requirement_by_id(ydid))

        elif get_ydid_type(ydid) == YDIDType.COMPUTE_SOURCE:
            print_log(f"Showing details of Compute Source ID '{ydid}'")
            compute_requirement = CLIENT.compute_client.get_compute_requirement_by_id(
                ydid.rsplit(":", 1)[0].replace("compsrc", "compreq")
            )
            for source in compute_requirement.provisionStrategy.sources:
                if source.id == ydid:
                    print_yd_object(source)
                    return
            else:
                print_error(f"Compute Source ID '{ydid}' not found")

        elif get_ydid_type(ydid) == YDIDType.WORKER_POOL:
            print_log(f"Showing details of Worker Pool ID '{ydid}'")
            worker_pool = CLIENT.worker_pool_client.get_worker_pool_by_id(ydid)
            print_yd_object(
                worker_pool,
                initial_indent=initial_indent,
                with_final_comma=with_final_comma,
                add_fields=({RESOURCE_PROPERTY_NAME: RN_CONFIGURED_POOL}),
            )
            if ARGS_PARSER.show_token and isinstance(worker_pool, ConfiguredWorkerPool):
                print_log("Showing Configured Worker Pool token data")
                print_yd_object(
                    CLIENT.worker_pool_client.get_configured_worker_pool_token_by_id(
                        ydid
                    )
                )

        elif get_ydid_type(ydid) == YDIDType.NODE:
            print_log(f"Showing details of Node ID '{ydid}'")
            print_yd_object(CLIENT.worker_pool_client.get_node_by_id(ydid))

        elif get_ydid_type(ydid) == YDIDType.WORKER:
            print_log(f"Showing details of Worker ID '{ydid}'")
            node = CLIENT.worker_pool_client.get_node_by_id(
                ydid.rsplit(":", 1)[0].replace("wrkr", "node")
            )
            for worker in node.workers:
                if worker.id == ydid:
                    print_yd_object(worker)
                    return
            else:
                print_error(f"Worker ID '{ydid}' not found")

        elif get_ydid_type(ydid) == YDIDType.WORK_REQUIREMENT:
            print_log(f"Showing details of Work Requirement ID '{ydid}'")
            print_yd_object(CLIENT.work_client.get_work_requirement_by_id(ydid))

        elif get_ydid_type(ydid) == YDIDType.TASK_GROUP:
            print_log(f"Showing details of Task Group ID '{ydid}'")
            work_requirement = CLIENT.work_client.get_work_requirement_by_id(
                ydid.rsplit(":", 1)[0].replace("taskgrp", "workreq")
            )
            for task_group in work_requirement.taskGroups:
                if task_group.id == ydid:
                    print_yd_object(task_group)
                    return
            else:
                print_error(f"Task Group ID '{ydid}' not found")

        elif get_ydid_type(ydid) == YDIDType.TASK:
            print_log(f"Showing details of Task ID '{ydid}'")
            work_requirement = CLIENT.work_client.get_work_requirement_by_id(
                ydid.rsplit(":", 2)[0].replace("task", "workreq")
            )
            for task_group in work_requirement.taskGroups:
                if task_group.id == ydid.rsplit(":", 1)[0].replace("task", "taskgrp"):
                    break
            else:
                print_error(f"Task Group ID '{ydid}' not found")
                return
            task: Optional[Task] = get_task_by_id(
                CLIENT, work_requirement.id, task_group.id, ydid
            )
            if task is not None:
                print_yd_object(task)
            else:
                print_error(f"Task ID '{ydid}' not found")

        elif get_ydid_type(ydid) == YDIDType.IMAGE_FAMILY:
            print_log(f"Showing details of Image Family ID '{ydid}'")
            print_yd_object(
                CLIENT.images_client.get_image_family_by_id(ydid),
                initial_indent=initial_indent,
                with_final_comma=with_final_comma,
                add_fields=({RESOURCE_PROPERTY_NAME: RN_IMAGE_FAMILY}),
            )

        elif get_ydid_type(ydid) == YDIDType.IMAGE_GROUP:
            print_log(f"Showing details of Image Group ID '{ydid}'")
            print_yd_object(CLIENT.images_client.get_image_group_by_id(ydid))

        elif get_ydid_type(ydid) == YDIDType.IMAGE:
            print_log(f"Showing details of Image ID '{ydid}'")
            print_yd_object(CLIENT.images_client.get_image(ydid))

        elif get_ydid_type(ydid) == YDIDType.KEYRING:
            print_log(f"Showing details of Keyring ID '{ydid}'")
            keyrings = CLIENT.keyring_client.find_all_keyrings()
            for keyring in keyrings:
                if keyring.id == ydid:
                    # This fetches additional Keyring data: credentials and accessors
                    print_yd_object(
                        get_keyring(keyring.name),
                        initial_indent=initial_indent,
                        with_final_comma=with_final_comma,
                        add_fields=({RESOURCE_PROPERTY_NAME: RN_KEYRING}),
                    )
                    return
            else:
                print_error(f"Keyring ID '{ydid}' not found")

        elif get_ydid_type(ydid) == YDIDType.ALLOWANCE:
            print_log(f"Showing details of Allowance ID '{ydid}'")
            print_yd_object(
                CLIENT.allowances_client.get_allowance_by_id(ydid),
                initial_indent=initial_indent,
                with_final_comma=with_final_comma,
                add_fields=({RESOURCE_PROPERTY_NAME: RN_ALLOWANCE}),
            )

        else:
            print_error(f"Unknown (or unsupported) YellowDog ID type for '{ydid}'")

    except Exception as e:
        print_error(f"Unable to show details for '{ydid}': {e}")


# Entry point
if __name__ == "__main__":
    main()
