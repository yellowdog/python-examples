"""
Utility functions for uploading objects.
"""

from os import name as os_name
from os.path import basename
from pathlib import Path
from typing import Optional

from yellowdog_client import PlatformClient
from yellowdog_client.object_store.model import FileTransferStatus

from yd_commands.printing import print_log
from yd_commands.settings import NAMESPACE_PREFIX_SEPARATOR
from yd_commands.utils import link


def upload_file(
    client: PlatformClient,
    filename: str,
    id: str,
    namespace: str,
    url: str,
    inputs_folder_name: Optional[str] = None,
    flatten_upload_paths: bool = False,
) -> bool:
    """
    Upload a local file to the YD Object Store using a calculated
    unique upload pathname.
    """

    dest_filename = unique_upload_pathname(
        filename=filename,
        id=id,
        inputs_folder_name=inputs_folder_name,
        flatten_upload_paths=flatten_upload_paths,
    )

    upload_file_core(
        client=client,
        url=url,
        local_file=filename,
        namespace=namespace,
        remote_file=dest_filename,
    )
    return True


def unique_upload_pathname(
    filename: str,
    id: str,
    inputs_folder_name: Optional[str],
    urlencode_forward_slash: bool = False,
    flatten_upload_paths: bool = False,
) -> str:
    """
    Maps the local filename into a uniquely identified upload object
    in the YD Object Store. Optionally replaces forward slashes for use
    in URLs.
    """

    if os_name == "nt":
        # Convert Windows path naming to Unix style for upload
        filename = filename.replace(":", "_").replace("\\", "/")

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
    if inputs_folder_name is not None:
        return prefix + inputs_folder_name + forward_slash + filename
    else:
        return prefix + filename


def upload_file_core(
    client: PlatformClient, url: str, local_file: str, namespace: str, remote_file: str
):
    """
    Core object upload action, without upload pathname processing.
    """
    pathname = Path(local_file)
    if not pathname.is_file():
        raise Exception(f"File '{pathname.name}' not found or not a regular file")

    client.object_store_client.start_transfers()
    session = client.object_store_client.create_upload_session(
        file_namespace=namespace,
        source_file_path=local_file,
        destination_file_name=remote_file,
    )
    session.start()

    # Wait for upload to complete
    session = session.when_status_matches(lambda status: status.is_finished()).result()

    if session.status != FileTransferStatus.Completed:
        raise Exception(f"Failed to upload file: {local_file}")

    print_log(
        f"Uploaded file '{local_file}' to"
        f" '{namespace}{NAMESPACE_PREFIX_SEPARATOR}{remote_file}'"
    )
    remote_file = remote_file.replace("/", "%2F")
    link_ = link(
        url,
        f"#/objects/{namespace}/{remote_file}?object=true",
    )
    print_log(f"Object URL: {link_}")
