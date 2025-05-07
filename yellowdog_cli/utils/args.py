"""
Class to parse command line arguments for all commands.
"""

import argparse
import sys
from typing import List, Optional

from yellowdog_cli.__init__ import __version__
from yellowdog_cli.utils.settings import MAX_PARALLEL_TASK_BATCH_UPLOAD_THREADS
from yellowdog_cli.version import DOCS_URL


def docs():
    print(
        f"Online documentation for Python Examples v{__version__}: {DOCS_URL}",
        flush=True,
    )


def allow_missing_attribute(func):
    """
    Wrapper function to return None if an option isn't enabled.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError:
            return None

    return wrapper


class CLIParser:
    def __init__(self, description: Optional[str] = None):
        """
        Create the argument parser, and parse the command
        line arguments. Argument availability depends on module.
        """
        self.tag_required = False
        self.namespace_required = False

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
                "the default to use is 'config.toml' in the current directory"
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
            "--url",
            "-u",
            type=str,
            required=False,
            help="the URL of the YellowDog Platform API",
            metavar="<url>",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            required=False,
            help="display the Python stack trace on error",
        )
        parser.add_argument(
            "--pac",
            action="store_true",
            required=False,
            help="enable PAC (proxy auto-configuration) support",
        )
        parser.add_argument(
            "--no-format",
            "--nf",
            action="store_true",
            required=False,
            help="disable colouring and text wrapping in command output",
        )

        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            required=False,
            help="suppress (non-error, non-interactive) status and progress messages",
        )

        # Module-specific argument sets
        if not any(module in sys.argv[0] for module in ["compare"]):
            parser.add_argument(
                "--variable",
                "-v",
                type=str,
                required=False,
                action="append",
                help=(
                    "user-defined variable substitution; the option can be supplied"
                    " multiple times, one per variable"
                ),
                metavar="<var1=v1>",
            )

        if not any(
            module in sys.argv[0]
            for module in [
                "boost",
                "resize",
                "cloudwizard",
                "follow",
                "list",
                "compare",
            ]
        ):
            self.namespace_required = True
            parser.add_argument(
                "--namespace",
                "-n",
                type=str,
                required=False,
                nargs="?",
                const="",
                help=(
                    "the namespace to use when creating and identifying entities;"
                    " this is set to '' if the option is provided without a value"
                ),
                metavar="<namespace>",
            )
            self.tag_required = True
            parser.add_argument(
                "--tag",
                "-t",
                "--prefix",
                type=str,
                required=False,
                nargs="?",
                const="",
                help=(
                    "the tag to use when naming, tagging, or selecting entities,"
                    " or the prefix (directory) when used with the object store;"
                    " this is set to '' if the option is provided without a value"
                ),
                metavar="<tag>",
            )

        # Namespace and tag attributes are defaulted to "" when using 'yd-list'
        if any(module in sys.argv[0] for module in ["list"]):
            parser.add_argument(
                "--namespace",
                "-n",
                type=str,
                required=False,
                nargs="?",
                const="",
                default="",
                help="the namespace to search when listing entities",
                metavar="<namespace>",
            )
            parser.add_argument(
                "--tag",
                "-t",
                "--prefix",
                type=str,
                required=False,
                nargs="?",
                const="",
                default="",
                help="the tag to search when listing entities",
                metavar="<tag>",
            )
            parser.add_argument(
                "--ids-only",
                "-D",
                action="store_true",
                required=False,
                help="list the YellowDog IDs only",
            )

        if any(module in sys.argv[0] for module in ["submit"]):
            parser.add_argument(
                "--work-requirement",
                "-r",
                type=str,
                required=False,
                help=(
                    "work requirement definition file in JSON or Jsonnet format"
                    " (deprecated: please use positional argument instead)"
                ),
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
                help="the 'executable' to use in the case of certain task types",
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
                help="the number of tasks to submit (copies of a single task)",
                metavar="<task_count>",
            )
            parser.add_argument(
                "--task-group-count",
                "-G",
                type=int,
                required=False,
                help="the number of task groups to submit (copies of a single task group)",
                metavar="<task_group_count>",
            )
            parser.add_argument(
                "--task-batch-size",
                "-b",
                type=int,
                required=False,
                help="the batch size for task submission; must be between 1 and 10,000",
                metavar="<batch_size>",
            )
            parser.add_argument(
                "--pause-between-batches",
                "-P",
                nargs="?",
                type=int,
                const=0,
                required=False,
                metavar="<interval_between_batches_in_seconds>",
                help=(
                    "pause for user input between task batch submissions; if no"
                    " pause interval is provided, user input is required to advance; "
                    "only valid when 'parallel-batches=1'"
                ),
            )
            parser.add_argument(
                "--csv-file",
                "-V",
                type=str,
                required=False,
                action="append",
                help="the CSV file(s) from which to read Task data",
                metavar="<data.csv>",
            )
            parser.add_argument(
                "--process-csv-only",
                "-p",
                action="store_true",
                required=False,
                help=(
                    "process CSV variable substitutions only and output the"
                    " intermediate JSON Work Requirement specification"
                ),
            )
            parser.add_argument(
                "--hold",
                "-H",
                action="store_true",
                required=False,
                help="set the work requirement status to 'HELD' on submission",
            )
            parser.add_argument(
                "--parallel-batches",
                "-l",
                type=int,
                required=False,
                help=(
                    "the maximum number of parallel task batch "
                    f"uploads (default={MAX_PARALLEL_TASK_BATCH_UPLOAD_THREADS})"
                    "; set this to '1' for sequential batch upload"
                ),
                metavar="<max_number_of_parallel_batches>",
            )

        if any(module in sys.argv[0] for module in ["provision", "instantiate"]):
            parser.add_argument(
                "--worker-pool",
                "-p",
                type=str,
                required=False,
                help=(
                    "worker pool definition file in JSON or Jsonnet format"
                    " (deprecated: please use positional argument instead)"
                ),
                metavar="<worker_pool.json>",
            )

        if any(module in sys.argv[0] for module in ["cancel"]):
            parser.add_argument(
                "--abort",
                "-a",
                action="store_true",
                required=False,
                help="abort running tasks with immediate effect",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow progress after cancelling the work requirement(s)",
            )

        if any(
            module in sys.argv[0]
            for module in [
                "start",
                "hold",
            ]
        ):
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow work requirement events after applying action",
            )

        if any(
            module in sys.argv[0]
            for module in [
                "cancel",
                "delete",
                "download",
                "shutdown",
                "terminate",
                "start",
                "hold",
            ]
        ):
            parser.add_argument(
                "--interactive",
                "-i",
                action="store_true",
                required=False,
                help="list, and interactively select, the items to act on",
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
                "cloudwizard",
                "boost",
                "hold",
                "start",
            ]
        ):
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="perform modifying actions without requiring user confirmation",
            )

        if any(module in sys.argv[0] for module in ["delete", "download"]):
            parser.add_argument(
                "--all",
                "-a",
                action="store_true",
                required=False,
                help="list all objects, at all levels in the prefix hierarchy",
            )
            parser.add_argument(
                "--non-exact-namespace-match",
                "-N",
                action="store_true",
                required=False,
                help="match all namespaces that contain the value of 'namespace'",
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
                default="",
                required=False,
                help=(
                    "the directory to use for downloaded objects (defaults to the"
                    " current directory)"
                ),
                metavar="<directory>",
            )
            parser.add_argument(
                "--flatten",
                "-f",
                action="store_true",
                required=False,
                help=(
                    "flatten download paths (warning: objects with the same filenames"
                    " will be overwritten)"
                ),
            )
            parser.add_argument(
                "--pattern",
                "-p",
                type=str,
                required=False,
                help=(
                    "the pattern to use to match objects to be downloaded, "
                    " e.g.: 'work_dir/results_*/results.txt'"
                ),
                metavar="<pattern-string>",
            )

        if "list" in sys.argv[0]:
            parser.add_argument(
                "--reverse",
                action="store_true",
                required=False,
                help="list items in reverse-sorted name order",
            )
            parser.add_argument(
                "--object-paths",
                "--objects",
                "-o",
                action="store_true",
                required=False,
                help="list object store object paths",
            )
            parser.add_argument(
                "--all",
                "-a",
                action="store_true",
                required=False,
                help=(
                    "when used with '--objects', list all objects, not just the top"
                    " level prefixes"
                ),
            )
            parser.add_argument(
                "--details",
                "-d",
                action="store_true",
                required=False,
                help="show the full details of (interactively) selected objects",
            )
            parser.add_argument(
                "--work-requirements",
                "-w",
                action="store_true",
                required=False,
                help="list work requirements",
            )
            parser.add_argument(
                "--task-groups",
                "-g",
                action="store_true",
                required=False,
                help="list task groups in selected work requirements",
            )
            parser.add_argument(
                "--tasks",
                "-T",
                action="store_true",
                required=False,
                help="list tasks in selected work requirements / task groups",
            )
            parser.add_argument(
                "--worker-pools",
                "-p",
                action="store_true",
                required=False,
                help="list worker pools",
            )
            parser.add_argument(
                "--compute-requirements",
                "-r",
                action="store_true",
                required=False,
                help="list compute requirements",
            )
            parser.add_argument(
                "--active-only",
                "-l",
                action="store_true",
                required=False,
                help=(
                    "list only active compute requirements / worker pools / work"
                    " requirements"
                ),
            )
            parser.add_argument(
                "--compute-templates",
                "-C",
                action="store_true",
                required=False,
                help="list compute requirement templates",
            )
            parser.add_argument(
                "--source-templates",
                "-S",
                action="store_true",
                required=False,
                help="list compute source templates",
            )
            parser.add_argument(
                "--keyrings",
                "-K",
                action="store_true",
                required=False,
                help="list keyrings",
            )
            parser.add_argument(
                "--image-families",
                "-I",
                action="store_true",
                required=False,
                help="list machine image families",
            )
            parser.add_argument(
                "--namespace-storage-configurations",
                "-N",
                action="store_true",
                required=False,
                help="list namespace storage configurations",
            )
            parser.add_argument(
                "--instances",
                "-i",
                action="store_true",
                required=False,
                help="list compute instances",
            )
            parser.add_argument(
                "--nodes",
                action="store_true",
                required=False,
                help="list worker pool nodes",
            )
            parser.add_argument(
                "--workers",
                action="store_true",
                required=False,
                help="list all workers in a worker pool",
            )
            parser.add_argument(
                "--public-ips-only",
                action="store_true",
                required=False,
                help="when used with '--instances', lists public IP addresses only",
            )
            parser.add_argument(
                "--allowances",
                "-A",
                action="store_true",
                required=False,
                help="list allowances",
            )
            parser.add_argument(
                "--attribute-definitions",
                "-R",
                action="store_true",
                required=False,
                help="list user attribute definitions",
            )
            parser.add_argument(
                "--namespace-policies",
                "-P",
                action="store_true",
                required=False,
                help="list namespace policies",
            )
            parser.add_argument(
                "--users",
                action="store_true",
                required=False,
                help="list users",
            )
            parser.add_argument(
                "--applications",
                action="store_true",
                required=False,
                help="list applications",
            )
            parser.add_argument(
                "--groups",
                action="store_true",
                required=False,
                help="list groups",
            )
            parser.add_argument(
                "--roles",
                action="store_true",
                required=False,
                help="list roles",
            )
            parser.add_argument(
                "--output-file",
                type=str,
                required=False,
                help=(
                    "if specified, the 'details' resource listing will be appended "
                    "to the nominated output file"
                ),
                metavar="<output-file>",
            )

        if any(module in sys.argv[0] for module in ["upload"]):
            parser.add_argument(
                "filenames",
                metavar="<filename>",
                type=str,
                nargs="+",
                help="files and/or directories to upload to the object store",
            )
            parser.add_argument(
                "--flatten-upload-paths",
                "-f",
                action="store_true",
                required=False,
                help=(
                    "don't mirror local directory structure when uploading files (files"
                    " may be overwritten)"
                ),
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
            module in sys.argv[0]
            for module in ["submit", "provision", "instantiate", "create"]
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
                help=(
                    "compute requirement definition file in JSON or Jsonnet format"
                    " (deprecated: please use positional argument instead)"
                ),
                metavar="<compute_requirement.json>",
            )
            parser.add_argument(
                "--report",
                "-r",
                action="store_true",
                required=False,
                help="report on a dynamic template test run",
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
            module in sys.argv[0]
            for module in ["submit", "provision", "instantiate", "create", "remove"]
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
                    "the name or YellowDog ID of the worker pool or compute requirement"
                    " to resize"
                ),
            )
            parser.add_argument(
                "worker_pool_size",
                metavar="<new-node/instance-count>",
                type=int,
                help="the desired number of (total) nodes in the worker pool",
            )
            parser.add_argument(
                "--compute-requirement",
                "-C",
                action="store_true",
                required=False,
                help="resize a compute requirement instead of a worker pool",
            )

        if "boost" in sys.argv[0]:
            parser.add_argument(
                "boost_hours",
                metavar="<boost hours>",
                type=int,
                help="the number of hours to boost the allowance by",
            )
            parser.add_argument(
                "allowances",
                metavar="<allowance-ID> [<allowance-ID>]",
                nargs="+",
                type=str,
                help="the YellowDog ID(s) of the allowance(s) to boost",
            )

        if "shutdown" in sys.argv[0]:
            parser.add_argument(
                "worker_pool_nodes_list",
                nargs="*",
                default="",
                metavar="<worker-pool-name-or-ID/node-id>",
                type=str,
                help="the name(s) or YellowDog ID(s) of the worker pool(s) and/or ID(s) of nodes",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow worker pool shutdown to completion",
            )
            parser.add_argument(
                "--terminate",
                "-T",
                action="store_true",
                required=False,
                help="also immediately terminate associated compute requirement(s)",
            )

        if "terminate" in sys.argv[0]:
            parser.add_argument(
                "compute_reqs",
                nargs="*",
                default="",
                metavar="<compute-requirement-name-or-ID>",
                type=str,
                help="the name(s) or YellowDog ID(s) of the compute requirement(s)",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow termination to completion",
            )

        if "cancel" in sys.argv[0]:
            parser.add_argument(
                "work_requirements",
                nargs="*",
                default="",
                metavar="<work-requirement-name-or-ID>",
                type=str,
                help=(
                    "the name(s) or YellowDog ID(s) of the work requirement(s) to be"
                    " cancelled; can also supply task IDs"
                ),
            )

        if "start" in sys.argv[0]:
            parser.add_argument(
                "work_requirements",
                nargs="*",
                default="",
                metavar="<work-requirement-name-or-ID>",
                type=str,
                help=(
                    "the name(s) or YellowDog ID(s) of the held (paused) work requirement(s) to be"
                    " started"
                ),
            )

        if "hold" in sys.argv[0]:
            parser.add_argument(
                "work_requirements",
                nargs="*",
                default="",
                metavar="<work-requirement-name-or-ID>",
                type=str,
                help=(
                    "the name(s) or YellowDog ID(s) of the work requirement(s) to be"
                    " held (paused)"
                ),
            )

        if "delete" in sys.argv[0]:
            parser.add_argument(
                "object_paths_to_delete",
                nargs="*",
                default=[],
                metavar="<object_path>",
                type=str,
                help="the object paths to delete; optional, overrides --tag/prefix",
            )

        if "download" in sys.argv[0]:
            parser.add_argument(
                "object_paths_to_download",
                nargs="*",
                default=[],
                metavar="<object_path>",
                type=str,
                help="the object paths to download; optional, overrides --tag/prefix",
            )
        if any(module in sys.argv[0] for module in ["create", "remove"]):
            parser.add_argument(
                "resource_specifications",
                nargs="+",
                default=[],
                metavar="<resource-specification>",
                type=str,
                help=(
                    "the resource specifications to process (or resource IDs if used"
                    " with 'yd-remove --ids')"
                ),
            )
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="allow updates without user confirmation",
            )
            parser.add_argument(
                "--match-allowances-by-description",
                "-M",
                action="store_true",
                required=False,
                help=(
                    "match using the 'description' property when updating "
                    "(using yd-create) or removing allowances"
                ),
            )
        if "create" in sys.argv[0]:
            parser.add_argument(
                "--show-keyring-passwords",
                action="store_true",
                required=False,
                help="display YellowDog-generated password when creating a Keyring",
            )

        if "remove" in sys.argv[0]:
            parser.add_argument(
                "--ids",
                action="store_true",
                required=False,
                help="remove resources using their YellowDog IDs (YDIDs)",
            )

        if any(module in sys.argv[0] for module in ["follow", "show"]):
            verb = "follow" if "follow" in sys.argv[0] else "show"
            parser.add_argument(
                "yellowdog_ids",
                nargs="+",
                default=[],
                metavar="<yellowdog-id>",
                type=str,
                help=f"the YellowDog ID(s) of the item(s) to {verb}",
            )

        if any(
            module in sys.argv[0]
            for module in ["upload", "submit", "provision", "instantiate"]
        ):
            parser.add_argument(
                "--content-path",
                "-F",
                type=str,
                required=False,
                help=(
                    "the directory in which files for upload (or for user data "
                    "or CSV data) are found"
                ),
                metavar="<directory>",
            )

        if any(module in sys.argv[0] for module in ["provision", "instantiate"]):
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow progress after provisioning",
            )

        if any(module in sys.argv[0] for module in ["resize"]):
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow progress after resizing",
            )

        if any(
            module in sys.argv[0]
            for module in ["follow", "shutdown", "provision", "resize"]
        ):
            parser.add_argument(
                "--auto-follow-compute-requirements",
                "-a",
                action="store_true",
                required=False,
                help=(
                    "automatically follow the associated compute requirements when"
                    " following worker pools"
                ),
            )
        if any(
            module in sys.argv[0]
            for module in [
                "follow",
                "provision",
                "instantiate",
                "resize",
                "shutdown",
                "terminate",
                "submit",
                "cancel",
                "start",
                "hold",
            ]
        ):
            parser.add_argument(
                "--raw-events",
                action="store_true",
                required=False,
                help="print the raw JSON event stream when following events",
            )

        if "cloudwizard" in sys.argv[0]:
            parser.add_argument(
                "operation",
                metavar="'setup', 'teardown', 'add-ssh' or 'remove-ssh'",
                type=str,
                choices=["setup", "teardown", "add-ssh", "remove-ssh"],
                help=(
                    "the cloud wizard operation to perform: 'setup', 'teardown',"
                    " 'add-ssh' or 'remove-ssh'"
                ),
            )
            parser.add_argument(
                "--cloud-provider",
                required=True,
                metavar="<name of cloud provider>",
                type=str,
                help=(
                    "the name of the cloud provider (AWS, GCP, and Azure are currently"
                    " supported)"
                ),
            )
            parser.add_argument(
                "--credentials-file",
                required=False,
                metavar="<file-containing-google-credentials>",
                type=str,
                help=(
                    "the name of the file containing the cloud GCP credentials when"
                    " using Cloud Wizard with GCP"
                ),
            )
            parser.add_argument(
                "--region-name",
                "-R",
                required=False,
                metavar="<cloud-provider-region-name>",
                type=str,
                help="specify the cloud provider region name for certain operations",
            )
            parser.add_argument(
                "--instance-type",
                "-I",
                required=False,
                metavar="<instance-type>",
                type=str,
                help=(
                    "the instance type to use in the automatically generated YellowDog"
                    " compute requirement templates"
                ),
            )
            parser.add_argument(
                "--show-secrets",
                action="store_true",
                required=False,
                help="print AWS secret key during setup",
            )

        if "abort" in sys.argv[0]:
            parser.add_argument(
                "task_id_list",
                nargs="*",
                default="",
                metavar="<task-id>",
                type=str,
                help="the YellowDog ID(s) of the task(s) to abort",
            )

        if any(module in sys.argv[0] for module in ["submit"]):
            # Note: removes the need for the '-r' option
            parser.add_argument(
                "work_requirement_file_positional",
                metavar="<work-requirement-specification-file>",
                type=str,
                nargs="?",
                help=(
                    "the JSON or Jsonnet specification of the work requirement"
                    " to submit; alternative to using the '--work-requirement/-r'"
                    " option"
                ),
            )

        if any(module in sys.argv[0] for module in ["provision"]):
            # Note: removes the need for the '-p' option
            parser.add_argument(
                "worker_pool_file_positional",
                metavar="<worker-pool-specification-file>",
                type=str,
                nargs="?",
                help=(
                    "the JSON or Jsonnet specification of the worker pool"
                    " to provision; alternative to using the '--worker-pool/-p'"
                    " option"
                ),
            )

        if any(module in sys.argv[0] for module in ["instantiate"]):
            # Note: removes the need for the '-C' option
            parser.add_argument(
                "compute_requirement_file_positional",
                metavar="<compute-requirement-specification-file>",
                type=str,
                nargs="?",
                help=(
                    "the JSON or Jsonnet specification of the compute requirement"
                    " to provision; alternative to using the"
                    "'--compute-requirement/-C' option"
                ),
            )

        if any(module in sys.argv[0] for module in ["create"]):
            parser.add_argument(
                "--no-resequence",
                action="store_true",
                required=False,
                help=(
                    "don't re-sequence resources prior  to creation (e.g., "
                    "putting source templates before requirement templates)"
                ),
            )

        if any(module in sys.argv[0] for module in ["show"]):
            parser.add_argument(
                "--show-token",
                action="store_true",
                required=False,
                help=(
                    "display the worker pool token when showing the details of a "
                    "configured worker pool"
                ),
            )

        if any(module in sys.argv[0] for module in ["list", "show"]):
            parser.add_argument(
                "--substitute-ids",
                "-U",
                action="store_true",
                required=False,
                help=(
                    "substitute compute source template IDs and image family IDs for "
                    "names in detailed compute requirement templates"
                ),
            )

        if "compare" in sys.argv[0]:
            parser.add_argument(
                "wr_or_tg_id",
                metavar="<work-requirement-or-task-group-ID>",
                type=str,
                help=(
                    "the YellowDog ID of the work requirement or task group to be compared"
                ),
            )
            parser.add_argument(
                "worker_pool_ids",
                metavar="<worker-pool-ID>",
                type=str,
                nargs="+",
                help="the YellowDog ID(s) of the worker pool(s) to compare",
            )

        self.args = parser.parse_args()

        if self.args.docs:
            docs()
            exit(0)

    @property
    @allow_missing_attribute
    def config_file(self) -> Optional[str]:
        return self.args.config

    @property
    @allow_missing_attribute
    def key(self) -> Optional[str]:
        return self.args.key

    @property
    @allow_missing_attribute
    def secret(self) -> Optional[str]:
        return self.args.secret

    @property
    @allow_missing_attribute
    def namespace(self) -> Optional[str]:
        return self.args.namespace

    @property
    @allow_missing_attribute
    def tag(self) -> Optional[str]:
        return self.args.tag

    @property
    @allow_missing_attribute
    def url(self) -> Optional[str]:
        return self.args.url

    @property
    @allow_missing_attribute
    def variables(self) -> Optional[List[str]]:
        return self.args.variable

    @property
    @allow_missing_attribute
    def quiet(self) -> Optional[bool]:
        return self.args.quiet

    @property
    @allow_missing_attribute
    def work_req_file(self) -> Optional[str]:
        return self.args.work_requirement

    @property
    @allow_missing_attribute
    def executable(self) -> Optional[str]:
        return self.args.executable

    @property
    @allow_missing_attribute
    def task_type(self) -> Optional[str]:
        return self.args.task_type

    @property
    @allow_missing_attribute
    def worker_pool_file(self) -> Optional[str]:
        return self.args.worker_pool

    @property
    @allow_missing_attribute
    def follow(self) -> Optional[bool]:
        return self.args.follow

    @property
    @allow_missing_attribute
    def abort(self) -> Optional[bool]:
        return self.args.abort

    @property
    @allow_missing_attribute
    def interactive(self) -> Optional[bool]:
        return self.args.interactive

    @interactive.setter
    def interactive(self, interactive: bool):
        self.args.interactive = interactive

    @property
    @allow_missing_attribute
    def yes(self) -> Optional[bool]:
        return self.args.yes

    @property
    @allow_missing_attribute
    def object_paths(self) -> Optional[bool]:
        return self.args.object_paths

    @property
    @allow_missing_attribute
    def work_requirements(self) -> Optional[bool]:
        return self.args.work_requirements

    @property
    @allow_missing_attribute
    def task_groups(self) -> Optional[bool]:
        return self.args.task_groups

    @property
    @allow_missing_attribute
    def tasks(self) -> Optional[bool]:
        return self.args.tasks

    @property
    @allow_missing_attribute
    def worker_pools(self) -> Optional[bool]:
        return self.args.worker_pools

    @property
    @allow_missing_attribute
    def compute_requirements(self) -> Optional[bool]:
        return self.args.compute_requirements

    @property
    @allow_missing_attribute
    def active_only(self) -> Optional[bool]:
        return self.args.active_only

    @property
    @allow_missing_attribute
    def all(self) -> Optional[bool]:
        return self.args.all

    @property
    @allow_missing_attribute
    def non_exact_namespace_match(self) -> Optional[bool]:
        return self.args.non_exact_namespace_match

    @property
    @allow_missing_attribute
    def details(self) -> Optional[bool]:
        return self.args.details

    @property
    @allow_missing_attribute
    def debug(self) -> Optional[bool]:
        return self.args.debug

    @property
    @allow_missing_attribute
    def use_pac(self) -> Optional[bool]:
        return self.args.pac

    @property
    @allow_missing_attribute
    def no_format(self) -> Optional[bool]:
        return self.args.no_format

    @property
    @allow_missing_attribute
    def directory(self) -> Optional[str]:
        return self.args.directory

    @property
    @allow_missing_attribute
    def files(self) -> List[str]:
        return self.args.filenames

    @property
    @allow_missing_attribute
    def flatten(self) -> Optional[bool]:
        return self.args.flatten_upload_paths

    @property
    @allow_missing_attribute
    def recursive(self) -> Optional[bool]:
        return self.args.recursive

    @property
    @allow_missing_attribute
    def batch(self) -> Optional[bool]:
        return self.args.batch

    @property
    @allow_missing_attribute
    def dry_run(self) -> Optional[bool]:
        return self.args.dry_run

    @property
    @allow_missing_attribute
    def json_raw(self) -> Optional[str]:
        return self.args.json_raw

    @property
    @allow_missing_attribute
    def compute_requirement(self) -> Optional[str]:
        return self.args.compute_requirement

    @property
    @allow_missing_attribute
    def task_count(self) -> Optional[int]:
        return self.args.task_count

    @property
    @allow_missing_attribute
    def task_group_count(self) -> Optional[int]:
        return self.args.task_group_count

    @property
    @allow_missing_attribute
    def csv_files(self) -> Optional[List[str]]:
        return self.args.csv_file

    @property
    @allow_missing_attribute
    def process_csv_only(self) -> Optional[bool]:
        return self.args.process_csv_only

    @property
    @allow_missing_attribute
    def wr_ids(self) -> Optional[List[str]]:
        return self.args.work_requirement_id

    @property
    @allow_missing_attribute
    def task_batch_size(self) -> Optional[int]:
        return self.args.task_batch_size

    @property
    @allow_missing_attribute
    def content_path(self) -> Optional[str]:
        return self.args.content_path

    @property
    @allow_missing_attribute
    def report(self) -> Optional[bool]:
        return self.args.report

    @property
    @allow_missing_attribute
    def jsonnet_dry_run(self) -> Optional[bool]:
        return self.args.jsonnet_dry_run

    @property
    @allow_missing_attribute
    def pause_between_batches(self) -> Optional[int]:
        return self.args.pause_between_batches

    @property
    @allow_missing_attribute
    def parallel_batches(self) -> Optional[int]:
        return self.args.parallel_batches

    @property
    @allow_missing_attribute
    def worker_pool_name(self) -> Optional[str]:
        return self.args.worker_pool

    @property
    @allow_missing_attribute
    def worker_pool_nodes_list(self) -> Optional[List[str]]:
        return self.args.worker_pool_nodes_list

    @property
    @allow_missing_attribute
    def compute_requirement_names(self) -> Optional[str]:
        return self.args.compute_reqs

    @property
    @allow_missing_attribute
    def work_requirement_names(self) -> Optional[str]:
        return self.args.work_requirements

    @property
    @allow_missing_attribute
    def object_paths_to_delete(self) -> Optional[List[str]]:
        return self.args.object_paths_to_delete

    @property
    @allow_missing_attribute
    def object_paths_to_download(self) -> Optional[List[str]]:
        return self.args.object_paths_to_download

    @property
    @allow_missing_attribute
    def worker_pool_size(self) -> Optional[int]:
        return self.args.worker_pool_size

    @property
    @allow_missing_attribute
    def compute_req_resize(self) -> Optional[bool]:
        return self.args.compute_requirement

    @property
    @allow_missing_attribute
    def flatten_download_paths(self) -> Optional[bool]:
        return self.args.flatten

    @property
    @allow_missing_attribute
    def compute_templates(self) -> Optional[bool]:
        return self.args.compute_templates

    @property
    @allow_missing_attribute
    def source_templates(self) -> Optional[bool]:
        return self.args.source_templates

    @property
    @allow_missing_attribute
    def keyrings(self) -> Optional[bool]:
        return self.args.keyrings

    @property
    @allow_missing_attribute
    def image_families(self) -> Optional[bool]:
        return self.args.image_families

    @property
    @allow_missing_attribute
    def namespace_storage_configurations(self) -> Optional[bool]:
        return self.args.namespace_storage_configurations

    @property
    @allow_missing_attribute
    def instances(self) -> Optional[bool]:
        return self.args.instances

    @property
    @allow_missing_attribute
    def nodes(self) -> Optional[bool]:
        return self.args.nodes

    @property
    @allow_missing_attribute
    def workers(self) -> Optional[bool]:
        return self.args.workers

    @property
    @allow_missing_attribute
    def allowances(self) -> Optional[bool]:
        return self.args.allowances

    @property
    @allow_missing_attribute
    def attribute_definitions(self) -> Optional[bool]:
        return self.args.attribute_definitions

    @property
    @allow_missing_attribute
    def namespace_policies(self) -> Optional[bool]:
        return self.args.namespace_policies

    @property
    @allow_missing_attribute
    def users(self) -> Optional[bool]:
        return self.args.users

    @property
    @allow_missing_attribute
    def applications(self) -> Optional[bool]:
        return self.args.applications

    @property
    @allow_missing_attribute
    def groups(self) -> Optional[bool]:
        return self.args.groups

    @property
    @allow_missing_attribute
    def roles(self) -> Optional[bool]:
        return self.args.roles

    @property
    @allow_missing_attribute
    def show_keyring_passwords(self) -> Optional[bool]:
        return self.args.show_keyring_passwords

    @property
    @allow_missing_attribute
    def ids(self) -> Optional[bool]:
        return self.args.ids

    @property
    @allow_missing_attribute
    def resource_specifications(self) -> Optional[List[str]]:
        return self.args.resource_specifications

    @property
    @allow_missing_attribute
    def yellowdog_ids(self) -> Optional[List[str]]:
        return self.args.yellowdog_ids

    @property
    @allow_missing_attribute
    def auto_cr(self) -> Optional[bool]:
        return self.args.auto_follow_compute_requirements

    @property
    @allow_missing_attribute
    def raw_events(self) -> Optional[bool]:
        return self.args.raw_events

    @property
    @allow_missing_attribute
    def reverse(self) -> Optional[bool]:
        return self.args.reverse

    @property
    @allow_missing_attribute
    def operation(self) -> Optional[str]:
        return self.args.operation

    @property
    @allow_missing_attribute
    def cloud_provider(self) -> Optional[str]:
        return self.args.cloud_provider

    @property
    @allow_missing_attribute
    def credentials_file(self) -> Optional[str]:
        return self.args.credentials_file

    @property
    @allow_missing_attribute
    def region_name(self) -> Optional[str]:
        return self.args.region_name

    @property
    @allow_missing_attribute
    def instance_type(self) -> Optional[str]:
        return self.args.instance_type

    @property
    @allow_missing_attribute
    def show_secrets(self) -> Optional[bool]:
        return self.args.show_secrets

    @property
    @allow_missing_attribute
    def hold(self) -> Optional[bool]:
        return self.args.hold

    @property
    @allow_missing_attribute
    def task_id_list(self) -> Optional[List[str]]:
        return self.args.task_id_list

    @property
    @allow_missing_attribute
    def work_requirement_file_positional(self) -> Optional[str]:
        return self.args.work_requirement_file_positional

    @property
    @allow_missing_attribute
    def worker_pool_file_positional(self) -> Optional[str]:
        return self.args.worker_pool_file_positional

    @property
    @allow_missing_attribute
    def compute_requirement_file_positional(self) -> Optional[str]:
        return self.args.compute_requirement_file_positional

    @property
    @allow_missing_attribute
    def object_path_pattern(self) -> Optional[str]:
        return self.args.pattern

    @property
    @allow_missing_attribute
    def allowance_list(self) -> List[str]:
        return self.args.allowances

    @property
    @allow_missing_attribute
    def boost_hours(self) -> int:
        return self.args.boost_hours

    @property
    @allow_missing_attribute
    def no_resequence(self) -> Optional[bool]:
        return self.args.no_resequence

    @property
    @allow_missing_attribute
    def match_allowances_by_description(self) -> Optional[bool]:
        return self.args.match_allowances_by_description

    @property
    @allow_missing_attribute
    def public_ips_only(self) -> Optional[bool]:
        return self.args.public_ips_only

    @property
    @allow_missing_attribute
    def show_token(self) -> Optional[bool]:
        return self.args.show_token

    @property
    @allow_missing_attribute
    def output_file(self) -> Optional[str]:
        return self.args.output_file

    @property
    @allow_missing_attribute
    def substitute_ids(self) -> Optional[bool]:
        return self.args.substitute_ids

    @property
    @allow_missing_attribute
    def wr_or_tg_id(self) -> Optional[str]:
        return self.args.wr_or_tg_id

    @property
    @allow_missing_attribute
    def worker_pool_ids(self) -> Optional[List[str]]:
        return self.args.worker_pool_ids

    @property
    @allow_missing_attribute
    def ids_only(self) -> Optional[bool]:
        return self.args.ids_only

    @property
    @allow_missing_attribute
    def terminate(self) -> Optional[bool]:
        return self.args.terminate


def lookup_module_description(module_name: str) -> Optional[str]:
    """
    Descriptive string for the module's purpose.
    """
    prefix = "YellowDog command line utility for "
    suffix = None

    if "submit" in module_name:
        suffix = "submitting a Work Requirement"
    elif "provision" in module_name:
        suffix = "provisioning a Worker Pool"
    elif "abort" in module_name:
        suffix = "aborting Tasks"
    elif "cancel" in module_name:
        suffix = "cancelling Work Requirements"
    elif "create" in module_name:
        suffix = "creating and updating resources"
    elif "download" in module_name:
        suffix = "downloading objects from the Object Store"
    elif "delete" in module_name:
        suffix = "deleting objects in the Object Store"
    elif "shutdown" in module_name:
        suffix = "shutting down Worker Pools and Nodes"
    elif "terminate" in module_name:
        suffix = "terminating Compute Requirements"
    elif "list" in module_name:
        suffix = "listing all kinds of YellowDog items"
    elif "instantiate" in module_name:
        suffix = "instantiating a Compute Requirement"
    elif "upload" in module_name:
        suffix = "uploading objects to the Object Store"
    elif "remove" in module_name:
        suffix = "removing resources"
    elif "resize" in module_name:
        suffix = "resizing Worker Pools and Compute Requirements"
    elif "follow" in module_name:
        suffix = "following event streams"
    elif "cloudwizard" in module_name:
        suffix = "setting up cloud accounts and YellowDog resources"
    elif "start" in module_name:
        suffix = "starting held (paused) Work Requirements"
    elif "hold" in module_name:
        suffix = "holding (pausing) running Work Requirements"
    elif "boost" in module_name:
        suffix = "boosting Allowances"
    elif "show" in module_name:
        suffix = "showing the JSON details of entities referenced by their YDIDs"
    elif "compare" in module_name:
        suffix = (
            "comparing whether a work requirement or task group is matched by "
            "workers in the specified worker pools"
        )

    return None if suffix is None else prefix + suffix


ARGS_PARSER = CLIParser(description=lookup_module_description(sys.argv[0]))
