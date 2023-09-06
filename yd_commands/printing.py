"""
Functions focused on print outputs.
"""

from datetime import datetime
from json import dumps as json_dumps
from json import loads as json_loads
from os import get_terminal_size
from os import name as os_name
from os.path import relpath
from textwrap import fill
from textwrap import indent as text_indent
from typing import Any, Dict, List, Optional, TypeVar

from rich.console import Console, Theme
from rich.highlighter import JSONHighlighter, RegexHighlighter
from tabulate import tabulate
from yellowdog_client import PlatformClient
from yellowdog_client.common.json import Json
from yellowdog_client.model import (
    BestComputeSourceReport,
    BestComputeSourceReportSource,
    ComputeRequirement,
    ComputeRequirementDynamicTemplateTestResult,
    ComputeRequirementTemplateSummary,
    ComputeRequirementTemplateTestResult,
    ComputeRequirementTemplateUsage,
    ComputeSourceTemplateSummary,
    ConfiguredWorkerPool,
    Instance,
    KeyringSummary,
    MachineImageFamilySummary,
    NodeStatus,
    NodeSummary,
    ObjectDetail,
    ObjectPath,
    ProvisionedWorkerPool,
    ProvisionedWorkerPoolProperties,
    Task,
    TaskGroup,
    WorkerPool,
    WorkerPoolSummary,
    WorkRequirement,
    WorkRequirementSummary,
)
from yellowdog_client.object_store.download import DownloadBatchBuilder
from yellowdog_client.object_store.upload import UploadBatchBuilder

from yd_commands.args import ARGS_PARSER
from yd_commands.compact_json import CompactJSONEncoder
from yd_commands.id_utils import YDIDType
from yd_commands.object_utilities import Item
from yd_commands.property_names import NAME, TASK_GROUPS, TASKS

JSON_INDENT = 2

try:
    LOG_WIDTH = get_terminal_size().columns
except OSError:
    LOG_WIDTH = 120  # Default log line width


# Set up Rich formatting for coloured output
class PrintLogHighlighter(RegexHighlighter):
    """
    Apply styles for print_log() lines.
    """

    base_style = "pyexamples."
    highlights = [
        r"(?P<date_time>[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"
        r" [0-9][0-9]:[0-9][0-9]:[0-9][0-9])",
        r"(?P<quoted>'[a-zA-Z0-9-._=;:\/\\\[\]{}+#@$£%\^&\*\(\)~`<>?]*')",
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*)",
        r"(?P<url>(https?):((//)|(\\\\))+[\w\d:#@%/;$~_?\+-=\\\.&]*)",
        r"(?P<active>EXECUTING)",
        r"(?P<failed>FAILED)",
        r"(?P<completed>COMPLETED)",
        r"(?P<cancelled>CANCELLED)",
        r"(?P<cancelled>ABORTED)",
        r"(?P<active>RUNNING)",
        r"(?P<transitioning>PROVISIONING)",
        r"(?P<transitioning>TERMINATING)",
        r"(?P<cancelled>TERMINATED)",
        r"(?P<cancelled>SHUTDOWN)",
        r"(?P<cancelled>CANCELLING)",
        r"(?P<idle>IDLE)",
        r"(?P<active>PENDING)",
        r"(?P<transitioning>EMPTY)",
        r"(?P<active>READY)",
        r"(?P<active>ALLOCATED)",
        r"(?P<starved>STARVED)",
        r"(?P<transitioning>CONFIGURING)",
        r"(?P<transitioning>UPLOADING)",
        r"(?P<transitioning>DOWNLOADING)",
    ]


class PrintTableHighlighter(RegexHighlighter):
    """
    Apply styles for table printing.
    """

    base_style = "pyexamples."
    table_outline_chars = "┌─┬│┼┐┤└┴┘├"
    highlights = [
        rf"(?P<table_outline>[{table_outline_chars}]*)",
        rf"(?P<table_content>[^{table_outline_chars}]*)",
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*)",
        r"(?P<active>EXECUTING)",
        r"(?P<failed>FAILED)",
        r"(?P<completed>COMPLETED)",
        r"(?P<cancelled>CANCELLED)",
        r"(?P<cancelled>ABORTED)",
        r"(?P<active>RUNNING)",
        r"(?P<transitioning>PROVISIONING)",
        r"(?P<transitioning>TERMINATING)",
        r"(?P<cancelled>TERMINATED)",
        r"(?P<cancelled>SHUTDOWN)",
        r"(?P<cancelled>CANCELLING)",
        r"(?P<idle>IDLE)",
        r"(?P<active>PENDING)",
        r"(?P<idle>EMPTY)",
        r"(?P<active>READY)",
        r"(?P<active>ALLOCATED)",
        r"(?P<starved>STARVED)",
        r"(?P<transitioning>CONFIGURING)",
        r"(?P<transitioning>UPLOADING)",
        r"(?P<transitioning>DOWNLOADING)",
    ]


# For Rich colour options, see colour list & swatches at:
# https://rich.readthedocs.io/en/stable/appendix/colors.html

pyexamples_theme = Theme(
    {
        "pyexamples.date_time": "bold deep_sky_blue1",
        "pyexamples.quoted": "bold green4",
        "pyexamples.url": "bold green4",
        "pyexamples.ydid": "bold dark_orange",
        "pyexamples.table_outline": "bold deep_sky_blue4",
        "pyexamples.table_content": "bold green4",
        "pyexamples.transitioning": "bold dark_orange",
        "pyexamples.executing": "bold deep_sky_blue4",
        "pyexamples.failed": "bold red3",
        "pyexamples.completed": "bold green4",
        "pyexamples.cancelled": "bold grey35",
        "pyexamples.active": "bold deep_sky_blue4",
        "pyexamples.idle": "bold bright_magenta",
        "pyexamples.starved": "bold dark_orange",
    }
)

ERROR_STYLE = "bold red3"
WARNING_STYLE = "red3"

CONSOLE = Console(highlighter=PrintLogHighlighter(), theme=pyexamples_theme)
CONSOLE_TABLE = Console(highlighter=PrintTableHighlighter(), theme=pyexamples_theme)
CONSOLE_ERR = Console(stderr=True, highlighter=PrintLogHighlighter())
CONSOLE_JSON = Console(highlighter=JSONHighlighter())

PREFIX_LEN = 0


def print_string(msg: str = "", no_fill: bool = False) -> str:
    """
    Message output format, with tidy line-wrapping calibrated
    for the terminal width.
    """
    global PREFIX_LEN
    prefix = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : "
    if PREFIX_LEN == 0:
        PREFIX_LEN = len(prefix)

    if no_fill:
        return prefix + msg

    return fill(
        msg,
        width=LOG_WIDTH,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
        drop_whitespace=True,
        break_long_words=False,  # Preserve URLs
        break_on_hyphens=False,  # Preserve names
    )


def print_log(
    log_message: str,
    override_quiet: bool = False,
    no_fill: bool = False,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    CONSOLE.print(print_string(log_message, no_fill=no_fill))


ErrorObject = TypeVar(
    "ErrorObject",
    Exception,
    str,
)


def print_error(error_obj: ErrorObject):
    """
    Print an error message to stderr.
    """
    CONSOLE_ERR.print(print_string(f"Error: {error_obj}"), style=ERROR_STYLE)


def print_warning(warning: str):
    """
    Print a warning.
    """
    CONSOLE.print(print_string(f"Warning: {warning}"), style=WARNING_STYLE)


TYPE_MAP = {
    ConfiguredWorkerPool: "Configured Worker Pool",
    ProvisionedWorkerPool: "Provisioned Worker Pool",
    WorkerPoolSummary: "Worker Pool",
    ComputeRequirement: "Compute Requirement",
    Task: "Task",
    TaskGroup: "Task Group",
    WorkRequirementSummary: "Work Requirement",
    ObjectPath: "Object Path",
    ComputeRequirementTemplateSummary: "Compute Requirement Template",
    ComputeSourceTemplateSummary: "Compute Source Template",
    KeyringSummary: "Keyring",
    MachineImageFamilySummary: "Machine Image Family",
}


def get_type_name(obj: Item) -> str:
    """
    Get the display name of an object's type.
    """
    if type(obj).__name__.endswith("NamespaceStorageConfiguration"):
        # Special case
        return "Namespace Storage Configuration"

    if type(obj).__name__.endswith("Instance"):
        # Special case
        return "Instance"

    return TYPE_MAP.get(type(obj), "")


def compute_requirement_table(
    cr_list: List[ComputeRequirement],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Compute Requirement Name",
        "Namespace",
        "Tag",
        "Status (Tgt/Exp)",
        "ID",
    ]
    table = []
    for index, cr in enumerate(cr_list):
        table.append(
            [
                index + 1,
                cr.name,
                cr.namespace,
                cr.tag,
                (
                    f"{cr.status}"
                    if cr.nextStatus is None
                    else (f"{cr.status} -> {cr.nextStatus}")
                )
                + f" ({cr.targetInstanceCount:,d}/{cr.expectedInstanceCount:,d})",
                cr.id,
            ]
        )
    return headers, table


def work_requirement_table(
    wr_summary_list: List[WorkRequirementSummary],
) -> (List[str], List[List]):
    headers = ["#", "Work Requirement Name", "Namespace", "Tag", "Status", "ID"]
    table = []
    for index, wr_summary in enumerate(wr_summary_list):
        namespace = "" if wr_summary.namespace is None else wr_summary.namespace
        tag = "" if wr_summary.tag is None else wr_summary.tag
        table.append(
            [
                index + 1,
                wr_summary.name,
                namespace,
                tag,
                str(wr_summary.status),
                wr_summary.id,
            ]
        )
    return headers, table


def task_group_table(
    task_group_list: List[TaskGroup],
) -> (List[str], List[List]):
    headers = ["#", "Task Group Name", "Status", "ID"]
    table = []
    for index, task_group in enumerate(task_group_list):
        table.append(
            [
                index + 1,
                task_group.name,
                str(task_group.status),
                task_group.id,
            ]
        )
    return headers, table


def task_table(task_list: List[Task]) -> (List[str], List[List]):
    headers = ["#", "Task Name", "Status", "ID"]
    table = []
    for index, task in enumerate(task_list):
        table.append(
            [
                index + 1,
                task.name,
                str(task.status),
                task.id,
            ]
        )
    return headers, table


def worker_pool_table(
    client: PlatformClient, worker_pool_summaries: List[WorkerPoolSummary]
) -> (List[str], List[List]):
    headers = [
        "#",
        "Worker Pool Name",
        "Type",
        "Status",
        "Min/Run/Max",
        "ID",
    ]
    table = []
    for index, worker_pool_summary in enumerate(worker_pool_summaries):
        worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_id(
            worker_pool_summary.id
        )
        try:
            min_nodes = str(worker_pool.properties.minNodes)
        except:
            min_nodes = "_"
        try:
            max_nodes = str(worker_pool.properties.maxNodes)
        except:
            max_nodes = "_"
        node_summary: NodeSummary = worker_pool.nodeSummary
        nodes_running = node_summary.statusCounts[NodeStatus.RUNNING]

        table.append(
            [
                index + 1,
                worker_pool_summary.name,
                (
                    f"{worker_pool_summary.type.split('.')[-1:][0].replace('WorkerPool', '')}"
                ),
                f"{worker_pool_summary.status}",
                f"{min_nodes}/{nodes_running}/{max_nodes}",
                worker_pool_summary.id,
            ]
        )
    return headers, table


def compute_requirement_template_table(
    crt_summaries: List[ComputeRequirementTemplateSummary],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Namespace",
        "Type",
        "Strategy Type",
        "ID",
    ]
    table = []
    for index, crt_summary in enumerate(crt_summaries):
        try:
            type = crt_summary.type.split(".")[-1].replace("ComputeRequirement", "")
        except:
            type = None
        try:
            strategy_type = crt_summary.strategyType.split(".")[-1].replace(
                "ProvisionStrategy", ""
            )
        except:
            strategy_type = None
        table.append(
            [
                index + 1,
                crt_summary.name,
                crt_summary.namespace,
                type,
                strategy_type,
                crt_summary.id,
            ]
        )
    return headers, table


def compute_source_template_table(
    cst_summaries: List[ComputeSourceTemplateSummary],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Namespace",
        "Provider",
        "Type",
        "ID",
    ]
    table = []
    for index, cst_summary in enumerate(cst_summaries):
        try:
            type = cst_summary.sourceType.split(".")[-1]
        except:
            type = None
        try:
            provider = cst_summary.provider
        except:
            provider = None
        table.append(
            [
                index + 1,
                cst_summary.name,
                cst_summary.namespace,
                provider,
                type,
                cst_summary.id,
            ]
        )
    return headers, table


def keyring_table(
    keyring_summaries: List[KeyringSummary],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Description",
        "ID",
    ]
    table = []
    for index, keyring in enumerate(keyring_summaries):
        table.append(
            [
                index + 1,
                keyring.name,
                keyring.description,
                keyring.id,
            ]
        )
    return headers, table


def image_family_table(
    image_family_summaries: List[MachineImageFamilySummary],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Name",
        "Access",
        "Namespace",
        "OS Type",
        "ID",
    ]
    table = []
    for index, image_family in enumerate(image_family_summaries):
        table.append(
            [
                index + 1,
                image_family.name,
                image_family.access,
                image_family.namespace,
                image_family.osType,
                image_family.id,
            ]
        )
    return headers, table


def object_path_table(
    object_paths: List[ObjectPath],
) -> (List[str], List[str]):
    headers = ["#", "Name"]
    table = []
    for index, object_path in enumerate(object_paths):
        table.append([index + 1, object_path.name])
    return headers, table


def instances_table(
    instances: List[Instance],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Type",
        "Provider",
        "Instance Type",
        "Private IP",
        "Public IP",
    ]
    table = []
    for index, instance in enumerate(instances):
        table.append(
            [
                index + 1,
                instance.type.split(".")[-1],
                instance.provider,
                instance.instanceType,
                instance.privateIpAddress,
                instance.publicIpAddress,
            ]
        )
    return headers, table


def print_numbered_object_list(
    client: PlatformClient,
    objects: List[Item],
    override_quiet: bool = False,
    showing_all: bool = False,
) -> None:
    """
    Print a numbered list of objects.
    Assume that the list supplied is already sorted.
    """
    if len(objects) == 0:
        return

    print_log(
        "Displaying"
        f" {'all' if showing_all else 'matching'} {get_type_name(objects[0])}(s):",
        override_quiet=override_quiet,
    )
    print()

    headers = None
    if isinstance(objects[0], ComputeRequirement):
        headers, table = compute_requirement_table(objects)
    elif isinstance(objects[0], WorkRequirementSummary):
        headers, table = work_requirement_table(objects)
    elif isinstance(objects[0], TaskGroup):
        headers, table = task_group_table(objects)
    elif isinstance(objects[0], Task):
        headers, table = task_table(objects)
    elif isinstance(objects[0], WorkerPoolSummary):
        headers, table = worker_pool_table(client, objects)
    elif isinstance(objects[0], ComputeRequirementTemplateSummary):
        headers, table = compute_requirement_template_table(objects)
    elif isinstance(objects[0], ComputeSourceTemplateSummary):
        headers, table = compute_source_template_table(objects)
    elif isinstance(objects[0], KeyringSummary):
        headers, table = keyring_table(objects)
    elif isinstance(objects[0], MachineImageFamilySummary):
        headers, table = image_family_table(objects)
    elif isinstance(objects[0], ObjectPath):
        headers, table = object_path_table(objects)
    elif isinstance(objects[0], Instance):
        headers, table = instances_table(objects)
    else:
        table = []
        for index, obj in enumerate(objects):
            try:
                table.append([index + 1, ":", obj.name])
            except:  # Handle the Namespace Storage Configuration case
                table.append([index + 1, ":", obj.namespace])
    if headers is None:
        CONSOLE_TABLE.print(
            indent(tabulate(table, tablefmt="plain"), indent_width=4),
        )
    else:
        CONSOLE_TABLE.print(
            indent(
                tabulate(table, headers=headers, tablefmt="simple_outline"),
                indent_width=4,
            ),
        )
    print()


def print_numbered_strings(objects: List[str], override_quiet: bool = False):
    """
    Print a simple list of strings with numbering.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    table = []
    for index, obj in enumerate(objects):
        table.append([index + 1, ":", obj])
    CONSOLE_TABLE.print(
        indent(tabulate(table, tablefmt="plain"), indent_width=4),
    )
    print()


def sorted_objects(objects: List[Item], reverse: bool = False) -> List[Item]:
    """
    Sort objects by their 'name' property, or 'namespace' in the case of
    Namespace Storage Configurations, or 'instanceType' in the case of
    Instances.
    """
    if len(objects) == 0:
        return objects

    if isinstance(objects[0], Instance):
        return sorted(objects, key=lambda x: x.instanceType, reverse=reverse)

    try:
        return sorted(objects, key=lambda x: x.name, reverse=reverse)
    except:
        return sorted(objects, key=lambda x: x.namespace, reverse=reverse)


def indent(txt: str, indent_width: int = 4) -> str:
    """
    Indent lines of text.
    """
    return text_indent(txt, prefix=" " * indent_width)


def print_json(
    data: Any,
    initial_indent: int = 0,
    drop_first_line: bool = False,
    with_final_comma: bool = False,
):
    """
    Print a dictionary as a JSON data structure, using the compact JSON
    encoder.
    """
    json_string = indent(
        json_dumps(data, indent=JSON_INDENT, cls=CompactJSONEncoder), initial_indent
    )
    if drop_first_line:
        json_string = "\n".join(json_string.splitlines()[1:])
    if with_final_comma:
        CONSOLE_JSON.print(json_string, end=",\n", soft_wrap=True)
    else:
        CONSOLE_JSON.print(json_string, soft_wrap=True)


def print_yd_object(
    yd_object: object,
    initial_indent: int = 0,
    drop_first_line: bool = False,
    with_final_comma: bool = False,
    add_fields: Optional[Dict] = None,
):
    """
    Print a YellowDog object as a JSON data structure,
    using the compact JSON encoder.
    """
    object_data: object = Json.dump(yd_object)
    if add_fields is not None:
        # Requires a copy of the 'object' datatype to be made,
        # in order to insert additional fields
        object_data_new = {}
        for key, value in add_fields.items():
            object_data_new[key] = value
        for key, value in object_data.items():
            object_data_new[key] = value
        object_data = object_data_new
    print_json(object_data, initial_indent, drop_first_line, with_final_comma)


def print_worker_pool(
    crtu: ComputeRequirementTemplateUsage, pwpp: ProvisionedWorkerPoolProperties
):
    """
    Reconstruct and print the JSON-formatted Worker Pool specification.
    """
    print_log("Dry-run: Printing JSON Worker Pool specification")
    wp_data = {
        "provisionedProperties": Json.dump(pwpp),
        "requirementTemplateUsage": Json.dump(crtu),
    }
    print_json(wp_data)


class WorkRequirementSnapshot:
    """
    Represent a complete Work Requirement, with Tasks included within
    Task Group definitions. Note, this is not an 'official' representation
    of a Work Requirement.
    """

    def __init__(self):
        self.wr_data: Dict = {}

    def set_work_requirement(self, wr: WorkRequirement):
        """
        Set the Work Requirement to be represented, processed to
        comply with the API.
        """
        self.wr_data = Json.dump(wr)  # Dictionary holding the complete WR

    def add_tasks(self, task_group_name: str, tasks: List[Task]):
        """
        Add the list of Tasks to a named Task Group within the
        Work Requirement. Cumulative.
        """
        for task_group in self.wr_data[TASK_GROUPS]:
            if task_group[NAME] == task_group_name:
                task_group[TASKS] = task_group.get(TASKS, [])
                task_group[TASKS] += [Json.dump(task) for task in tasks]
                return

    def print(self):
        """
        Print the JSON representation.
        """
        print_log("Dry-run: Printing JSON Work Requirement specification:")
        print_json(self.wr_data)
        print_log("Dry-run: Complete")


def print_compute_template_test_result(result: ComputeRequirementTemplateTestResult):
    """
    Print the results of a test submission of a Dynamic Compute Template.
    """
    if not isinstance(result, ComputeRequirementDynamicTemplateTestResult):
        print_log("Reports are only available for Dynamic Templates")
        return

    report: BestComputeSourceReport = result.report
    sources: List[BestComputeSourceReportSource] = report.sources
    source_table = [
        [
            "#",
            "Rank",
            "Provider",
            "Type",
            "Region",
            "InstanceType",
            "Source Name",
        ]
    ]
    for index, source in enumerate(sources):
        source_table.append(
            [
                index + 1,
                source.rank,
                source.provider,
                source.type,
                source.region,
                source.instanceType,
                source.name,
            ]
        )
    print()
    CONSOLE_TABLE.print(
        indent(tabulate(source_table, headers="firstrow", tablefmt="simple_outline")),
    )
    print()


def print_object_detail(object_detail: ObjectDetail):
    """
    Pretty print an Object Detail.
    Not currently used.
    """
    indent: str = 4 * " "
    print(f"{indent}Namespace:         {object_detail.namespace}")
    print(f"{indent}Object Name:       {object_detail.objectName}")
    print(f"{indent}Object Size:       {object_detail.objectSize:,d} byte(s)")
    print(f"{indent}Last Modified At:  {object_detail.lastModified}")


def print_batch_upload_files(upload_batch_builder: UploadBatchBuilder):
    """
    Print the list of files that will be batch uploaded.
    """
    if ARGS_PARSER.quiet:
        return

    headers = ["#", "Source Object", "Target Object"]
    table = []
    # Yes, I know I shouldn't be accessing '_source_file_entries'
    for index, file_entry in enumerate(upload_batch_builder._source_file_entries):
        table.append(
            [
                index + 1,
                file_entry.source_file_path,
                f"{upload_batch_builder.namespace}::{file_entry.default_object_name}",
            ]
        )
    print()
    print(
        indent(
            tabulate(table, headers=headers, tablefmt="simple_outline"), indent_width=4
        )
    )
    print()


def print_batch_download_files(
    download_batch_builder: DownloadBatchBuilder, flatten_downloads: bool = False
):
    """
    Print the list of files that will be batch downloaded.
    """
    if ARGS_PARSER.quiet:
        return

    headers = ["#", "Source Object", "Target Object"]
    directory_separator = "\\" if os_name == "nt" else "/"
    table = []
    # Yes, I know I shouldn't be accessing '_source_object_entries'
    for index, object_entry in enumerate(download_batch_builder._source_object_entries):
        object_source = f"{object_entry.namespace}::{object_entry.object_name}"
        object_target = (
            f"{object_entry.object_name.replace('/', directory_separator)}"
            if flatten_downloads is False
            else f"{object_entry.object_name.split('/')[-1:][0]}"
        )
        table.append(
            [
                index + 1,
                object_source,
                relpath(
                    f"{download_batch_builder.destination_folder}"
                    f"{directory_separator}"
                    f"{object_target}"
                ),
            ]
        )
    print()
    CONSOLE_TABLE.print(
        indent(
            tabulate(table, headers=headers, tablefmt="simple_outline"), indent_width=4
        ),
    )
    print()


def print_event(event: str, id_type: YDIDType):
    """
    Print a YellowDog event.
    """
    data_prefix = "data:"

    # Ignore events that don't have a 'data:' payload
    if not event.startswith(data_prefix):
        return

    event_data: Dict = json_loads(event.replace(data_prefix, ""))
    if ARGS_PARSER.raw_events:
        print_json(event_data)
        return

    indent = "\n" + (" " * PREFIX_LEN) + "--> "
    indent_2 = "\n" + (" " * (PREFIX_LEN + 4))

    if id_type == YDIDType.WORK_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        for task_group in event_data["taskGroups"]:
            msg += (
                f"{indent}Task Group '{task_group['name']}' [{task_group['status']}]:"
                f" {task_group['taskSummary']['taskCount']} Task(s){indent_2}{task_group['taskSummary']['statusCounts']['PENDING']} PENDING,"
                f" {task_group['taskSummary']['statusCounts']['READY']} READY,"
                f" {task_group['taskSummary']['statusCounts']['ALLOCATED']} ALLOCATED,"
                f" {task_group['taskSummary']['statusCounts']['EXECUTING']} EXECUTING"
            )
            if task_group["taskSummary"]["statusCounts"]["UPLOADING"] != 0:
                msg += (
                    f", {task_group['taskSummary']['statusCounts']['UPLOADING']} UPLOADING"
                )
            if task_group["taskSummary"]["statusCounts"]["DOWNLOADING"] != 0:
                msg += (
                    f", {task_group['taskSummary']['statusCounts']['DOWNLOADING']} DOWNLOADING"
                )
            msg += (
                f", {task_group['taskSummary']['statusCounts']['COMPLETED']} COMPLETED"
            )
            if task_group["taskSummary"]["statusCounts"]["CANCELLED"] != 0:
                msg += f", {task_group['taskSummary']['statusCounts']['CANCELLED']} CANCELLED"
            if task_group["taskSummary"]["statusCounts"]["ABORTED"] != 0:
                msg += f", {task_group['taskSummary']['statusCounts']['ABORTED']} ABORTED"
            if task_group["taskSummary"]["statusCounts"]["FAILED"] != 0:
                msg += f", {task_group['taskSummary']['statusCounts']['FAILED']} FAILED"

    elif id_type == YDIDType.WORKER_POOL:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += (
            f"{indent}Node(s):       "
            f" {event_data['nodeSummary']['statusCounts']['RUNNING']} running,"
            f" {event_data['nodeSummary']['statusCounts']['TERMINATED']} terminated,"
            f" {event_data['nodeSummary']['statusCounts']['DEREGISTERED']} deregistered"
        )
        try:
            msg += (
                f"{indent}Node Action(s):"
                f" {event_data['nodeSummary']['actionQueueStatuses']['WAITING']} waiting,"
                f" {event_data['nodeSummary']['actionQueueStatuses']['EXECUTING']} executing,"
                f" {event_data['nodeSummary']['actionQueueStatuses']['FAILED']} failed"
            )
        except TypeError:
            pass
        msg += (
            f"{indent}Worker(s):     "
            f" {event_data['workerSummary']['statusCounts']['DOING_TASK']} doing task,"
            f" {event_data['workerSummary']['statusCounts']['SLEEPING']} sleeping,"
            f" {event_data['workerSummary']['statusCounts']['SHUTDOWN']} shutdown,"
            f" {event_data['workerSummary']['statusCounts']['LATE']} late,"
            f" {event_data['workerSummary']['statusCounts']['LOST']} lost,"
            f" {event_data['workerSummary']['statusCounts']['FOUND']} found"
        )

    elif id_type == YDIDType.COMPUTE_REQ:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += (
            f"{indent}Instance(s): "
            f"{event_data['targetInstanceCount']} target,"
            f" {event_data['expectedInstanceCount']} expected"
        )
        for source in event_data["provisionStrategy"]["sources"]:
            msg += (
                f"{indent}Source: '{source['name']}':"
                f" {source['instanceSummary']['statusCounts']['PENDING']} pending,"
                f" {source['instanceSummary']['statusCounts']['RUNNING']} running,"
                f" {source['instanceSummary']['statusCounts']['TERMINATING']} terminating,"
                f" {source['instanceSummary']['statusCounts']['TERMINATED']} terminated"
            )

    else:
        return

    print_log(msg, no_fill=True)
