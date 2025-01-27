#!/usr/bin/env python3

"""
A script to delete YellowDog Object Store items.
"""

from yellowdog_cli.utils.entity_utils import (
    get_non_exact_namespace_matches,
    list_matching_object_paths,
)
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.misc_utils import unpack_namespace_in_prefix
from yellowdog_cli.utils.printing import print_log
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():

    # Non-exact matching of namespace property
    if ARGS_PARSER.non_exact_namespace_match:
        print_log("Using non-exact namespace matching")
        matching_namespaces = get_non_exact_namespace_matches(
            CLIENT, CONFIG_COMMON.namespace
        )
        if len(matching_namespaces) == 0:
            print_log("No matching namespaces")
            return
        print_log(f"{len(matching_namespaces)} namespace(s) to consider")
        for namespace in matching_namespaces:
            _, tag = unpack_namespace_in_prefix(namespace, CONFIG_COMMON.name_tag)
            delete_object_paths(namespace, tag, ARGS_PARSER.all)
        return

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
