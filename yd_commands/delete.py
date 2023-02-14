#!/usr/bin/env python3

"""
A script to delete YellowDog Object Store items.
"""

from typing import List

from yellowdog_client.model import ObjectPath, ObjectPathsRequest

from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_log
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    print_log(
        f"Deleting Object Paths in namespace '{CONFIG_COMMON.namespace}' and "
        f"names starting with '{CONFIG_COMMON.name_tag}'"
    )
    object_paths: List[
        ObjectPath
    ] = CLIENT.object_store_client.get_namespace_object_paths(
        ObjectPathsRequest(CONFIG_COMMON.namespace)
    )
    object_paths_to_delete: List[ObjectPath] = []
    for object_path in object_paths:
        if object_path.name.startswith(CONFIG_COMMON.name_tag):
            object_paths_to_delete.append(object_path)

    if len(object_paths_to_delete) > 0:
        object_paths_to_delete = select(CLIENT, object_paths_to_delete)

    if len(object_paths_to_delete) > 0 and confirmed(
        f"Delete {len(object_paths_to_delete)} Object Path(s)?"
    ):
        print_log(f"{len(object_paths_to_delete)} Object Path(s) to Delete")
        CLIENT.object_store_client.delete_objects(
            CONFIG_COMMON.namespace, object_paths=object_paths_to_delete
        )
        for object_path in object_paths_to_delete:
            print_log(f"Deleted Object Path: {object_path.displayName}")
        print_log(f"Deleted {len(object_paths_to_delete)} Object Path(s)")
    else:
        print_log("Nothing to delete")


# Entry point
if __name__ == "__main__":
    main()
