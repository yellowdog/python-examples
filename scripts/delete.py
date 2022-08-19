#!python3

"""
A minimal, example script to delete YDOS objects. No error-checking is
performed.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ObjectPath,
    ObjectPathsRequest,
    ServicesSchema,
)

from common import Config, link, load_config, print_log

# Import the configuration from the TOML file
CONFIG: Config = load_config()

CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main():
    print_log(
        f"Deleting Object Paths in NAMESPACE={CONFIG.namespace} with "
        f"names starting with NAME_TAG={CONFIG.name_tag}"
    )
    object_paths: List[
        ObjectPath
    ] = CLIENT.object_store_client.get_namespace_object_paths(
        ObjectPathsRequest(CONFIG.namespace)
    )
    object_paths_to_delete: List[ObjectPath] = []
    for object_path in object_paths:
        if object_path.name.startswith(CONFIG.name_tag):
            object_paths_to_delete.append(object_path)
    if len(object_paths_to_delete) != 0:
        print_log(f"{len(object_paths_to_delete)} Object Path(s) to Delete")
        CLIENT.object_store_client.delete_objects(
            CONFIG.namespace, object_paths=object_paths_to_delete
        )
        for object_path in object_paths_to_delete:
            print_log(f"Deleted Object Path: {object_path.displayName}")
        print_log(f"Deleted {len(object_paths_to_delete)} Object Path(s)")
    else:
        print_log("Nothing to delete")
    # Clean up
    CLIENT.close()
    print_log("Done")


# Entry point
if __name__ == "__main__":
    main()
    exit(0)
