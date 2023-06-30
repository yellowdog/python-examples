#!/usr/bin/env python3

"""
A script to download YellowDog Object Store objects.
"""

from concurrent import futures
from pathlib import Path
from typing import List

from yellowdog_client.model import ObjectPath, ObjectPathsRequest
from yellowdog_client.object_store.download.abstracts.abstract_download_batch_builder import (
    AbstractDownloadBatchBuilder,
    AbstractTransferBatch,
)
from yellowdog_client.object_store.model import FileTransferStatus

from yd_commands.config import unpack_namespace_in_prefix
from yd_commands.interactive import confirmed, select
from yd_commands.printing import print_log
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    namespace, tag = unpack_namespace_in_prefix(
        CONFIG_COMMON.namespace, CONFIG_COMMON.name_tag
    )
    print_log(
        f"Downloading all Objects in namespace '{namespace}' and "
        f"names starting with '{tag}'"
    )

    object_paths_to_download: List[ObjectPath] = (
        CLIENT.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(namespace=namespace, prefix=tag, flat=ARGS_PARSER.all)
        )
    )

    if len(object_paths_to_download) > 0:
        object_paths_to_download = select(CLIENT, object_paths_to_download)

    if len(object_paths_to_download) == 0:
        print_log("No Objects to download")
        return

    if not confirmed(f"Download {len(object_paths_to_download)} Object Path(s)?"):
        return

    print_log(f"{len(object_paths_to_download)} Object Path(s) to Download")

    download_dir: str = _create_download_directory(
        namespace if ARGS_PARSER.directory == "" else ARGS_PARSER.directory
    )

    for object_path in object_paths_to_download:
        download_batch_builder: AbstractDownloadBatchBuilder = (
            CLIENT.object_store_client.build_download_batch()
        )
        download_batch_builder.destination_folder = download_dir
        download_batch_builder.find_source_objects(
            namespace=namespace,
            object_name_pattern=f"{object_path.name}*",
        )
        download_batch: AbstractTransferBatch = (
            download_batch_builder.get_batch_if_objects_found()
        )
        if download_batch is None:
            print_log(f"No Objects found in Object Path {object_path.displayName}")
            continue
        download_batch.start()
        future: futures.Future = download_batch.when_status_matches(
            lambda status: status == FileTransferStatus.Completed
        )
        CLIENT.object_store_client.start_transfers()
        futures.wait((future,))
        print_log(f"Downloaded {object_path.displayName}")

    print_log(
        f"Downloaded all Objects in {len(object_paths_to_download)} Object Path(s)"
    )


def _create_download_directory(directory_name: str) -> str:
    """
    Create a new local download directory in the current working directory,
    if it doesn't exist, and return the absolute pathname.
    """
    path = Path(directory_name).resolve()
    if path.exists():
        print_log(f"Downloading to existing directory: '{path}'")
    else:
        print_log(f"Creating download directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


# Entry point
if __name__ == "__main__":
    main()
