#!/usr/bin/env python3

"""
A script to download YellowDog Object Store objects.
"""

from concurrent import futures
from pathlib import Path
from typing import Optional

from yellowdog_client.object_store.download.download_batch_builder import (
    AbstractTransferBatch,
    DownloadBatchBuilder,
    FlattenPath,
)
from yellowdog_client.object_store.model import FileTransferStatus

from yd_commands.interactive import confirmed, select
from yd_commands.object_utilities import list_matching_object_paths
from yd_commands.printing import print_batch_download_files, print_log
from yd_commands.utils import unpack_namespace_in_prefix
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    # Direct command line argument overrides tag/prefix
    if len(ARGS_PARSER.object_paths_to_download) > 0:
        for object_path in ARGS_PARSER.object_paths_to_download:
            namespace, tag = unpack_namespace_in_prefix(
                namespace=CONFIG_COMMON.namespace,
                prefix=object_path,
            )
            download_object_paths(
                namespace, tag, ARGS_PARSER.object_path_pattern, ARGS_PARSER.all
            )
        return

    # Use tag/prefix
    namespace, tag = unpack_namespace_in_prefix(
        namespace=CONFIG_COMMON.namespace, prefix=CONFIG_COMMON.name_tag
    )
    download_object_paths(
        namespace, tag, ARGS_PARSER.object_path_pattern, ARGS_PARSER.all
    )
    return


def download_object_paths(
    namespace: str, prefix: str, pattern: Optional[str], flat: bool
):
    """
    Download Object Paths matching namespace, prefix and pattern.
    """
    print_log(
        f"Downloading Objects in namespace '{namespace}' and "
        f"prefix starting with '{prefix}'"
        + ("" if pattern is None else f", matching name pattern '{pattern}'")
    )

    object_paths_to_download = list_matching_object_paths(
        CLIENT, namespace, prefix, flat
    )

    if len(object_paths_to_download) == 0:
        print_log("No matching Object Paths")
        return

    object_paths_to_download = select(CLIENT, object_paths_to_download)

    if len(object_paths_to_download) == 0:
        print_log("No Objects Paths to include")
        return

    print_log("Note: existing local objects will be overwritten without warning")
    if not confirmed(
        f"Download matching objects in {len(object_paths_to_download)} Object Path(s)?"
    ):
        return

    print_log(f"{len(object_paths_to_download)} Object Path(s) to include")

    download_dir: str = _create_download_directory(
        "." if ARGS_PARSER.directory == "" else ARGS_PARSER.directory
    )

    download_batch_builder: DownloadBatchBuilder = (
        CLIENT.object_store_client.build_download_batch()
    )
    download_batch_builder.destination_folder = download_dir
    if ARGS_PARSER.flatten_download_paths:
        download_batch_builder.set_flatten_file_name_mapper(FlattenPath.FILE_NAME_ONLY)

    for object_path in object_paths_to_download:
        object_name_pattern = (
            f"{object_path.name}*"
            if pattern is None
            else f"{object_path.name}{pattern.lstrip('/')}"
        )
        print_log(f"Finding object paths matching '{object_name_pattern}'")
        download_batch_builder.find_source_objects(
            namespace=namespace,
            object_name_pattern=object_name_pattern,
        )

    download_batch: AbstractTransferBatch = (
        download_batch_builder.get_batch_if_objects_found()
    )

    if download_batch is None:
        print_log(f"No matching Objects found in included Object Paths")
        return

    object_count = print_batch_download_files(
        download_batch_builder, ARGS_PARSER.flatten_download_paths
    )

    print_log("Starting batch download")
    download_batch.start()
    future: futures.Future = download_batch.when_status_matches(
        lambda status: status == FileTransferStatus.Completed
    )
    CLIENT.object_store_client.start_transfers()
    futures.wait((future,))

    print_log(f"Downloaded {object_count} Object(s)")


def _create_download_directory(directory_name: str) -> str:
    """
    Create a new local download directory in the current working directory,
    if it doesn't exist, and return the absolute pathname.
    """
    path = Path(directory_name).resolve()
    if path.exists():
        print_log(f"Downloading to existing directory: '{path}'")
    else:
        print_log(f"Creating download directory: '{path}'")
        path.mkdir(parents=True, exist_ok=True)
    return str(path)


# Entry point
if __name__ == "__main__":
    main()
