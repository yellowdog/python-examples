"""
Utility functions for rclone-backed data client commands:
yd-upload, yd-download, yd-delete, yd-ls.
"""

from pathlib import Path

from rclone_api import Config
from rclone_api.dir_listing import DirListing

from yellowdog_cli.utils.config_types import ConfigDataClient
from yellowdog_cli.utils.printing import print_info, print_warning
from yellowdog_cli.utils.rclone_utils import make_rclone, parse_rclone_config


def _require_remote(config: ConfigDataClient) -> str:
    """
    Return config.remote, raising a clear error if it is not set.
    """
    if not config.remote:
        raise Exception(
            "No rclone remote configured. "
            "Set 'remote' in the [dataClient] config section, "
            "via the YD_DATA_CLIENT_REMOTE environment variable, "
            "or with --remote."
        )
    return config.remote


def _rclone_for_config(config: ConfigDataClient):
    """
    Return (remote_name, Rclone) for the given data client config.
    """
    remote_str = _require_remote(config)
    remote_name, config_section = parse_rclone_config(remote_str)
    rclone = make_rclone(Config(config_section) if config_section is not None else None)
    return remote_name, rclone


def resolve_remote_path(
    config: ConfigDataClient,
    relative_path: str | None = None,
    filename: str | None = None,
) -> str:
    """
    Assemble a full rclone remote path from config plus an optional relative
    path or filename.

    If relative_path already starts with '<remote_name>:', it is returned
    verbatim (absolute rclone path).  Otherwise the path is assembled as:
        <remote_name>:<bucket>/<prefix>/<relative_path_or_filename>
    """
    remote_str = _require_remote(config)
    remote_name, _ = parse_rclone_config(remote_str)

    # Absolute rclone path — use verbatim
    if relative_path is not None and relative_path.startswith(f"{remote_name}:"):
        return relative_path

    parts: list[str] = []
    if config.bucket:
        parts.append(config.bucket.strip("/"))
    if config.prefix:
        parts.append(config.prefix.strip("/"))
    if relative_path:
        parts.append(relative_path.strip("/"))
    elif filename:
        parts.append(filename)

    return f"{remote_name}:{'/'.join(parts)}"


def upload_file(
    config: ConfigDataClient,
    local_path: Path,
    remote_path: str,
    dry_run: bool = False,
) -> None:
    """
    Upload a single local file to the given remote path.
    """
    if dry_run:
        print_info(f"Dry-run: Would upload '{local_path}' → '{remote_path}'")
        return

    _, rclone = _rclone_for_config(config)
    print_info(f"Uploading '{local_path}' → '{remote_path}'")
    result = rclone.copy_to(src=str(local_path.resolve()), dst=remote_path)
    if result.returncode != 0:
        raise Exception(f"Upload failed: {result.stderr}")


def _rclone_sync(rclone, src: str, dst: str):
    """
    Run 'rclone sync src dst', making dst an exact mirror of src.
    rclone_api has no sync wrapper, so we call the underlying _run directly.
    Performance flags match those hardcoded in rclone_api's copy().
    """
    return rclone.impl._run(
        [
            "sync",
            src,
            dst,
            "--checkers",
            "1000",
            "--transfers",
            "32",
            "--low-level-retries",
            "10",
        ],
        capture=False,
    )


def upload_directory(
    config: ConfigDataClient,
    local_path: Path,
    remote_path: str,
    flatten: bool = False,
    sync: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Upload a local directory to the given remote path.

    With flatten=True, all files are uploaded flat to the remote destination
    (no subdirectory structure preserved).
    With sync=True, the remote destination is made to mirror the local source
    (remote files not present locally are deleted).
    """
    if flatten:
        _upload_directory_flat(config, local_path, remote_path, dry_run)
        return

    action = "sync" if sync else "copy"
    if dry_run:
        print_info(
            f"Dry-run: Would {action} directory '{local_path}' → '{remote_path}'"
        )
        return

    _, rclone = _rclone_for_config(config)
    print_info(f"{'Syncing' if sync else 'Uploading'} '{local_path}' → '{remote_path}'")
    if sync:
        result = _rclone_sync(rclone, src=str(local_path.resolve()), dst=remote_path)
    else:
        result = rclone.copy(src=str(local_path.resolve()), dst=remote_path)
    if result.returncode != 0:
        raise Exception(f"Directory upload failed: {result.stderr}")


def _upload_directory_flat(
    config: ConfigDataClient,
    local_path: Path,
    remote_path: str,
    dry_run: bool,
) -> None:
    """
    Upload all files under local_path to remote_path without preserving
    directory structure (all files land directly under remote_path).
    """
    files = [f for f in local_path.rglob("*") if f.is_file()]
    if not files:
        print_info(f"No files found under '{local_path}'")
        return

    for local_file in files:
        dest = f"{remote_path.rstrip('/')}/{local_file.name}"
        upload_file(config, local_file, dest, dry_run=dry_run)


def download_files(
    config: ConfigDataClient,
    remote_path: str,
    local_destination: Path,
    flatten: bool = False,
    sync: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Download from remote_path to local_destination.

    remote_path may be a single file, a directory, or include glob patterns
    (delegated to rclone).  With flatten=True, all remote files are placed
    directly in local_destination without preserving directory structure.
    With sync=True, local files not present in the remote are deleted.
    """
    if flatten and sync:
        print_warning("--sync is not supported with --flatten; ignoring --sync")
        sync = False

    if dry_run:
        action = "sync" if sync else "download"
        print_info(f"Dry-run: Would {action} '{remote_path}' → '{local_destination}'")
        return

    listing = list_remote(config, remote_path)
    if not listing.dirs and not listing.files:
        print_warning(f"'{remote_path}' does not exist")
        return

    _, rclone = _rclone_for_config(config)
    dst = str(local_destination)

    if flatten:
        # Walk the remote path and download each file flat to the destination
        print_info(f"Downloading (flat) '{remote_path}' → '{local_destination}'")
        local_destination.mkdir(parents=True, exist_ok=True)
        for dir_listing in rclone.walk(remote_path):
            for f in dir_listing.files:
                file_dst = str(local_destination / f.name)
                result = rclone.copy_to(
                    src=f"{remote_path.rstrip('/')}/{f.path.path}", dst=file_dst
                )
                if result.returncode != 0:
                    raise Exception(
                        f"Download failed for '{f.path.path}': {result.stderr}"
                    )
    else:
        action = "Syncing" if sync else "Downloading"
        print_info(f"{action} '{remote_path}' → '{local_destination}'")
        if sync:
            result = _rclone_sync(rclone, src=remote_path, dst=dst)
        else:
            result = rclone.copy(src=remote_path, dst=dst)
        if result.returncode != 0:
            raise Exception(f"Download failed: {result.stderr}")


def delete_remote(
    config: ConfigDataClient,
    remote_path: str,
    recursive: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Delete a remote file or, with recursive=True, a directory tree.
    """
    if dry_run:
        action = "recursively delete" if recursive else "delete"
        print_info(f"Dry-run: Would {action} '{remote_path}'")
        return

    _, rclone = _rclone_for_config(config)

    if recursive:
        print_info(f"Deleting directory '{remote_path}'")
        result = rclone.purge(remote_path)
    else:
        listing = list_remote(config, remote_path)
        # When rclone lists a single file, it returns that file itself in the
        # listing (name == basename of the path).  Distinguish this from a
        # directory whose *contents* are listed (names differ from the path).
        if not listing.dirs and not listing.files:
            print_warning(f"'{remote_path}' does not exist")
            return
        basename = remote_path.rstrip("/").rsplit("/", 1)[-1].split(":")[-1]
        is_file = (
            not listing.dirs
            and len(listing.files) == 1
            and listing.files[0].name == basename
        )
        if not is_file and (listing.dirs or listing.files):
            print_warning(
                f"'{remote_path}' is a directory; use --recursive to delete it"
            )
            return
        print_info(f"Deleting '{remote_path}'")
        result = rclone.delete_files(remote_path)

    if result.returncode != 0:
        raise Exception(f"Delete failed: {result.stderr}")


def list_remote(
    config: ConfigDataClient,
    remote_path: str,
    recursive: bool = False,
) -> DirListing:
    """
    List files and directories at remote_path.

    Returns a DirListing with .files and .dirs attributes.
    With recursive=False, only the immediate contents are returned.
    """
    _, rclone = _rclone_for_config(config)
    max_depth = -1 if recursive else 1
    return rclone.ls(src=remote_path, max_depth=max_depth)
