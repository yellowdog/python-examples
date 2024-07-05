#!/usr/bin/env python3

"""
Command to list YellowDog entities.
"""

from dataclasses import asdict, fields
from json import loads as json_loads
from typing import Dict, List

from requests import get
from tabulate import tabulate
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    Allowance,
    AllowanceSearch,
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    ComputeRequirementTemplate,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    Instance,
    InstanceSearch,
    Keyring,
    KeyringSummary,
    MachineImageFamilySearch,
    MachineImageFamilySummary,
    NamespacePolicy,
    NamespacePolicySearch,
    NamespaceStorageConfiguration,
    Node,
    NodeSearch,
    NodeStatus,
    ObjectDetail,
    Task,
    TaskGroup,
    Worker,
    WorkerPool,
    WorkerPoolStatus,
    WorkerPoolSummary,
    WorkerStatus,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yd_commands.interactive import select
from yd_commands.object_utilities import (
    get_filtered_work_requirements,
    get_task_groups_from_wr_summary,
    get_tasks,
    list_matching_object_paths,
)
from yd_commands.printing import (
    indent,
    print_json,
    print_log,
    print_numbered_object_list,
    print_table_core,
    print_warning,
    print_yd_object,
    sorted_objects,
)
from yd_commands.utils import unpack_namespace_in_prefix
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    if not check_for_valid_option():
        raise Exception("Please choose a (single) listing type")

    # Always use interactive mode for selections
    ARGS_PARSER.interactive = True

    if ARGS_PARSER.object_paths:
        list_object_paths()
    elif ARGS_PARSER.work_requirements or ARGS_PARSER.task_groups or ARGS_PARSER.tasks:
        list_work_requirements()
    elif ARGS_PARSER.worker_pools or ARGS_PARSER.nodes or ARGS_PARSER.workers:
        list_worker_pools()
    elif ARGS_PARSER.compute_requirements or ARGS_PARSER.instances:
        list_compute_requirements()
    elif ARGS_PARSER.compute_templates:
        list_compute_templates()
    elif ARGS_PARSER.source_templates:
        list_source_templates()
    elif ARGS_PARSER.keyrings:
        list_keyrings()
    elif ARGS_PARSER.image_families:
        list_image_families()
    elif ARGS_PARSER.namespace_storage_configurations:
        list_namespaces()
    elif ARGS_PARSER.allowances:
        list_allowances()
    elif ARGS_PARSER.attribute_definitions:
        list_attribute_definitions()
    elif ARGS_PARSER.namespace_policies:
        list_namespace_policies()


def check_for_valid_option() -> bool:
    """
    Only one of the listing options must be selected.
    """
    if [
        ARGS_PARSER.allowances,
        ARGS_PARSER.attribute_definitions,
        ARGS_PARSER.compute_requirements,
        ARGS_PARSER.compute_templates,
        ARGS_PARSER.image_families,
        ARGS_PARSER.instances,
        ARGS_PARSER.keyrings,
        ARGS_PARSER.namespace_policies,
        ARGS_PARSER.namespace_storage_configurations,
        ARGS_PARSER.nodes,
        ARGS_PARSER.object_paths,
        ARGS_PARSER.source_templates,
        ARGS_PARSER.task_groups,
        ARGS_PARSER.tasks,
        ARGS_PARSER.work_requirements,
        ARGS_PARSER.worker_pools,
        ARGS_PARSER.workers,
    ].count(True) == 1:
        return True
    else:
        return False


def list_work_requirements():
    """
    List Work Requirements whenever --work-requirements, --task-groups or
    --tasks are selected.

    This function falls through from WRs to TGs to Tasks, depending on the
    options chosen.
    """
    print_log(
        f"Listing Work Requirements with  '{CONFIG_COMMON.namespace}' in namespace "
        f"and '{CONFIG_COMMON.name_tag}' in tag",
    )
    if ARGS_PARSER.active_only:
        print_log("Listing active Work Requirements only")

    exclude_filter = (
        [
            WorkRequirementStatus.COMPLETED,
            WorkRequirementStatus.CANCELLED,
            WorkRequirementStatus.FAILED,
        ]
        if ARGS_PARSER.active_only
        else []
    )
    work_requirement_summaries: List[WorkRequirementSummary] = (
        get_filtered_work_requirements(
            CLIENT,
            namespace=CONFIG_COMMON.namespace,
            tag=CONFIG_COMMON.name_tag,
            exclude_filter=exclude_filter,
        )
    )
    if len(work_requirement_summaries) == 0:
        print_log("No matching Work Requirements")
        return

    work_requirement_summaries = sorted_objects(work_requirement_summaries)
    if not (ARGS_PARSER.task_groups or ARGS_PARSER.tasks):
        if ARGS_PARSER.details:
            for wr_summary in select(CLIENT, work_requirement_summaries):
                print_yd_object(wr_summary)
        else:
            print_numbered_object_list(CLIENT, work_requirement_summaries)
    else:
        selected_work_summaries = select(
            CLIENT, work_requirement_summaries, single_result=True
        )
        for work_summary in selected_work_summaries:
            print_log(f"Work Requirement '{work_summary.name}'")
            list_task_groups(work_summary)


def list_task_groups(work_summary: WorkRequirementSummary):
    task_groups: List[TaskGroup] = get_task_groups_from_wr_summary(
        CLIENT, work_summary.id
    )
    task_groups = sorted_objects(task_groups)
    if not ARGS_PARSER.tasks:
        if ARGS_PARSER.details:
            for task_group in select(CLIENT, task_groups):
                print_yd_object(task_group)
        else:
            print_numbered_object_list(CLIENT, task_groups)
    else:
        task_groups = select(CLIENT, task_groups, single_result=True)
        for task_group in task_groups:
            list_tasks(task_group, work_summary)


def list_tasks(task_group: TaskGroup, work_summary: WorkRequirementSummary):
    tasks: List[Task] = get_tasks(CLIENT, work_summary.id, task_group.id)
    tasks = sorted_objects(tasks)
    if ARGS_PARSER.details:
        for task in select(CLIENT, tasks):
            print_yd_object(task)
    else:
        print_numbered_object_list(CLIENT, tasks)


def list_object_paths():
    namespace, tag = unpack_namespace_in_prefix(
        CONFIG_COMMON.namespace, CONFIG_COMMON.name_tag
    )
    print_log(
        f"Listing Object Paths in namespace '{namespace}' and "
        f"names (prefixes) starting with '{tag}'"
    )
    if ARGS_PARSER.all and not ARGS_PARSER.details:
        print_log("Listing all Objects")

    object_paths = list_matching_object_paths(CLIENT, namespace, tag, ARGS_PARSER.all)

    if len(object_paths) == 0:
        print_log("No matching Object Paths")
        return

    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(object_paths))
        return

    # Print object details for selected objects
    object_paths = select(CLIENT, object_paths, override_quiet=True)
    if len(object_paths) != 0:
        print_log(f"Showing Object details for {len(object_paths)} Object(s)")
    for object_path in object_paths:
        if object_path.prefix:
            print_log(f"Object Path '{object_path.name}' is a prefix not an object")
            continue
        object_detail: ObjectDetail = CLIENT.object_store_client.get_object_detail(
            namespace=namespace, name=object_path.name
        )
        # print_object_detail(object_detail)  # Retired for now
        print_yd_object(object_detail)


def list_worker_pools():
    print_log(f"Displaying Worker Pools with '{CONFIG_COMMON.namespace}' in namespace")

    worker_pool_summaries: List[WorkerPoolSummary] = (
        CLIENT.worker_pool_client.find_all_worker_pools()
    )

    excluded_states = (
        [WorkerPoolStatus.TERMINATED, WorkerPoolStatus.SHUTDOWN]
        if ARGS_PARSER.active_only
        else []
    )

    if ARGS_PARSER.active_only:
        print_log("Displaying active Worker Pools only")

    worker_pool_summaries = [
        wp_summary
        for wp_summary in worker_pool_summaries
        if wp_summary.status not in excluded_states
        and CONFIG_COMMON.namespace in wp_summary.namespace
    ]

    if len(worker_pool_summaries) == 0:
        print_log("No Worker Pools to display")
        return

    if ARGS_PARSER.nodes or ARGS_PARSER.workers:
        print_log(
            "Please select the Worker Pool(s) for which to list "
            f"{'Nodes' if ARGS_PARSER.nodes else 'Workers'}"
        )
        worker_pool_summaries = select(
            CLIENT,
            sorted_objects(worker_pool_summaries),
        )
        list_nodes(worker_pool_summaries)
        return

    if ARGS_PARSER.details:
        for worker_pool_summary in select(
            CLIENT, sorted_objects(worker_pool_summaries)
        ):
            worker_pool: WorkerPool = CLIENT.worker_pool_client.get_worker_pool_by_id(
                worker_pool_summary.id
            )
            print_yd_object(worker_pool)
    else:
        print_numbered_object_list(CLIENT, sorted_objects(worker_pool_summaries))


def list_compute_requirements():
    print_log(
        "Listing Compute Requirements with "
        f"namespace containing '{CONFIG_COMMON.namespace}' and "
        f" names containing '{CONFIG_COMMON.name_tag}'"
    )

    if ARGS_PARSER.active_only:
        print_log("Listing active Compute Requirements only")

    cr_search = ComputeRequirementSearch(
        namespace=CONFIG_COMMON.namespace,
    )
    search_client: SearchClient = CLIENT.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    filtered_compute_requirements: List[ComputeRequirement] = []
    excluded_states = (
        [ComputeRequirementStatus.TERMINATED, ComputeRequirementStatus.TERMINATING]
        if ARGS_PARSER.active_only
        else []
    )
    for compute_requirement in compute_requirements:
        compute_requirement.tag = (
            "" if compute_requirement.tag is None else compute_requirement.tag
        )
        if (
            CONFIG_COMMON.name_tag in compute_requirement.tag
            and CONFIG_COMMON.namespace in compute_requirement.namespace
            and compute_requirement.status not in excluded_states
        ):
            filtered_compute_requirements.append(compute_requirement)

    if len(filtered_compute_requirements) == 0:
        print_log("No matching Compute Requirements")
        return

    filtered_compute_requirements = sorted_objects(filtered_compute_requirements)

    if ARGS_PARSER.instances:
        for compute_requirement in select(
            CLIENT, filtered_compute_requirements, single_result=True
        ):
            list_instances(compute_requirement)
        return

    if ARGS_PARSER.details:
        for compute_requirement in select(CLIENT, filtered_compute_requirements):
            print_yd_object(compute_requirement)
    else:
        print_numbered_object_list(CLIENT, filtered_compute_requirements)


def list_instances(compute_requirement: ComputeRequirement):
    """
    List the instances within a Compute Requirement.
    """
    instance_search = InstanceSearch(computeRequirementId=compute_requirement.id)
    search_client: SearchClient = CLIENT.compute_client.get_instances(
        instance_search=instance_search
    )
    instances: List[Instance] = search_client.list_all()
    if len(instances) == 0:
        print_log("No instances to list")
        return

    if ARGS_PARSER.public_ips_only:
        print_log("Listing public IP addresses only:")
        for instance in instances:
            try:
                if instance.publicIpAddress is not None:
                    print(instance.publicIpAddress)
            except:
                pass
        return

    if ARGS_PARSER.details:
        for instance in select(CLIENT, instances):
            print_yd_object(instance)
    else:
        print_numbered_object_list(CLIENT, instances)


def list_nodes(worker_pool_summaries: List[WorkerPoolSummary]):
    """
    List the Nodes in a list of Worker Pools.
    """
    nodes_all: List[Node] = []
    for worker_pool_summary in worker_pool_summaries:
        nodes_search = NodeSearch(
            worker_pool_summary.id,
            statuses=[NodeStatus.RUNNING] if ARGS_PARSER.active_only else None,
        )
        search_client = CLIENT.worker_pool_client.get_nodes(search=nodes_search)
        nodes: List[Node] = search_client.list_all()
        for node in nodes:
            node.worker_pool_name = worker_pool_summary.name
        nodes_all += nodes

    if len(nodes_all) == 0:
        print_log("No Nodes to display")
        return

    if ARGS_PARSER.workers:
        list_workers(nodes_all)
        return

    if ARGS_PARSER.details:
        for node in select(CLIENT, nodes_all):
            delattr(node, "worker_pool_name")
            print_yd_object(node)
    else:
        print_numbered_object_list(CLIENT, nodes_all)


def list_workers(nodes: List[Node]):
    """
    Display a list of workers across all nodes in a worker pool.
    """
    workers_all: List[Worker] = []
    for node in nodes:
        for worker in node.workers:
            if ARGS_PARSER.active_only:
                if worker.status not in [
                    WorkerStatus.SLEEPING,
                    WorkerStatus.DOING_TASK,
                    WorkerStatus.FOUND,
                ]:
                    continue
            # Add extra info to the Worker object
            worker.worker_tag = node.details.workerTag
            worker.task_types = node.details.supportedTaskTypes
            worker.worker_pool_name = node.worker_pool_name
            workers_all.append(worker)

    if len(workers_all) == 0:
        print_log("No Workers to display")
        return

    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, workers_all)
        return

    for worker in select(CLIENT, workers_all):
        delattr(worker, "worker_tag")
        delattr(worker, "task_types")
        delattr(worker, "worker_pool_name")
        print_yd_object(worker)


def list_compute_templates():
    """
    Print the list of Compute Requirement Templates, filtered on Namespace
    and Name. Set these both to empty strings to generate an unfiltered list.
    """
    cr_templates: List[ComputeRequirementTemplateSummary] = (
        CLIENT.compute_client.find_all_compute_requirement_templates()
    )
    print_log(
        "Listing Compute Requirement Templates with namespaces including"
        f" '{CONFIG_COMMON.namespace}' and names including"
        f" '{CONFIG_COMMON.name_tag}'"
    )
    cr_templates = [
        crt
        for crt in cr_templates
        if (CONFIG_COMMON.namespace in ("" if crt.namespace is None else crt.namespace))
        and CONFIG_COMMON.name_tag in crt.name
    ]
    if len(cr_templates) == 0:
        print_log("No matching Compute Requirement Templates found")
        return
    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(cr_templates))
        return

    cr_templates = select(CLIENT, cr_templates)
    for cr_template in cr_templates:
        cr_template_detail: ComputeRequirementTemplate = (
            CLIENT.compute_client.get_compute_requirement_template(cr_template.id)
        )
        print_yd_object(cr_template_detail)


def list_source_templates():
    """
    Print the list of Compute Source Templates, filtered on Namespace
    and Name. Set these both to empty strings to generate an unfiltered list.
    """
    cs_templates: List[ComputeSourceTemplateSummary] = (
        CLIENT.compute_client.find_all_compute_source_templates()
    )
    print_log(
        "Listing Compute Source Templates with namespaces including"
        f" '{CONFIG_COMMON.namespace}' and names including"
        f" '{CONFIG_COMMON.name_tag}'"
    )
    cs_templates = [
        cst
        for cst in cs_templates
        if (CONFIG_COMMON.namespace in ("" if cst.namespace is None else cst.namespace))
        and CONFIG_COMMON.name_tag in cst.name
    ]
    if len(cs_templates) == 0:
        print_log("No matching Compute Source Templates found")
        return
    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(cs_templates))
        return

    cs_templates = select(CLIENT, sorted_objects(cs_templates))
    for cs_template in cs_templates:
        cs_template_detail: ComputeSourceTemplate = (
            CLIENT.compute_client.get_compute_source_template(cs_template.id)
        )
        print_yd_object(cs_template_detail)


def list_keyrings():
    """
    Print the list of Keyrings
    """
    keyrings: List[KeyringSummary] = CLIENT.keyring_client.find_all_keyrings()
    if len(keyrings) == 0:
        print_log("No Keyrings found")
        return
    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(keyrings))
        return

    keyrings = select(CLIENT, keyrings)
    for keyring_summary in keyrings:
        print_yd_object(get_keyring(keyring_summary.name))


def get_keyring(name: str) -> Keyring:
    """
    Temporary function in place of a missing KeyringClient SDK call.
    """
    response = get(
        url=f"{CONFIG_COMMON.url}/keyrings/{name}",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
    )
    if response.status_code == 200:
        return Keyring(**response.json())
    else:
        raise Exception(f"Failed to get Keyring '{name}' ({response.text})")


def list_image_families():
    """
    List the Machine Image Families.
    """
    image_search = MachineImageFamilySearch(includePublic=True)
    search_client: SearchClient = CLIENT.images_client.get_image_families(image_search)
    image_family_summaries: List[MachineImageFamilySummary] = search_client.list_all()
    if len(image_family_summaries) == 0:
        print_log("No Machine Image Families found")
        return

    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, sorted_objects(image_family_summaries))
        return

    for image_family_summary in select(CLIENT, sorted_objects(image_family_summaries)):
        image_family = CLIENT.images_client.get_image_family_by_id(
            image_family_summary.id
        )
        print_yd_object(image_family)


def list_namespaces():
    """
    List Storage Namespaces. For now, prints a table directly rather than
    calling the printing module, due to it being a bit fiddly.
    """

    # Get the configured namespaces
    namespaces_config: List[NamespaceStorageConfiguration] = (
        CLIENT.object_store_client.get_namespace_storage_configurations()
    )
    namespace_config_names = [namespace.namespace for namespace in namespaces_config]

    # Create dicts for the default object store namespaces, and give them
    # a type name. Exclude configured namespaces.
    namespaces_default = [
        {"namespace": namespace, "type": "Default Storage Configuration"}
        for namespace in sorted(CLIENT.object_store_client.get_namespaces())
        if namespace not in namespace_config_names
    ]

    # Convert NamespaceStorageConfiguration objects to dicts, and simplify
    # the type names
    namespace_list: List[Dict] = [asdict(x) for x in namespaces_config]
    for namespace in namespace_list:
        namespace["type"] = namespace["type"].split(".")[-1]

    # Combine configured and default Namespaces
    namespace_list += namespaces_default

    if len(namespace_list) == 0:
        print_log("No Namespaces found")
        return
    print_log("Displaying all Object Store Namespaces")

    # Accumulate all available headings; keep "namespace", "type"
    # at the start
    all_fields = set()
    for config in namespaces_config:
        for field in fields(config):
            if not (field.name == "namespace" or field.name == "type"):
                all_fields.add(field.name)
    all_fields = sorted(list(all_fields))
    all_fields.insert(0, "type")
    all_fields.insert(0, "namespace")

    # Assemble and print the table
    headings = [field.capitalize() for field in all_fields]
    headings.insert(0, "#")
    rows = sorted(
        [
            [index + 1] + [namespace.get(field, "") for field in all_fields]
            for index, namespace in enumerate(namespace_list)
        ]
    )
    print(flush=True)
    print_table_core(
        indent(tabulate(rows, headings, tablefmt="simple_outline")),
    )
    print(flush=True)

    if ARGS_PARSER.details:  # Print the details for non-default only
        for namespace in select(CLIENT, namespaces_config, showing_all=True):
            print_yd_object(namespace)


def list_allowances():
    """
    List allowances.
    """
    allowances_search = AllowanceSearch()
    search_client: SearchClient = CLIENT.allowances_client.get_allowances(
        allowances_search
    )
    allowances: List[Allowance] = search_client.list_all()
    if len(allowances) == 0:
        print_log("No Allowances to display")
        return

    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, allowances)
        return

    for allowance in select(CLIENT, allowances):
        print_yd_object(allowance)


def list_attribute_definitions():
    """
    List user compute attribute definitions using the API.
    """
    response = get(
        url=f"{CONFIG_COMMON.url}/compute/attributes/user",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
    )

    if response.status_code != 200:
        raise Exception(
            "Unable to list user attribute definitions: HTTP "
            f"{response.status_code} ({response.text})"
        )

    attribute_definition_list = json_loads(response.text)
    attribute_definition_list.sort(key=lambda x: x["name"])

    if not ARGS_PARSER.details:
        print_numbered_object_list(
            CLIENT, attribute_definition_list, object_type_name="Attribute Definition"
        )
        return

    for selected_attribute_definition in select(
        CLIENT,
        attribute_definition_list,
        object_type_name="Attribute Definition",
        sort_objects=False,
    ):
        print_json(selected_attribute_definition)


def list_namespace_policies():
    """
    List namespace policies.
    """

    np_search = NamespacePolicySearch()
    search_client: SearchClient = CLIENT.namespaces_client.get_namespace_policies(
        np_search
    )
    namespace_policies: List[NamespacePolicy] = search_client.list_all()
    if len(namespace_policies) == 0:
        print_log("No Namespace Policies to display")
        return

    if not ARGS_PARSER.details:
        print_numbered_object_list(CLIENT, namespace_policies)
        return

    for selected_namespace_policy in select(
        CLIENT, namespace_policies, object_type_name="Namespace Policy"
    ):
        if selected_namespace_policy.autoscalingMaxNodes is None:
            print_yd_object(selected_namespace_policy)
        else:
            details = get_autoscaling_capacity(selected_namespace_policy.namespace)
            details["autoscalingMaxNodes"] = (
                selected_namespace_policy.autoscalingMaxNodes
            )
            print_json(details)


def get_autoscaling_capacity(namespace: str) -> Dict:
    """
    Get the current autoscaling values for a namespace.
    """
    response = get(
        url=f"{CONFIG_COMMON.url}/workerPools/namespaces/{namespace}/autoscalingCapacity",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
    )
    if response.status_code == 200:
        return response.json()
    else:
        print_warning(
            f"Failed to get autoscaling details for namespace '{namespace}' ({response.text})"
        )
        return {"namespace": namespace}


# Entry point
if __name__ == "__main__":
    main()
