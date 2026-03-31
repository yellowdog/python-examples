"""
Utility function to follow event streams.
"""

import signal
from collections.abc import Callable
from json import loads as json_loads
from threading import Thread
from time import sleep

import requests
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.entity_utils import (
    get_compute_requirement_id_by_worker_pool_id,
)
from yellowdog_cli.utils.printing import (
    CONSOLE,
    print_error,
    print_event,
    print_info,
    print_warning,
)
from yellowdog_cli.utils.settings import EVENT_STREAM_RETRY_INTERVAL
from yellowdog_cli.utils.wrapper import CLIENT, CONFIG_COMMON
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


class _WRNameColumn(ProgressColumn):
    """
    Renders the Work Requirement name (stored in task.fields["wr_name"]) in
    brackets with dim styling, for display after the progress bar.
    """

    def render(self, task) -> Text:
        name = task.fields.get("wr_name", "")
        return Text(f"[{name}]" if name else "", style="dim")


def follow_work_requirement_with_progress(ydid: str) -> None:
    """
    Follow a Work Requirement event stream, displaying a live Rich progress bar.

    Safe to call from either the main thread or a daemon thread; signal
    handling is skipped automatically when not in the main thread.
    """
    total_tasks = completed_tasks = failed_tasks = 0

    try:
        wr_name = CLIENT.work_client.get_work_requirement_by_id(ydid).name or ""
    except Exception:
        wr_name = ""

    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(
            complete_style="green4",
            finished_style="green4",
            pulse_style="deep_sky_blue4",
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        _WRNameColumn(),
        console=CONSOLE,
        transient=False,
    )
    bar_task = progress.add_task("Starting\u2026", total=None, wr_name=wr_name)

    def on_event(event: str, ydid_type: YDIDType) -> None:
        nonlocal total_tasks, completed_tasks, failed_tasks
        if not event.startswith("data:"):
            return
        try:
            event_data = json_loads(event[len("data:") :])
        except Exception:
            return
        if ydid_type is not YDIDType.WORK_REQUIREMENT:
            return

        new_total = new_completed = new_failed = 0
        for tg in event_data.get("taskGroups", []):
            summary = tg.get("taskSummary", {})
            new_total += summary.get("taskCount", 0)
            counts = summary.get("statusCounts", {})
            new_completed += counts.get("COMPLETED", 0)
            new_failed += counts.get("FAILED", 0) + counts.get("ABORTED", 0)

        total_tasks = new_total
        completed_tasks = new_completed
        failed_tasks = new_failed

        wr_status = event_data.get("status", "")
        done = completed_tasks + failed_tasks
        desc = f"{wr_status}  {done:,}/{total_tasks:,}"
        if failed_tasks:
            desc += f"  ({failed_tasks:,} failed)"

        progress.update(
            bar_task,
            total=total_tasks if total_tasks > 0 else None,
            completed=done,
            description=desc,
        )

    def _restore_cursor() -> None:
        try:
            CONSOLE.file.write("\033[?25h")
            CONSOLE.file.flush()
        except Exception:
            pass

    _original_sigint = signal.getsignal(signal.SIGINT)

    def _on_sigint(sig: int, frame) -> None:
        _restore_cursor()
        signal.signal(signal.SIGINT, _original_sigint)
        signal.default_int_handler(sig, frame)

    try:
        signal.signal(signal.SIGINT, _on_sigint)
        in_main_thread = True
    except ValueError:
        in_main_thread = False  # Signal handlers only work in the main thread

    print_info(f"Tracking progress for Work Requirement '{ydid}'")
    try:
        with progress:
            follow_events(ydid, YDIDType.WORK_REQUIREMENT, on_event=on_event)
    finally:
        if in_main_thread:
            signal.signal(signal.SIGINT, _original_sigint)
        _restore_cursor()

    if failed_tasks:
        print_warning(
            f"Work Requirement finished with {failed_tasks:,} failed/aborted task(s)"
        )


def follow_ids(ydids: list[str], auto_cr: bool = False):
    """
    Creates an event thread for each YDID passed on the command line.
    """
    if len(ydids) == 0:
        return

    ydids_set = set(ydids)  # Eliminate duplicates
    num_duplicates = len(ydids) - len(ydids_set)
    if num_duplicates > 0:
        print_warning(f"Ignoring {num_duplicates} duplicate YellowDog ID(s)")

    if auto_cr:
        # Automatically add Compute Requirement IDs for
        # Provisioned Worker Pools, to follow both
        cr_ydids = set()
        for ydid in ydids_set:
            if get_ydid_type(ydid) == YDIDType.WORKER_POOL:
                cr_ydid = get_compute_requirement_id_by_worker_pool_id(CLIENT, ydid)
                if cr_ydid is not None:
                    print_info(
                        f"Adding event stream for Compute Requirement '{cr_ydid}'"
                    )
                    cr_ydids.add(cr_ydid)
        ydids_set = ydids_set.union(cr_ydids)

    print_info(f"Following the event stream(s) for {len(ydids_set)} YellowDog ID(s)")

    threads: list[Thread] = []

    for ydid in ydids_set:
        ydid_type = get_ydid_type(ydid)
        if ydid_type not in [
            YDIDType.WORK_REQUIREMENT,
            YDIDType.WORKER_POOL,
            YDIDType.COMPUTE_REQUIREMENT,
        ]:
            print_error(
                f"Invalid YellowDog ID '{ydid}' (Must be valid YDID for Work"
                " Requirement, Worker Pool or Compute Requirement)"
            )
            continue

        if ARGS_PARSER.progress and ydid_type == YDIDType.WORK_REQUIREMENT:
            target, args = follow_work_requirement_with_progress, (ydid,)
        else:
            target, args = follow_events, (ydid, ydid_type)
        thread = Thread(target=target, args=args, daemon=True)
        try:
            thread.start()
        except RuntimeError as e:
            print_error(f"Unable to start event thread for '{ydid}': ({e})")
            continue
        threads.append(thread)

    # Install a SIGINT handler in the main thread so that Ctrl-C restores the
    # terminal cursor even if Rich's Live context is running in a daemon thread
    # (signal handlers can only be installed from the main thread).
    _original_sigint = signal.getsignal(signal.SIGINT)
    if ARGS_PARSER.progress and threads:

        def _on_sigint(sig, frame):
            try:
                CONSOLE.file.write("\033[?25h")
                CONSOLE.file.flush()
            except Exception:
                pass
            signal.signal(signal.SIGINT, _original_sigint)
            signal.default_int_handler(sig, frame)

        signal.signal(signal.SIGINT, _on_sigint)

    for thread in threads:
        thread.join()

    if ARGS_PARSER.progress:
        signal.signal(signal.SIGINT, _original_sigint)

    if len(threads) > 1 and not ARGS_PARSER.print_pid:
        print_info("All event streams have concluded")


def follow_events(
    ydid: str,
    ydid_type: YDIDType,
    on_event: Callable[[str, YDIDType], None] | None = None,
):
    """
    Follow events for a single YDID.

    If on_event is provided it is called for each raw SSE line instead of
    print_event(), allowing callers to handle events themselves (e.g. to
    update a progress bar).
    """
    while True:
        response = requests.get(
            headers={
                "Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"
            },
            url=get_event_url(ydid, ydid_type),
            stream=True,
        )

        if response.status_code != 200:
            try:
                error_text = response.json()["message"]
            except Exception:
                error_text = "(JSON error cannot be decoded)"
            print_error(f"'{ydid}': {error_text}")
            break

        if response.encoding is None:
            response.encoding = "utf-8"

        try:
            for event in response.iter_lines(decode_unicode=True):
                if event:
                    if on_event is not None:
                        on_event(event, ydid_type)
                    else:
                        print_event(event, ydid_type)
            break

        except Exception as e:
            if "Connection broken" in str(e):
                print_warning(
                    f"Event stream interruption for '{ydid}' "
                    f"(retrying in {EVENT_STREAM_RETRY_INTERVAL}s)"
                )
                sleep(EVENT_STREAM_RETRY_INTERVAL)
                continue
            else:
                print_error(f"Event stream error: {e}")
                break

    print_info(f"Event stream concluded for '{ydid}'")


def get_event_url(ydid: str, ydid_type: YDIDType) -> str | None:
    """
    Get the event stream URL.
    """
    if ydid_type is YDIDType.WORK_REQUIREMENT:
        return f"{CONFIG_COMMON.url}/work/requirements/{ydid}/updates"
    if ydid_type == YDIDType.WORKER_POOL:
        return f"{CONFIG_COMMON.url}/workerPools/{ydid}/updates"
    if ydid_type == YDIDType.COMPUTE_REQUIREMENT:
        return f"{CONFIG_COMMON.url}/compute/requirements/{ydid}/updates"
    return None
