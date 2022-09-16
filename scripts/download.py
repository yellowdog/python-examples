#!python3

"""
A minimal example script to download YDOS objects to local storage.
"""

from concurrent import futures
from os import mkdir, path
from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    ObjectPath,
    ObjectPathsRequest,
    ServicesSchema,
)
from yellowdog_client.object_store.download.abstracts.abstract_download_batch_builder import (
    AbstractDownloadBatchBuilder,
)
from yellowdog_client.object_store.model import FileTransferStatus

from common import ConfigCommon, load_config_common, print_log

# Import the configuration from the TOML file
CONFIG: ConfigCommon = load_config_common()

CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main():
    print_log(
        f"Downloading all Objects in NAMESPACE={CONFIG.namespace} with "
        f"names starting with NAME_TAG={CONFIG.name_tag}"
    )
    object_paths: List[
        ObjectPath
    ] = CLIENT.object_store_client.get_namespace_object_paths(
        ObjectPathsRequest(CONFIG.namespace)
    )
    object_paths_to_download: List[ObjectPath] = []
    for object_path in object_paths:
        if object_path.name.startswith(CONFIG.name_tag):
            object_paths_to_download.append(object_path)
    if len(object_paths_to_download) != 0:
        print_log(f"{len(object_paths_to_download)} Object Path(s) to Download")
        download_dir: str = _create_download_directory(CONFIG.namespace)
        download_batch_builder: AbstractDownloadBatchBuilder = (
            CLIENT.object_store_client.build_download_batch()
        )
        download_batch_builder.destination_folder = download_dir
        for object_path in object_paths_to_download:
            download_batch_builder.find_source_objects(
                namespace=CONFIG.namespace, object_name_pattern=f"{object_path.name}*"
            )
            download_batch = download_batch_builder.get_batch_if_objects_found()
            if download_batch is None:
                print_log(f"No Objects found in Object Path {object_path.displayName}")
                continue
            download_batch.start()
            future = download_batch.when_status_matches(
                lambda status: status == FileTransferStatus.Completed
            )
            CLIENT.object_store_client.start_transfers()
            futures.wait((future,))
            print_log(f"Downloaded all Objects in {object_path.displayName}")
        if len(object_paths_to_download) > 1:
            print_log(
                f"Downloaded all Objects in {len(object_paths_to_download)} Object Path(s)"
            )
    else:
        print_log("No Objects to download")
    # Clean up
    CLIENT.close()
    print_log("Done")


def _create_download_directory(namespace: str) -> str:
    """
    Create a new local download directory in the current working directory,
    using a sequence of names as follows to avoid over-writes:
       <namespace>, <namespace>.01, ..., <namespace>.99
    """
    new_dir = namespace
    if path.exists(new_dir):
        for index in range(1, 100):
            new_dir = namespace + "." + str(index).zfill(2)
            if not path.exists(new_dir):
                break
        else:
            raise Exception(f"Too many download directories for {namespace}")
    mkdir(new_dir)
    new_dir = path.abspath(new_dir)
    print_log(f"Created local download directory: {new_dir}")
    return new_dir


# Entry point
if __name__ == "__main__":
    main()
    exit(0)
