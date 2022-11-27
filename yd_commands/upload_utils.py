"""
Utility functions for uploading objects.
"""

from os.path import basename
from pathlib import Path
from typing import Optional

from yellowdog_client import PlatformClient
from yellowdog_client.object_store.model import FileTransferStatus

from yd_commands.config import link
from yd_commands.printing import print_error, print_log


def upload_file(
    client: PlatformClient,
    filename: str,
    id: str,
    namespace: str,
    url: str,
    input_folder_name: Optional[str] = None,
    flatten_upload_paths: bool = False,
):
    """
    Upload a local file to the YD Object Store.
    """
    pathname = Path(filename)
    if not pathname.is_file():
        raise Exception(f"File '{pathname.name}' not found or not a regular file")

    dest_filename = unique_upload_pathname(
        filename,
        id=id,
        input_folder_name=input_folder_name,
        flatten_upload_paths=flatten_upload_paths,
    )
    client.object_store_client.start_transfers()
    session = client.object_store_client.create_upload_session(
        namespace,
        str(pathname),
        destination_file_name=dest_filename,
    )
    session.start()
    # Wait for upload to complete
    session = session.when_status_matches(lambda status: status.is_finished()).result()
    if session.status != FileTransferStatus.Completed:
        print_error(f"Failed to upload file: {filename}")
        # Continue here?
    else:
        uploaded_pathname = unique_upload_pathname(
            filename,
            id=id,
            input_folder_name=input_folder_name,
            urlencode_forward_slash=True,
            flatten_upload_paths=flatten_upload_paths,
        )
        link_ = link(
            url,
            f"#/objects/{namespace}/{uploaded_pathname}?object=true",
        )
        print_log(f"Uploaded file '{filename}': {link_}")


def unique_upload_pathname(
    filename: str,
    id: str,
    input_folder_name: Optional[str],
    urlencode_forward_slash: bool = False,
    flatten_upload_paths: bool = False,
) -> str:
    """
    Maps the local filename into a uniquely identified upload object
    in the YD Object Store. Optionally replaces forward slashes.
    """
    forward_slash = "%2F" if urlencode_forward_slash else "/"
    prefix = "" if id == "" else id + forward_slash

    if flatten_upload_paths:
        # Use the root of the Work Requirement directory
        return prefix + basename(filename)

    # Rework the filename
    double_dots = filename.count("..")  # Use to disambiguate relative paths
    filename = filename.replace("../", "").replace("./", "").replace("//", "/")
    filename = filename[1:] if filename[0] == "/" else filename
    filename = str(double_dots) + "/" + filename if double_dots != 0 else filename
    if urlencode_forward_slash is True:
        filename = filename.replace("/", forward_slash)
    if input_folder_name is not None:
        return prefix + input_folder_name + forward_slash + filename
    else:
        return prefix + filename
