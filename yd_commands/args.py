#!/usr/bin/env python3

"""
Class to parse command line arguments.
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from yd_commands.__init__ import __version__
from yd_commands.version import DOCS_URL


def docs():
    print(
        f"Online documentation for Python Examples v{__version__}: {DOCS_URL}",
        flush=True,
    )


class CLIParser:
    def __init__(self, description: Optional[str] = None):
        """
        Create the argument parser, and parse the command
        line arguments. Argument availability depends on module.
        """
        parser = argparse.ArgumentParser(description=description)

        # Common arguments across all commands
        parser.add_argument(
            "--docs",
            action="store_true",
            required=False,
            help="provide a link to the documentation for this version",
        )
        parser.add_argument(
            "--config",
            "-c",
            required=False,
            type=str,
            help=(
                "configuration file in TOML format; "
                "default is 'config.toml' in the current directory"
            ),
            metavar="<config_file.toml>",
        )
        parser.add_argument(
            "--key",
            "-k",
            type=str,
            required=False,
            help="the YellowDog Application key",
            metavar="<app-key>",
        )
        parser.add_argument(
            "--secret",
            "-s",
            required=False,
            type=str,
            help="the YellowDog Application secret",
            metavar="<app-secret>",
        )
        parser.add_argument(
            "--namespace",
            "-n",
            type=str,
            required=False,
            help="the namespace to use when creating and identifying entities",
            metavar="<namespace>",
        )
        parser.add_argument(
            "--tag",
            "-t",
            "--prefix",
            type=str,
            required=False,
            help="the tag/prefix for naming or selecting entities",
            metavar="<tag>",
        )
        parser.add_argument(
            "--url",
            "-u",
            type=str,
            required=False,
            help="the URL of the YellowDog Platform API",
            metavar="<url>",
        )
        parser.add_argument(
            "--variable",
            "-v",
            type=str,
            required=False,
            action="append",
            help="user-defined variable substitutions; can be supplied multiple times",
            metavar="<var1=v1>",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            required=False,
            help="suppress (non-error, non-interactive) status and progress messages",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            required=False,
            help="print a stack trace (etc.) on error",
        )
        parser.add_argument(
            "--pac",
            action="store_true",
            required=False,
            help="enable PAC (proxy auto-configuration) support",
        )

        # Module-specific argument sets

        if any(module in sys.argv[0] for module in ["submit"]):
            parser.add_argument(
                "--work-requirement",
                "-r",
                type=str,
                required=False,
                help="submit a work requirement definition file in JSON format",
                metavar="<work_requirement.json>",
            )
            parser.add_argument(
                "--json-raw",
                "-j",
                type=str,
                required=False,
                help="submit a 'raw' JSON work requirement file",
                metavar="<raw_work_requirement.json>",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow the work requirement's progress to completion",
            )
            parser.add_argument(
                "--executable",
                "-X",
                type=str,
                required=False,
                help="the executable to use",
                metavar="<executable>",
            )
            parser.add_argument(
                "--task-type",
                "-T",
                type=str,
                required=False,
                help="the task type to use",
                metavar="<task_type>",
            )
            parser.add_argument(
                "--task-count",
                "-C",
                type=int,
                required=False,
                help="the number of times to submit the task",
                metavar="<task_count>",
            )
            parser.add_argument(
                "--task-batch-size",
                "-b",
                type=int,
                required=False,
                help="the batch size for task submission",
                metavar="<batch_size>",
            )
            parser.add_argument(
                "--pause-between-batches",
                "-P",
                action="store_true",
                required=False,
                help="pause for user input between batches (for debugging)",
            )
            parser.add_argument(
                "--csv-file",
                "-V",
                type=str,
                required=False,
                action="append",
                help="the CSV file(s) from which to read task data",
                metavar="<data.csv>",
            )
            parser.add_argument(
                "--process-csv-only",
                "-p",
                action="store_true",
                required=False,
                help=(
                    "process CSV variable substitutions only and output intermediate"
                    " JSON"
                ),
            )

        if any(module in sys.argv[0] for module in ["provision", "instantiate"]):
            parser.add_argument(
                "--worker-pool",
                "-p",
                type=str,
                required=False,
                help="worker pool definition file in JSON format",
                metavar="<worker_pool.json>",
            )

        if any(module in sys.argv[0] for module in ["cancel"]):
            parser.add_argument(
                "--abort",
                "-a",
                action="store_true",
                required=False,
                help="abort all running tasks with immediate effect",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="when using --abort, poll until all Tasks have been aborted",
            )

        if any(
            module in sys.argv[0]
            for module in [
                "cancel",
                "delete",
                "download",
                "shutdown",
                "terminate",
            ]
        ):
            parser.add_argument(
                "--interactive",
                "-i",
                action="store_true",
                required=False,
                help="list, and interactively select, items to act on",
            )

        if any(
            module in sys.argv[0]
            for module in [
                "abort",
                "cancel",
                "delete",
                "shutdown",
                "terminate",
                "resize",
            ]
        ):
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="perform destructive actions without requiring user confirmation",
            )

        if "download" in sys.argv[0]:
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="download without requiring user confirmation",
            )
            parser.add_argument(
                "--directory",
                "-d",
                type=str,
                required=False,
                help=(
                    "the directory to use for downloaded objects (namespace is default)"
                ),
                metavar="<directory>",
            )

        if any(module in sys.argv[0] for module in ["delete", "download"]):
            parser.add_argument(
                "--all",
                "-a",
                action="store_true",
                required=False,
                help="list all objects, not just the top level",
            )

        if "list" in sys.argv[0]:
            parser.add_argument(
                "--object-paths",
                "--objects",
                "-o",
                action="store_true",
                required=False,
                help="list YellowDog Object Store object paths",
            )
            parser.add_argument(
                "--all",
                "-a",
                action="store_true",
                required=False,
                help=(
                    "when used with '--objects', list all objects, not just the top"
                    " level structure"
                ),
            )
            parser.add_argument(
                "--details",
                "-d",
                action="store_true",
                required=False,
                help=(
                    "when used with '--objects', select objects from the list of"
                    " matches and show their details"
                ),
            )
            parser.add_argument(
                "--work-requirements",
                "-w",
                action="store_true",
                required=False,
                help="list Work Requirements",
            )
            parser.add_argument(
                "--task-groups",
                "-g",
                action="store_true",
                required=False,
                help="list Task Groups in selected Work Requirements",
            )
            parser.add_argument(
                "--tasks",
                "-T",
                action="store_true",
                required=False,
                help="list Tasks in selected Work Requirements",
            )
            parser.add_argument(
                "--worker-pools",
                "-p",
                action="store_true",
                required=False,
                help="list Worker Pools",
            )
            parser.add_argument(
                "--compute-requirements",
                "-r",
                action="store_true",
                required=False,
                help="list Compute Requirements",
            )
            parser.add_argument(
                "--live-only",
                "-l",
                action="store_true",
                required=False,
                help="list only running requirements/pools",
            )

        if "upload" in sys.argv[0]:
            parser.add_argument(
                "--content-path",
                "-C",
                type=str,
                required=False,
                help="the path where the items to be uploaded are found",
                metavar="<directory>",
            )
            parser.add_argument(
                "filenames",
                metavar="<filename>",
                type=str,
                nargs="+",
                help="files and/or directories to upload to the Object Store",
            )
            parser.add_argument(
                "--flatten-upload-paths",
                "-f",
                action="store_true",
                required=False,
                help="flatten/remove local directories when uploading files",
            )
            parser.add_argument(
                "--recursive",
                "-r",
                action="store_true",
                required=False,
                help="recursively upload files from directories",
            )
            parser.add_argument(
                "--batch",
                "-b",
                action="store_true",
                required=False,
                help=(
                    "use batch upload; file_patterns must contain wildcards and "
                    "be quoted to prevent shell expansion"
                ),
            )

        if any(
            module in sys.argv[0] for module in ["submit", "provision", "instantiate"]
        ):
            parser.add_argument(
                "--dry-run",
                "-D",
                action="store_true",
                required=False,
                help="dry-run the action and print the JSON that would be submitted",
            )

        if any(module in sys.argv[0] for module in ["instantiate"]):
            parser.add_argument(
                "--compute-requirement",
                "-C",
                type=str,
                required=False,
                help="the compute requirement definition",
                metavar="<compute_requirement.json>",
            )
            parser.add_argument(
                "--report",
                "-r",
                action="store_true",
                required=False,
                help="report on a Dynamic Template test run",
            )

        if "admin" in sys.argv[0]:
            parser.add_argument(
                "work_requirement_id",
                metavar="<work_requirement_id>",
                type=str,
                nargs="*",
                help="work requirement to be refreshed",
            )

        if any(
            module in sys.argv[0] for module in ["submit", "provision", "instantiate"]
        ):
            parser.add_argument(
                "--jsonnet-dry-run",
                "-J",
                action="store_true",
                required=False,
                help="dry-run Jsonnet processing into JSON",
            )

        if "resize" in sys.argv[0]:
            parser.add_argument(
                "worker_pool",
                metavar="<worker-pool-or-compute-requirement-name-or-ID>",
                type=str,
                help=(
                    "the name or YellowDog ID of the Worker Pool or Compute Requirement"
                    " to resize"
                ),
            )
            parser.add_argument(
                "worker_pool_size",
                metavar="<new-node/instance-count>",
                type=int,
                help="the desired number of (total) nodes in the Worker Pool",
            )
            parser.add_argument(
                "--compute-requirement",
                "-C",
                action="store_true",
                required=False,
                help="resize a Compute Requirement instead of a Worker Pool",
            )

        if "shutdown" in sys.argv[0]:
            parser.add_argument(
                "worker_pool",
                nargs="?",
                default="",
                metavar="<worker-pool-name-or-ID>",
                type=str,
                help="the name or YellowDog ID of the Worker Pool",
            )

        if "terminate" in sys.argv[0]:
            parser.add_argument(
                "compute_requirement",
                nargs="?",
                default="",
                metavar="<compute-requirement-name-or-ID>",
                type=str,
                help="the name or YellowDog ID of the Compute Requirement",
            )

        if "cancel" in sys.argv[0]:
            parser.add_argument(
                "work_requirement",
                nargs="?",
                default="",
                metavar="<work-requirement-name-or-ID>",
                type=str,
                help="the name or YellowDog ID of the Work Requirement",
            )

        self.args = parser.parse_args()

        if self.args.docs:
            docs()
            exit(0)

        # Temporary notification message while we figure out the problem
        # with the use of concurrent futures in Python 3.10+
        if (
            any(module in sys.argv[0] for module in ["submit"])
            and self.args.follow
            and sys.version_info >= (3, 10)
        ):
            print(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ":",
                (
                    "Note: the '--follow' ('-f') option is partially supported "
                    "for Python versions 3.10 and above"
                ),
            )

    @property
    def config_file(self) -> Optional[str]:
        return self.args.config

    @property
    def key(self) -> Optional[str]:
        return self.args.key

    @property
    def secret(self) -> Optional[str]:
        return self.args.secret

    @property
    def namespace(self) -> Optional[str]:
        return self.args.namespace

    @property
    def tag(self) -> Optional[str]:
        return self.args.tag

    @property
    def url(self) -> Optional[str]:
        return self.args.url

    @property
    def variables(self) -> Optional[List[str]]:
        return self.args.variable

    @property
    def quiet(self) -> bool:
        return self.args.quiet

    @property
    def work_req_file(self) -> Optional[str]:
        return self.args.work_requirement

    @property
    def executable(self) -> Optional[str]:
        return self.args.executable

    @property
    def task_type(self) -> Optional[str]:
        return self.args.task_type

    @property
    def worker_pool_file(self) -> Optional[str]:
        return self.args.worker_pool

    @property
    def follow(self) -> Optional[bool]:
        return self.args.follow

    @property
    def abort(self) -> Optional[bool]:
        return self.args.abort

    @property
    def interactive(self) -> Optional[bool]:
        return self.args.interactive

    @interactive.setter
    def interactive(self, interactive: bool):
        self.args.interactive = interactive

    @property
    def yes(self) -> Optional[bool]:
        # This attribute is used in 'submit' without the '--yes' option
        # being enabled for that module. Ensure that 'None' is returned.
        try:
            return self.args.yes
        except AttributeError:
            return None

    @property
    def object_paths(self) -> Optional[bool]:
        return self.args.object_paths

    @property
    def work_requirements(self) -> Optional[bool]:
        return self.args.work_requirements

    @property
    def task_groups(self) -> Optional[bool]:
        return self.args.task_groups

    @property
    def tasks(self) -> Optional[bool]:
        return self.args.tasks

    @property
    def worker_pools(self) -> Optional[bool]:
        return self.args.worker_pools

    @property
    def compute_requirements(self) -> Optional[bool]:
        return self.args.compute_requirements

    @property
    def live_only(self) -> Optional[bool]:
        return self.args.live_only

    @property
    def all(self) -> Optional[bool]:
        return self.args.all

    @property
    def details(self) -> Optional[bool]:
        return self.args.details

    @property
    def debug(self) -> Optional[bool]:
        return self.args.debug

    @property
    def use_pac(self) -> Optional[bool]:
        return self.args.pac

    @property
    def directory(self) -> str:
        return "" if self.args.directory is None else self.args.directory

    @property
    def files(self) -> List[str]:
        return self.args.filenames

    @property
    def flatten(self) -> Optional[bool]:
        return self.args.flatten_upload_paths

    @property
    def recursive(self) -> Optional[bool]:
        return self.args.recursive

    @property
    def batch(self) -> Optional[bool]:
        return self.args.batch

    @property
    def dry_run(self) -> Optional[bool]:
        return self.args.dry_run

    @property
    def json_raw(self) -> Optional[str]:
        return self.args.json_raw

    @property
    def compute_requirement(self) -> Optional[str]:
        return self.args.compute_requirement

    @property
    def task_count(self) -> Optional[int]:
        return self.args.task_count

    @property
    def csv_files(self) -> Optional[List[str]]:
        return self.args.csv_file

    @property
    def process_csv_only(self) -> Optional[bool]:
        return self.args.process_csv_only

    @property
    def wr_ids(self) -> Optional[List[str]]:
        return self.args.work_requirement_id

    @property
    def task_batch_size(self) -> Optional[int]:
        return self.args.task_batch_size

    @property
    def content_path(self) -> Optional[str]:
        return self.args.content_path

    @property
    def report(self) -> Optional[bool]:
        return self.args.report

    @property
    def jsonnet_dry_run(self) -> Optional[bool]:
        return self.args.jsonnet_dry_run

    @property
    def pause_between_batches(self) -> Optional[bool]:
        return self.args.pause_between_batches

    @property
    def worker_pool_name(self) -> str:
        return self.args.worker_pool

    @property
    def compute_requirement_name(self) -> str:
        return self.args.compute_requirement

    @property
    def work_requirement_name(self) -> str:
        return self.args.work_requirement

    @property
    def worker_pool_size(self) -> int:
        return self.args.worker_pool_size

    @property
    def compute_req_resize(self) -> Optional[bool]:
        return self.args.compute_requirement


def lookup_module_description(module_name: str) -> Optional[str]:
    """
    Descriptive string for the module's purpose.
    """
    prefix = "YellowDog example utility for "
    suffix = None

    if "submit" in module_name:
        suffix = "submitting a Work Requirement"
    elif "provision" in module_name:
        suffix = "provisioning a Worker Pool"
    elif "abort" in module_name:
        suffix = "aborting Tasks"
    elif "cancel" in module_name:
        suffix = "cancelling Work Requirements"
    elif "download" in module_name:
        suffix = "downloading objects from the Object Store"
    elif "delete" in module_name:
        suffix = "deleting objects in the Object Store"
    elif "shutdown" in module_name:
        suffix = "shutting down Worker Pools"
    elif "terminate" in module_name:
        suffix = "terminating Compute Requirements"
    elif "list" in module_name:
        suffix = "listing entities"
    elif "instantiate" in module_name:
        suffix = "provisioning a Compute Requirement"
    elif "upload" in module_name:
        suffix = "uploading objects to the Object Store"
    elif "resize" in module_name:
        suffix = "resizing Worker Pools"

    return None if suffix is None else prefix + suffix


ARGS_PARSER = CLIParser(description=lookup_module_description(sys.argv[0]))
