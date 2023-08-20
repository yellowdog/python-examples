"""
Functions focused on print outputs.
"""

import sys
from datetime import datetime
from json import dumps as json_dumps
from os import get_terminal_size
from os import name as os_name
from os.path import relpath
from textwrap import fill
from textwrap import indent as text_indent
from typing import Any, Dict, List, Optional, TypeVar

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
from yd_commands.config_keys import NAME, TASK_GROUPS, TASKS
from yd_commands.object_utilities import Item

JSON_INDENT = 2

try:
    LOG_WIDTH = get_terminal_size().columns
except OSError:
    LOG_WIDTH = 120  # Default log line width


def print_string(msg: str = "") -> str:
    """
    Message output format, with tidy line-wrapping calibrated
    for the terminal width.
    """
    prefix = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : "
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
    flush: bool = True,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    print(
        print_string(log_message),
        flush=flush,
    )


ErrorObject = TypeVar(
    "ErrorObject",
    Exception,
    str,
)


def print_error(error_obj: ErrorObject):
    """
    Print an error message to stderr.
    """
    print(print_string(f"Error: {error_obj}"), file=sys.stderr, flush=True)


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

    return TYPE_MAP.get(type(obj), "")


def compute_requirement_table(
    cr_list: List[ComputeRequirement],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Compute Requirement Name",
        "Tag",
        "Instance Counts",
        "Status",
    ]
    table = []
    for index, cr in enumerate(cr_list):
        table.append(
            [
                index + 1,
                cr.name,
                f"{cr.tag}",
                (
                    f"Target={cr.targetInstanceCount:,d},"
                    f" Expected={cr.expectedInstanceCount:,d}"
                ),
                (
                    f"{cr.status}"
                    if cr.nextStatus is None
                    else f"{cr.status} -> {cr.nextStatus}"
                ),
            ]
        )
    return headers, table


def work_requirement_table(
    wr_summary_list: List[WorkRequirementSummary],
) -> List[List]:
    table = []
    for index, wr_summary in enumerate(wr_summary_list):
        table.append(
            [
                index + 1,
                ":",
                wr_summary.name,
                f"[{wr_summary.status}]",
            ]
        )
    return table


def task_group_table(
    task_group_list: List[TaskGroup],
) -> List[List]:
    table = []
    for index, task_group in enumerate(task_group_list):
        table.append(
            [
                index + 1,
                task_group.name,
                f"[{task_group.status}]",
            ]
        )
    return table


def task_table(task_list: List[Task]) -> List[List]:
    table = []
    for index, task in enumerate(task_list):
        table.append(
            [
                index + 1,
                ":",
                task.name,
                f"[{task.status}]",
            ]
        )
    return table


def worker_pool_table(
    client: PlatformClient, worker_pool_summaries: List[WorkerPoolSummary]
) -> (List[str], List[List]):
    headers = [
        "#",
        "Worker Pool Name",
        "Type",
        "Status",
        "Running",
        "Min",
        "Max",
        "Term.",
        "Late",
        "Lost",
        "Dereg.",
    ]
    table = []
    for index, worker_pool_summary in enumerate(worker_pool_summaries):
        worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_id(
            worker_pool_summary.id
        )
        try:
            min_nodes = str(worker_pool.properties.minNodes)
        except:
            min_nodes = " "
        try:
            max_nodes = str(worker_pool.properties.maxNodes)
        except:
            max_nodes = " "
        node_summary: NodeSummary = worker_pool.nodeSummary
        nodes_running = node_summary.statusCounts[NodeStatus.RUNNING]
        nodes_late = node_summary.statusCounts[NodeStatus.LATE]
        nodes_lost = node_summary.statusCounts[NodeStatus.LOST]
        nodes_terminated = node_summary.statusCounts[NodeStatus.TERMINATED]
        nodes_deregistered = node_summary.statusCounts[NodeStatus.DEREGISTERED]

        table.append(
            [
                index + 1,
                worker_pool_summary.name,
                f"{worker_pool_summary.type.split('.')[-1:][0]}",
                f"{worker_pool_summary.status}",
                f"{nodes_running}",
                f"{min_nodes}",
                f"{max_nodes}",
                f"{nodes_terminated}",
                f"{nodes_late}",
                f"{nodes_lost}",
                f"{nodes_deregistered}",
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


def print_numbered_object_list(
    client: PlatformClient,
    objects: List[Item],
    parent: Optional[Item] = None,
    override_quiet: bool = False,
) -> None:
    """
    Print a numbered list of objects.
    Assume that the list supplied is already sorted.
    """
    if len(objects) == 0:
        return

    print_log(
        f"Displaying matching {get_type_name(objects[0])}(s):",
        override_quiet=override_quiet,
    )
    print()

    headers = None
    if isinstance(objects[0], ComputeRequirement):
        headers, table = compute_requirement_table(objects)
    elif isinstance(objects[0], WorkRequirementSummary):
        table = work_requirement_table(objects)
    elif isinstance(objects[0], TaskGroup):
        table = task_group_table(objects)
    elif isinstance(objects[0], Task):
        table = task_table(objects)
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
    else:
        table = []
        for index, obj in enumerate(objects):
            try:
                table.append([index + 1, ":", obj.name])
            except:  # Handle the Namespace Storage Configuration case
                table.append([index + 1, ":", obj.namespace])
    if headers is None:
        print(indent(tabulate(table, tablefmt="plain"), indent_width=4))
    else:
        print(
            indent(
                tabulate(table, headers=headers, tablefmt="simple_outline"),
                indent_width=4,
            )
        )
    print()


def print_numbered_strings(objects: List[str], override_quiet: bool = False):
    """
    Print a simple list of strings with numbering
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    table = []
    for index, obj in enumerate(objects):
        table.append([index + 1, ":", obj])
    print(indent(tabulate(table, tablefmt="plain"), indent_width=4))
    print()


def sorted_objects(objects: List[Item], reverse: bool = False) -> List[Item]:
    """
    Sort objects by their 'name' property, or 'namespace' in the case of
    Namespace Storage Configurations.
    """
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
        print(json_string, end=",\n")
    else:
        print(json_string)


def print_yd_object(
    yd_object: object,
    initial_indent: int = 0,
    drop_first_line: bool = False,
    with_final_comma: bool = False,
    add_fields: Optional[Dict] = None,
):
    """
    Print a YellowDog object as a JSON data structure,
    using the compact JSON encoder
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
        Print the JSON representation
        """
        print_log("Dry-run: Printing JSON Work Requirement specification:")
        print_json(self.wr_data)
        print_log("Dry-run: Complete")


def print_compute_template_test_result(result: ComputeRequirementTemplateTestResult):
    """
    Print the results of a test submission of a Dynamic Compute Template
    """
    if not isinstance(result, ComputeRequirementDynamicTemplateTestResult):
        print_log("Reports are only available for Dynamic Templates")
        return

    report: BestComputeSourceReport = result.report
    sources: List[BestComputeSourceReportSource] = report.sources
    source_table = [
        [
            "",
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
    print(tabulate(source_table, headers="firstrow", tablefmt="simple_outline"))
    print()


def print_object_detail(object_detail: ObjectDetail):
    """
    Pretty print an Object Detail
    """
    indent: str = 4 * " "
    print(f"{indent}Namespace:         {object_detail.namespace}")
    print(f"{indent}Object Name:       {object_detail.objectName}")
    print(f"{indent}Object Size:       {object_detail.objectSize:,d} byte(s)")
    print(f"{indent}Last Modified At:  {object_detail.lastModified}")


def print_batch_upload_files(upload_batch_builder: UploadBatchBuilder):
    """
    Print the list of files that will be batch uploaded
    """
    if ARGS_PARSER.quiet:
        return

    headers = ["Item", "Source Object", "->", "Target Object"]
    table = []
    # Yes, I know I shouldn't be accessing '_source_file_entries'
    for index, file_entry in enumerate(upload_batch_builder._source_file_entries):
        table.append(
            [
                index + 1,
                file_entry.source_file_path,
                "->",
                f"{upload_batch_builder.namespace}::{file_entry.default_object_name}",
            ]
        )
    print()
    print(indent(tabulate(table, headers=headers, tablefmt="simple"), indent_width=4))
    print()


def print_batch_download_files(
    download_batch_builder: DownloadBatchBuilder, flatten_downloads: bool = False
):
    """
    Print the list of files that will be batch downloaded.
    """
    if ARGS_PARSER.quiet:
        return

    headers = ["Item", "Source Object", "->", "Target Object"]
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
                "->",
                relpath(
                    f"{download_batch_builder.destination_folder}"
                    f"{directory_separator}"
                    f"{object_target}"
                ),
            ]
        )
    print()
    print(indent(tabulate(table, headers=headers, tablefmt="simple"), indent_width=4))
    print()
