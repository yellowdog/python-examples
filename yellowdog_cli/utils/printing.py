"""
Functions focused on print outputs.
"""

from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime
from json import dumps as json_dumps
from json import loads as json_loads
from os import get_terminal_size
from os import name as os_name
from os.path import relpath
from textwrap import fill
from textwrap import indent as text_indent
from typing import Any, Dict, List, Optional, Tuple, Union

from rich.console import Console, Theme
from rich.highlighter import JSONHighlighter, RegexHighlighter
from tabulate import tabulate
from yellowdog_client import PlatformClient
from yellowdog_client.common.json import Json
from yellowdog_client.model import (
    Allowance,
    Application,
    BestComputeSourceReport,
    BestComputeSourceReportSource,
    ComputeRequirement,
    ComputeRequirementDynamicTemplateTestResult,
    ComputeRequirementTemplateSummary,
    ComputeRequirementTemplateTestResult,
    ComputeRequirementTemplateUsage,
    ComputeSourceTemplateSummary,
    ConfiguredWorkerPool,
    ExternalUser,
    Group,
    Instance,
    InternalUser,
    KeyringSummary,
    MachineImageFamilySummary,
    NamespacePolicy,
    Node,
    ObjectDetail,
    ObjectPath,
    ProvisionedWorkerPool,
    ProvisionedWorkerPoolProperties,
    Role,
    Task,
    TaskGroup,
    User,
    Worker,
    WorkerPoolSummary,
    WorkRequirement,
    WorkRequirementSummary,
)
from yellowdog_client.object_store.download import DownloadBatchBuilder
from yellowdog_client.object_store.upload import UploadBatchBuilder

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.cloudwizard_aws_types import AWSAvailabilityZone
from yellowdog_cli.utils.compact_json import CompactJSONEncoder
from yellowdog_cli.utils.items import Item
from yellowdog_cli.utils.property_names import NAME, TASK_GROUPS, TASKS
from yellowdog_cli.utils.rich_console_input_fixed import ConsoleWithInputBackspaceFixed
from yellowdog_cli.utils.settings import (
    DEFAULT_LOG_WIDTH,
    DEFAULT_THEME,
    ERROR_STYLE,
    HIGHLIGHTED_STATES,
    JSON_INDENT,
    MAX_LINES_COLOURED_FORMATTING,
    NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR,
    PROP_RESOURCE,
    WARNING_STYLE,
)
from yellowdog_cli.utils.ydid_utils import YDIDType

try:
    LOG_WIDTH = get_terminal_size().columns
except OSError:
    LOG_WIDTH = DEFAULT_LOG_WIDTH  # Default log line width


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
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*:[0-9]*)",
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*:[0-9]*:[0-9]*)",
        r"(?P<url>(https?):((//)|(\\\\))+[\w\d:#@%/;$~_?\+-=\\\.&]*)",
    ] + HIGHLIGHTED_STATES


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
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*:[0-9]*)",
        r"(?P<ydid>ydid:[a-z]*:[0-9ABCDEF]*:[0-9abcdef-]*:[0-9]*:[0-9]*)",
    ] + HIGHLIGHTED_STATES


pyexamples_theme = Theme(DEFAULT_THEME)


CONSOLE = ConsoleWithInputBackspaceFixed(
    highlighter=PrintLogHighlighter(), theme=pyexamples_theme
)
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

    if no_fill or msg == "" or msg.isspace() or ARGS_PARSER.no_format:
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


def print_simple(
    log_message: str = "",
    override_quiet: bool = False,
):
    """
    Simple print function without timestamp.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    CONSOLE.print(log_message)


def print_log(
    log_message: str = "",
    override_quiet: bool = False,
    no_fill: bool = False,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    if ARGS_PARSER.no_format:
        print(print_string(log_message, no_fill=no_fill), flush=True)
        return

    CONSOLE.print(print_string(log_message, no_fill=no_fill))


def print_error(error_obj: Union[Exception, str]):
    """
    Print an error message to stderr.
    """
    if ARGS_PARSER.no_format:
        print(print_string(f"Error: {error_obj}"), flush=True)
        return

    CONSOLE_ERR.print(print_string(f"Error: {error_obj}"), style=ERROR_STYLE)


def print_warning(
    warning: str,
    override_quiet: bool = False,
    no_fill: bool = False,
):
    """
    Print a warning.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    if ARGS_PARSER.no_format:
        print(print_string(f"Warning: {warning}", no_fill=no_fill), flush=True)
        return

    CONSOLE.print(
        print_string(f"Warning: {warning}", no_fill=no_fill), style=WARNING_STYLE
    )


TYPE_MAP = {
    AWSAvailabilityZone: "AWS Availability Zones",
    Allowance: "Allowance",
    ComputeRequirement: "Compute Requirement",
    ComputeRequirementTemplateSummary: "Compute Requirement Template",
    ComputeSourceTemplateSummary: "Compute Source Template",
    ConfiguredWorkerPool: "Configured Worker Pool",
    KeyringSummary: "Keyring",
    MachineImageFamilySummary: "Machine Image Family",
    NamespacePolicy: "Namespace Policy",
    Node: "Node",
    ObjectPath: "Object Path",
    ProvisionedWorkerPool: "Provisioned Worker Pool",
    Task: "Task",
    TaskGroup: "Task Group",
    WorkRequirementSummary: "Work Requirement",
    Worker: "Worker",
    WorkerPoolSummary: "Worker Pool",
}


def print_table_core(table: str):
    """
    Core function for printing a table.
    """
    if ARGS_PARSER.no_format or table.count("\n") > MAX_LINES_COLOURED_FORMATTING:
        print(table, flush=True)
    else:
        CONSOLE_TABLE.print(table)


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

    if type(obj).__name__.endswith("Allowance"):
        # Special case
        return "Allowance"

    return TYPE_MAP.get(type(obj), "")


def compute_requirement_table(
    cr_list: List[ComputeRequirement],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Compute Requirement Name",
        "Namespace",
        "Tag",
        "Status (Tgt/Exp/Alive)",
        "Compute Requirement ID",
    ]
    table = []
    for index, cr in enumerate(cr_list):
        alive_count = sum(
            [
                source.instanceSummary.aliveCount
                for source in cr.provisionStrategy.sources
            ]
        )
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
                + f" ({cr.targetInstanceCount:,d}/{cr.expectedInstanceCount:,d}/{alive_count:,d})",
                cr.id,
            ]
        )
    return headers, table


def work_requirement_table(
    wr_summary_list: List[WorkRequirementSummary],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Work Requirement Name",
        "Namespace",
        "Tag",
        "Status",
        "Work Requirement ID",
    ]
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
    headers = ["#", "Task Group Name", "Status", "Task Group ID"]
    table = []
    for index, task_group in enumerate(task_group_list):
        status_msg = str(task_group.status)
        if task_group.starved:
            status_msg += "/STARVED"
        if task_group.waitingOnDependency:
            status_msg += "/WAITING"
        table.append(
            [
                index + 1,
                task_group.name,
                status_msg,
                task_group.id,
            ]
        )
    return headers, table


def task_table(task_list: List[Task]) -> (List[str], List[List]):
    headers = ["#", "Task Name", "Status", "Task ID"]
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
        "Namespace",
        "Type",
        "Status",
        "Worker Pool ID",
    ]
    table = []
    for index, worker_pool_summary in enumerate(worker_pool_summaries):
        table.append(
            [
                index + 1,
                worker_pool_summary.name,
                worker_pool_summary.namespace,
                f"{worker_pool_summary.type.split('.')[-1:][0].replace('WorkerPool', '')}",
                f"{worker_pool_summary.status}",
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
        "Compute Requirement Template ID",
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
        "Compute Source Template ID",
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
        "Keyring ID",
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
        "Image Family ID",
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
        "Provider",
        "Instance Type",
        "Hostname",
        "Status",
        "Private IP",
        "Public IP",
    ]
    table = []
    for index, instance in enumerate(instances):
        table.append(
            [
                index + 1,
                instance.provider,
                instance.instanceType,
                instance.hostname,
                instance.status,
                instance.privateIpAddress,
                instance.publicIpAddress,
            ]
        )
    return headers, table


def nodes_table(
    nodes: List[Node],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Worker Pool Name",
        "Provider",
        "RAM",
        "vCPUs",
        "Task Types",
        "Worker Tag",
        "# Workers",
        "Status",
        "Node ID",
    ]
    table = []
    for index, node in enumerate(nodes):
        if node.details is None:
            continue
        table.append(
            [
                index + 1,
                node.workerPoolName,
                node.details.provider,
                node.details.ram,
                node.details.vcpus,
                ", ".join(node.details.supportedTaskTypes),
                node.details.workerTag,
                len(node.workers),
                node.status,
                node.id,
            ]
        )
    return headers, table


def workers_table(
    workers: List[Worker],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Worker Pool Name",
        "Task Types",
        "Worker Tag",
        "Status",
        "Claims",
        "Exclusive?",
        "Worker ID",
    ]
    table = []
    for index, worker in enumerate(workers):
        table.append(
            [
                index + 1,
                worker.workerPoolName,
                ", ".join(worker.taskTypes),
                worker.workerTag,
                worker.status,
                worker.claimCount,
                worker.exclusive,
                worker.id,
            ]
        )
    return headers, table


def allowances_table(
    allowances: List[Allowance],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Type",
        "Description",
        "Allowed Hrs",
        "Remaining Hrs",
        "Limit",
        "Reset",
        "Allowances ID",
    ]
    table = []
    for index, allowance in enumerate(allowances):
        table.append(
            [
                index + 1,
                allowance.type.split(".")[-1],
                allowance.description,
                allowance.allowedHours,
                allowance.remainingHours,
                allowance.limitEnforcement,
                (
                    f"{allowance.resetInterval} {allowance.resetType}"
                    if allowance.resetInterval is not None
                    else ""
                ),
                allowance.id,
            ]
        )
    return headers, table


def attribute_definitions_table(
    attribute_definitions: List[Dict],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Name",
        "Type",
        "Title",
        "Description",
    ]
    table = []
    for index, attribute_definition in enumerate(attribute_definitions):
        table.append(
            [
                index + 1,
                attribute_definition["name"],
                attribute_definition["type"].split(".")[-1],
                attribute_definition["title"],
                attribute_definition.get("description", ""),
            ]
        )
    return headers, table


def aws_availability_zone_table(
    aws_azs: List[AWSAvailabilityZone],
) -> (List[str], List[str]):
    headers = [
        "#",
        "Availability Zone",
        "Default Subnet ID",
        "Default Security Group ID",
    ]
    table = []
    for index, az in enumerate(aws_azs):
        table.append(
            [
                index + 1,
                az.az,
                az.default_subnet_id,
                az.default_sec_grp.id,
            ]
        )
    return headers, table


def namespace_policies_table(
    ns_policies: List[NamespacePolicy],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Namespace",
        "AutoscalingMaxNodes",
    ]
    table = []
    for index, ns_policy in enumerate(ns_policies):
        table.append(
            [
                index + 1,
                ns_policy.namespace,
                ns_policy.autoscalingMaxNodes,
            ]
        )
    return headers, table


def users_table(
    users: List[User],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "User Type",
        "Username",
        "Email",
        "ID",
    ]
    table = []
    for index, user in enumerate(users):
        if isinstance(user, InternalUser):
            table.append(
                [
                    index + 1,
                    user.name,
                    "Internal",
                    user.username,
                    user.email,
                    user.id,
                ]
            )
        elif isinstance(user, ExternalUser):  # External user
            table.append(
                [
                    index + 1,
                    user.name,
                    "External",
                    "",
                    user.email,
                    user.id,
                ]
            )
    return headers, table


def applications_table(
    applications: List[Application],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Description",
        "ID",
    ]
    table = []
    for index, application in enumerate(applications):
        table.append(
            [
                index + 1,
                application.name,
                application.description,
                application.id,
            ]
        )
    return headers, table


def groups_table(
    groups: List[Group],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Admin Group?",
        "Description",
        "Roles",
        "ID",
    ]
    table = []
    for index, group in enumerate(groups):
        table.append(
            [
                index + 1,
                group.name,
                group.adminGroup,
                f"{group.description[:40] + '...' if len(group.description) > 40 else group.description}",
                ", ".join([x.role.name for x in group.roles]),
                group.id,
            ]
        )
    return headers, table


def roles_table(
    roles: List[Role],
) -> (List[str], List[List]):
    headers = [
        "#",
        "Name",
        "Permissions",
        "ID",
    ]
    table = []
    for index, role in enumerate(roles):
        permissions = ", ".join(sorted([x.value for x in role.permissions]))
        table.append(
            [
                index + 1,
                role.name,
                f"{permissions[:40] + '...' if len(permissions) > 40 else permissions}",
                role.id,
            ]
        )
    return headers, table


def print_numbered_object_list(
    client: PlatformClient,
    objects: List[Union[Item, str, Dict]],
    object_type_name: Optional[str] = None,
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
        f" {'all' if showing_all else 'matching'}"
        f" {(object_type_name if object_type_name is not None else get_type_name(objects[0]))}(s):",
        override_quiet=override_quiet,
    )
    print()

    headers = None
    if isinstance(objects[0], str):
        headers = ["#", "Name"]
        table = [[index + 1, name] for index, name in enumerate(objects)]
    elif isinstance(objects[0], ComputeRequirement):
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
    elif isinstance(objects[0], Allowance):
        headers, table = allowances_table(objects)
    elif isinstance(objects[0], AWSAvailabilityZone):
        headers, table = aws_availability_zone_table(objects)
    elif object_type_name == "Attribute Definition":
        headers, table = attribute_definitions_table(objects)
    elif isinstance(objects[0], NamespacePolicy):
        headers, table = namespace_policies_table(objects)
    elif isinstance(objects[0], Node):
        headers, table = nodes_table(objects)
    elif isinstance(objects[0], Worker):
        headers, table = workers_table(objects)
    elif isinstance(objects[0], User):
        headers, table = users_table(objects)
    elif isinstance(objects[0], Application):
        headers, table = applications_table(objects)
    elif isinstance(objects[0], Group):
        headers, table = groups_table(objects)
    elif isinstance(objects[0], Role):
        headers, table = roles_table(objects)
    else:
        table = []
        for index, obj in enumerate(objects):
            try:
                table.append([index + 1, ":", obj.name])
            except:  # Handle the Namespace Storage Configuration case
                table.append([index + 1, ":", obj.namespace])
    if headers is None:
        print_table_core(indent(tabulate(table, tablefmt="plain"), indent_width=4))
    else:
        print_table_core(
            indent(
                tabulate(table, headers=headers, tablefmt="simple_outline"),
                indent_width=4,
            )
        )
    print(flush=True)


def print_numbered_strings(objects: List[str], override_quiet: bool = False):
    """
    Print a simple list of strings with numbering.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    table = []
    for index, obj in enumerate(objects):
        table.append([index + 1, ":", obj])

    print_table_core(indent(tabulate(table, tablefmt="plain"), indent_width=4))
    print(flush=True)


def sorted_objects(
    objects: List[Union[Item, str]], reverse: bool = False
) -> List[Item]:
    """
    Sort objects by their 'name' property, or 'namespace' in the case of
    Namespace Storage Configurations, or 'instanceType' in the case of
    Instances, etc.
    """
    if len(objects) == 0:
        return objects

    if ARGS_PARSER.reverse is not None:
        reverse = ARGS_PARSER.reverse

    if isinstance(objects[0], str):
        return sorted(objects, reverse=reverse)

    if isinstance(objects[0], Instance):
        return sorted(objects, key=lambda x: x.instanceType, reverse=reverse)

    if isinstance(objects[0], Node):
        # Note: worker_pool_name property is added dynamically in yd_list
        return sorted(objects, key=lambda x: str(x.workerPoolName), reverse=reverse)

    if isinstance(objects[0], Worker):
        # Note: worker_pool_name property is added dynamically in yd_list
        return sorted(objects, key=lambda x: str(x.workerPoolName), reverse=reverse)

    if isinstance(objects[0], AWSAvailabilityZone):
        return sorted(objects)

    if isinstance(objects[0], Allowance):
        try:
            return sorted(objects, key=lambda x: x.description, reverse=reverse)
        except TypeError:
            return objects

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

    # Coloured formatting of JSON console output is expensive
    if json_string.count("\n") > MAX_LINES_COLOURED_FORMATTING or ARGS_PARSER.no_format:
        if with_final_comma:
            print(json_string, end=",\n", flush=True)
        else:
            print(json_string, flush=True)

    else:
        if with_final_comma:
            CONSOLE_JSON.print(json_string, end=",\n", soft_wrap=True)
        else:
            CONSOLE_JSON.print(json_string, soft_wrap=True)

    if ARGS_PARSER.output_file is not None:  # Also output to a nominated file
        _print_to_file(
            json_string=json_string,
            output_file=ARGS_PARSER.output_file,
            with_final_comma=with_final_comma,
        )


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


def print_yd_object_list(
    objects: List[Tuple[Any, Optional[str]]],  # Tuples are (object, resource_type_name)
):
    """
    Print a JSON list of objects.
    """

    if ARGS_PARSER.output_file is not None:
        print_log(f"Copying detailed resource list to '{ARGS_PARSER.output_file}'")

    if len(objects) > 1:
        print("[")
        if ARGS_PARSER.output_file is not None:
            _print_to_file("[", ARGS_PARSER.output_file)

    for index, (object_, resource_type_name) in enumerate(objects):
        print_yd_object(
            object_,
            initial_indent=2 if len(objects) > 1 else 0,
            with_final_comma=(True if index < len(objects) - 1 else False),
            add_fields=(
                {}
                if resource_type_name is None
                else {PROP_RESOURCE: resource_type_name}
            ),
        )

    if len(objects) > 1:
        print("]")
        if ARGS_PARSER.output_file is not None:
            _print_to_file("]", ARGS_PARSER.output_file)


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
            "Instance Type",
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
    print(flush=True)
    print_table_core(
        indent(tabulate(source_table, headers="firstrow", tablefmt="simple_outline"))
    )
    print(flush=True)


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
                f"{upload_batch_builder.namespace}{NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR}{file_entry.default_object_name}",
            ]
        )
    print(flush=True)
    print_table_core(
        indent(
            tabulate(table, headers=headers, tablefmt="simple_outline"),
            indent_width=4,
        )
    )
    print(flush=True)


def print_batch_download_files(
    download_batch_builder: DownloadBatchBuilder, flatten_downloads: bool = False
) -> int:
    """
    Print the list of files that will be batch downloaded.
    Returns the number of files printed.
    """
    if ARGS_PARSER.quiet:
        return 0

    headers = ["#", "Source Object", "Target Object"]
    directory_separator = "\\" if os_name == "nt" else "/"
    table = []
    counter = 0
    # Yes, I know I shouldn't be accessing '_source_object_entries'
    for index, object_entry in enumerate(download_batch_builder._source_object_entries):
        object_source = f"{object_entry.namespace}{NAMESPACE_OBJECT_STORE_PREFIX_SEPARATOR}{object_entry.object_name}"
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
        counter += 1

    print(flush=True)
    print_table_core(
        indent(
            tabulate(table, headers=headers, tablefmt="simple_outline"),
            indent_width=4,
        )
    )
    print(flush=True)
    return counter


@dataclass
class StatusCount:
    name: str
    include_if_zero: bool = False


STATUS_COUNTS_TASKS = [
    StatusCount("PENDING"),
    StatusCount("READY", True),
    StatusCount("ALLOCATED"),
    StatusCount("EXECUTING", True),
    StatusCount("UPLOADING"),
    StatusCount("DOWNLOADING"),
    StatusCount("COMPLETED", True),
    StatusCount("CANCELLED"),
    StatusCount("ABORTED"),
    StatusCount("FAILED"),
]

STATUS_COUNTS_INSTANCES = [
    StatusCount("PENDING", True),
    StatusCount("RUNNING", True),
    StatusCount("STOPPING"),
    StatusCount("STOPPED"),
    StatusCount("TERMINATING"),
    StatusCount("TERMINATED", True),
    StatusCount("UNAVAILABLE"),
    StatusCount("UNKNOWN"),
]

STATUS_COUNTS_WORKERS = [
    StatusCount("DOING_TASK", True),
    StatusCount("STOPPED", True),
    StatusCount("SLEEPING"),  # Should no longer see this state
    StatusCount("STARTING"),
    StatusCount("LATE"),
    StatusCount("FOUND"),
    StatusCount("LOST"),
    StatusCount("SHUTDOWN"),
]

STATUS_COUNTS_NODES = [
    StatusCount("RUNNING", True),
    StatusCount("TERMINATED", True),
    StatusCount("DEREGISTERED"),
    StatusCount("LATE"),
    StatusCount("LOST"),
]

STATUS_COUNTS_NODE_ACTIONS = [
    # StatusCount("EMPTY", True),
    StatusCount("WAITING", True),
    StatusCount("EXECUTING", True),
    StatusCount("FAILED"),
]

STATUS_COUNTS_COMPUTE_REQ = [
    StatusCount("PENDING", True),
    StatusCount("RUNNING", True),
    StatusCount("STOPPING"),
    StatusCount("STOPPED"),
    StatusCount("TERMINATING"),
    StatusCount("TERMINATED"),
    StatusCount("UNAVAILABLE"),
    StatusCount("UNKNOWN"),
]


def status_counts_msg(
    status_counts: List[StatusCount],
    counts_data: Dict,
    empty_msg_if_zero_total: bool = False,
) -> str:
    """
    Generate the count of items in specific statuses.
    """
    msg = ""
    first = True
    total_count = 0
    for status_count in status_counts:
        try:
            count = counts_data[status_count.name]
            if count > 0 or status_count.include_if_zero:
                msg += f"{'' if first else ', '}{count:,d} {status_count.name}"
                first = False
                total_count += count
        except (KeyError, TypeError):
            continue  # Do nothing if a status is not present in the event data
    if total_count > 0 or empty_msg_if_zero_total is False:
        return msg
    else:
        return ""


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

    if id_type == YDIDType.WORK_REQUIREMENT:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        for task_group in event_data["taskGroups"]:
            status = task_group["status"]
            if task_group["waitingOnDependency"] is True:
                status += "/WAITING"
            elif task_group["starved"] is True:
                status += "/STARVED"
            msg += (
                f"{indent}[{status}] Task Group '{task_group['name']}':"
                f" {task_group['taskSummary']['taskCount']:,d} Task(s){indent_2}"
            )
            msg += status_counts_msg(
                STATUS_COUNTS_TASKS, task_group["taskSummary"]["statusCounts"]
            )

    elif id_type == YDIDType.WORKER_POOL:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        msg += f"{indent}Node(s):        " + status_counts_msg(
            STATUS_COUNTS_NODES, event_data["nodeSummary"]["statusCounts"]
        )
        node_actions_msg = status_counts_msg(
            STATUS_COUNTS_NODE_ACTIONS,
            event_data["nodeSummary"]["actionQueueStatuses"],
            empty_msg_if_zero_total=True,
        )
        if len(node_actions_msg) > 0:
            msg += f"{indent}Node Action(s): " + node_actions_msg
        workers_msg = status_counts_msg(
            STATUS_COUNTS_WORKERS,
            event_data["workerSummary"]["statusCounts"],
            empty_msg_if_zero_total=True,
        )
        if len(workers_msg) > 0:
            msg += f"{indent}Worker(s):      " + workers_msg

    elif id_type == YDIDType.COMPUTE_REQUIREMENT:
        msg = f"{id_type.value} '{event_data['name']}' is {event_data['status']}"
        alive_count = sum(
            [
                int(source["instanceSummary"]["aliveCount"])
                for source in event_data["provisionStrategy"]["sources"]
            ]
        )
        msg += (
            f"{indent}Instance(s): "
            f"{event_data['targetInstanceCount']:,d} TARGET,"
            f" {event_data['expectedInstanceCount']:,d} EXPECTED,"
            f" {alive_count:,d} ALIVE"
        )
        for source in event_data["provisionStrategy"]["sources"]:
            source_msg = status_counts_msg(
                STATUS_COUNTS_INSTANCES,
                source["instanceSummary"]["statusCounts"],
                empty_msg_if_zero_total=True,
            )
            if len(source_msg) > 0:
                msg += f"{indent}Source: '{source['name']}': " + source_msg

    else:
        return

    print_log(msg, no_fill=True)


FIRST_OUTPUT_TO_FILE = True  # Determine whether to 'write' or 'append'


def _print_to_file(json_string: str, output_file: str, with_final_comma: bool = False):
    """
    Dump details output to a file.
    """
    global FIRST_OUTPUT_TO_FILE

    try:
        with open(output_file, "w" if FIRST_OUTPUT_TO_FILE else "a") as f:
            with redirect_stdout(f):
                if with_final_comma:
                    print(json_string, end=",\n", flush=True)
                else:
                    print(json_string, flush=True)
    except Exception as e:
        raise Exception(f"Cannot open output file for writing: {e}")

    FIRST_OUTPUT_TO_FILE = False
