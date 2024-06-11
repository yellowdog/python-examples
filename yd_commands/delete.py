#!/usr/bin/env python3

"""
A script to delete YellowDog Object Store items.
"""

from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import list_matching_object_paths
from yd_commands.printing import print_log
from yd_commands.utils import unpack_namespace_in_prefix
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    # Direct command line argument overrides tag/prefix
    if len(ARGS_PARSER.object_paths_to_delete) > 0:
        for object_path in ARGS_PARSER.object_paths_to_delete:
            namespace, tag = unpack_namespace_in_prefix(
                namespace=CONFIG_COMMON.namespace,
                prefix=object_path,
            )
            delete_object_paths(namespace, tag, ARGS_PARSER.all)
        return

    # Use tag/prefix
    namespace, tag = unpack_namespace_in_prefix(
        namespace=CONFIG_COMMON.namespace,
        prefix=CONFIG_COMMON.name_tag,
    )
    delete_object_paths(namespace, tag, ARGS_PARSER.all)
    return


def delete_object_paths(namespace: str, prefix: str, flat: bool):
    """
    Delete Object Paths matching the namespace and prefix. Set 'flat' to
    enumerate Object Paths at all levels.
    """
    print_log(
        f"Deleting Object Paths in namespace '{namespace}' and "
        f"prefix starting with '{prefix}'"
    )

    object_paths_to_delete = list_matching_object_paths(CLIENT, namespace, prefix, flat)

    if len(object_paths_to_delete) == 0:
        print_log("No matching Object Paths")
        return

    object_paths_to_delete = select(CLIENT, object_paths_to_delete)

    if len(object_paths_to_delete) > 0 and confirmed(
        f"Delete {len(object_paths_to_delete)} Object Path(s)?"
    ):
        print_log(f"{len(object_paths_to_delete)} Object Path(s) to Delete")
        CLIENT.object_store_client.delete_objects(
            namespace=namespace, object_paths=object_paths_to_delete
        )
        for object_path in object_paths_to_delete:
            print_log(f"Deleted Object Path: '{object_path.displayName}'")
        print_log(f"Deleted {len(object_paths_to_delete)} Object Path(s)")
    else:
        print_log("Nothing to delete")


# Entry point
if __name__ == "__main__":
    main()
