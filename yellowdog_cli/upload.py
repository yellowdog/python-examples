#!/usr/bin/env python3

"""
A script to upload files to the YellowDog Object Store.
"""

from concurrent import futures
from glob import glob
from os import chdir
from os import name as os_name
from os import walk as os_walk
from os.path import join as os_path_join
from pathlib import Path

from yellowdog_client.object_store.abstracts import AbstractTransferBatch
from yellowdog_client.object_store.model import FileTransferStatus
from yellowdog_client.object_store.upload import UploadBatchBuilder

from yellowdog_cli.utils.misc_utils import unpack_namespace_in_prefix
from yellowdog_cli.utils.printing import print_batch_upload_files, print_log
from yellowdog_cli.utils.upload_utils import upload_file
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if ARGS_PARSER.content_path is not None and ARGS_PARSER.content_path != "":
        try:
            chdir(ARGS_PARSER.content_path)
            print_log(
                "Uploading files relative to local directory:"
                f" '{ARGS_PARSER.content_path}'"
            )
        except Exception as e:
            raise Exception(
                "Unable to switch to content directory"
                f" '{ARGS_PARSER.content_path}': {e}"
            )

    namespace, prefix = unpack_namespace_in_prefix(
        CONFIG_COMMON.namespace, CONFIG_COMMON.name_tag
    )

    if ARGS_PARSER.batch:  # Use the batch uploader
        print_log(
            f"Batch uploading Using Object Store namespace '{namespace}' (prefix"
            f" '{prefix}' is ignored for batch upload)"
        )
        if ARGS_PARSER.recursive or ARGS_PARSER.flatten:
            print_log(
                "Warning: '--recursive', '--flatten-upload-paths' options are ignored"
                " for batch upload"
            )
        for file_pattern in ARGS_PARSER.files:
            # Remove quotes passed through by the shell
            file_pattern = file_pattern.lstrip("'\"").rstrip("'\"")
            # Compensate for issues with file matching by prepending an initial
            # '.\' or './' when a path is not explicitly supplied
            if not (
                file_pattern.startswith("/")
                or file_pattern.startswith("\\")
                or file_pattern.startswith("./")
                or file_pattern.startswith(".\\")
            ):
                if os_name == "nt":
                    file_pattern = f".\\{file_pattern}"
                else:
                    file_pattern = f"./{file_pattern}"
            print_log(f"Uploading files matching '{file_pattern}'")

            upload_batch_builder: UploadBatchBuilder = (
                CLIENT.object_store_client.build_upload_batch()
            )
            upload_batch_builder.find_source_objects(
                ".",
                file_pattern,
            )
            upload_batch_builder.namespace = namespace
            upload_batch: AbstractTransferBatch = (
                upload_batch_builder.get_batch_if_objects_found()
            )
            print_batch_upload_files(upload_batch_builder)
            if upload_batch is not None:
                upload_batch.start()
                future: futures.Future = upload_batch.when_status_matches(
                    lambda status: status == FileTransferStatus.Completed
                )
                CLIENT.object_store_client.start_transfers()
                futures.wait((future,))
                print_log("Batch upload complete")
            else:
                print_log(f"No objects matching '{file_pattern}'")
        return

    # Use the sequential uploader
    print_log(f"Using Object Store namespace '{namespace}' and prefix '{prefix}'")
    files_set = set(ARGS_PARSER.files)
    if os_name == "nt":
        # Windows wildcard expansion (not done natively by the Windows shell)
        files_set = {f for files in files_set for f in glob(files)}

    if len(files_set) == 0:
        print_log("No files to upload")
        return

    added_files_set = set()
    removed_dirs_set = set()

    for file_or_dir in files_set:
        pathname = Path(file_or_dir)
        if not pathname.exists():
            raise Exception(f"'{file_or_dir}' doesn't exist")
        if pathname.is_dir():
            if not ARGS_PARSER.recursive:
                raise Exception(
                    f"'{file_or_dir}' is a directory; please use '--recursive/-r'"
                )
            else:
                removed_dirs_set.add(file_or_dir)
                for dir_path, dirs, files in os_walk(file_or_dir):
                    for file in files:
                        added_files_set.add(os_path_join(dir_path, file))

    files_set = files_set.union(added_files_set).difference(removed_dirs_set)

    if ARGS_PARSER.flatten:
        print_log("Flattening upload paths")

    uploaded_file_count = 0
    for file in files_set:
        if (
            upload_file(
                client=CLIENT,
                filename=file,
                id=prefix,
                namespace=namespace,
                url=CONFIG_COMMON.url,
                flatten_upload_paths=ARGS_PARSER.flatten,
            )
            is True
        ):
            uploaded_file_count += 1
    print_log(f"Uploaded {uploaded_file_count} files")


# Standalone entry point
if __name__ == "__main__":
    main()
