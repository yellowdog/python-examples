#!/usr/bin/env python3

"""
Command to show the JSON details of YellowDog entities via their IDs.
"""

from typing import Optional

from yellowdog_client.model import ConfiguredWorkerPool, Task

from yd_commands.object_utilities import get_task_by_id
from yd_commands.printing import print_log, print_warning, print_yd_object
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():

    for ydid in ARGS_PARSER.yellowdog_ids:
        show_details(ydid)


def show_details(ydid: str):
    """
    Show the details for a given YDID
    """
    try:
        if ":cst:" in ydid:
            print_log(f"Showing details of Compute Source Template ID '{ydid}'")
            print_yd_object(CLIENT.compute_client.get_compute_source_template(ydid))

        elif ":crt:" in ydid:
            print_log(f"Showing details of Compute Requirement Template ID '{ydid}'")
            print_yd_object(
                CLIENT.compute_client.get_compute_requirement_template(ydid)
            )

        elif ":compreq:" in ydid:
            print_log(f"Showing details of Compute Requirement ID '{ydid}'")
            print_yd_object(CLIENT.compute_client.get_compute_requirement_by_id(ydid))

        elif ":compsrc:" in ydid:
            print_log(f"Showing details of Compute Source ID '{ydid}'")
            compute_requirement = CLIENT.compute_client.get_compute_requirement_by_id(
                ydid.rsplit(":", 1)[0].replace("compsrc", "compreq")
            )
            for source in compute_requirement.provisionStrategy.sources:
                if source.id == ydid:
                    print_yd_object(source)
                    return
            else:
                print_warning(f"Compute Source ID '{ydid}' not found")

        elif ":wrkrpool:" in ydid:
            print_log(f"Showing details of Worker Pool ID '{ydid}'")
            worker_pool = CLIENT.worker_pool_client.get_worker_pool_by_id(ydid)
            print_yd_object(worker_pool)
            if ARGS_PARSER.show_token and isinstance(worker_pool, ConfiguredWorkerPool):
                print_log("Showing Configured Worker Pool token data")
                print_yd_object(
                    CLIENT.worker_pool_client.get_configured_worker_pool_token_by_id(
                        ydid
                    )
                )

        elif ":node:" in ydid:
            print_log(f"Showing details of Node ID '{ydid}'")
            print_yd_object(CLIENT.worker_pool_client.get_node_by_id(ydid))

        elif ":wrkr:" in ydid:
            print_log(f"Showing details of Worker ID '{ydid}'")
            node = CLIENT.worker_pool_client.get_node_by_id(
                ydid.rsplit(":", 1)[0].replace("wrkr", "node")
            )
            for worker in node.workers:
                if worker.id == ydid:
                    print_yd_object(worker)
                    return
            else:
                print_warning(f"Worker ID '{ydid}' not found")

        elif ":workreq:" in ydid:
            print_log(f"Showing details of Work Requirement ID '{ydid}'")
            print_yd_object(CLIENT.work_client.get_work_requirement_by_id(ydid))

        elif ":taskgrp:" in ydid:
            print_log(f"Showing details of Task Group ID '{ydid}'")
            work_requirement = CLIENT.work_client.get_work_requirement_by_id(
                ydid.rsplit(":", 1)[0].replace("taskgrp", "workreq")
            )
            for task_group in work_requirement.taskGroups:
                if task_group.id == ydid:
                    print_yd_object(task_group)
                    return
            else:
                print_warning(f"Task Group ID '{ydid}' not found")

        elif ":task:" in ydid:
            print_log(f"Showing details of Task ID '{ydid}'")
            work_requirement = CLIENT.work_client.get_work_requirement_by_id(
                ydid.rsplit(":", 2)[0].replace("task", "workreq")
            )
            for task_group in work_requirement.taskGroups:
                if task_group.id == ydid.rsplit(":", 1)[0].replace("task", "taskgrp"):
                    break
            else:
                print_warning(f"Task Group ID '{ydid}' not found")
                return
            task: Optional[Task] = get_task_by_id(
                CLIENT, work_requirement.id, task_group.id, ydid
            )
            if task is not None:
                print_yd_object(task)
            else:
                print_warning(f"Task ID '{ydid}' not found")

        elif ":imgfam:" in ydid:
            print_log(f"Showing details of Image Family ID '{ydid}'")
            print_yd_object(CLIENT.images_client.get_image_family_by_id(ydid))

        elif ":imggrp:" in ydid:
            print_log(f"Showing details of Image Group ID '{ydid}'")
            print_yd_object(CLIENT.images_client.get_image_group_by_id(ydid))

        elif ":image:" in ydid:
            print_log(f"Showing details of Image ID '{ydid}'")
            print_yd_object(CLIENT.images_client.get_image(ydid))

        elif ":keyring:" in ydid:
            print_log(f"Showing details of Keyring ID '{ydid}'")
            keyrings = CLIENT.keyring_client.find_all_keyrings()
            for keyring in keyrings:
                if keyring.id == ydid:
                    print_yd_object(keyring)
                    return
            else:
                print_warning(f"Keyring ID '{ydid}' not found")

        elif ":allow:" in ydid:
            print_log(f"Showing details of Allowance ID '{ydid}'")
            print_yd_object(CLIENT.allowances_client.get_allowance_by_id(ydid))

        else:
            print_warning(f"Unknown (or unsupported) YellowDog ID type for '{ydid}'")

    except Exception as e:
        print_warning(f"Unable to show details for '{ydid}': {e}")


# Entry point
if __name__ == "__main__":
    main()
