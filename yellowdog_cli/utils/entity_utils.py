"""
Various utility functions for finding objects, etc.
"""

from functools import lru_cache
from typing import List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    AllowanceSearch,
    ComputeRequirement,
    ComputeRequirementSearch,
    ComputeRequirementStatus,
    ComputeRequirementTemplate,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    MachineImageFamily,
    MachineImageFamilySearch,
    MachineImageFamilySummary,
    ObjectPath,
    ObjectPathsRequest,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    TaskSearch,
    WorkerPool,
    WorkerPoolSummary,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.printing import print_log, print_warning
from yellowdog_cli.utils.settings import NAMESPACE_PREFIX_SEPARATOR
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


@lru_cache
def get_task_groups_from_wr_summary(
    client: PlatformClient, wr_summary_id: str
) -> List[TaskGroup]:
    """
    Get the list of the Work Requirement's Task Groups.
    Cache results to avoid repeatedly hitting the API for the same thing.
    """
    work_requirement = client.work_client.get_work_requirement_by_id(wr_summary_id)
    return work_requirement.taskGroups


def get_task_group_name(
    client: PlatformClient, wr_summary: WorkRequirementSummary, task: Task
) -> str:
    """
    Function to find the Task Group Name for a given Task
    within a Work Requirement.
    """
    for task_group in get_task_groups_from_wr_summary(client, wr_summary.id):
        if task.taskGroupId == task_group.id:
            return task_group.name
    return ""  # Shouldn't get here


def get_filtered_work_requirements(
    client: PlatformClient,
    namespace: str,
    tag: str,
    include_filter: Optional[List[WorkRequirementStatus]] = None,
    exclude_filter: Optional[List[WorkRequirementStatus]] = None,
) -> List[WorkRequirementSummary]:
    """
    Get a list of Work Requirements filtered by namespace, tag
    and status. Supply either include_filter OR exclude_filter.
    """
    filtered_work_summaries: List[WorkRequirementSummary] = []

    work_requirement_summaries: List[WorkRequirementSummary] = (
        client.work_client.find_all_work_requirements()
    )

    for work_summary in work_requirement_summaries:
        work_summary.tag = "" if work_summary.tag is None else work_summary.tag
        work_summary.namespace = (
            "" if work_summary.namespace is None else work_summary.namespace
        )
        if namespace in work_summary.namespace and tag in work_summary.tag:
            if include_filter is not None:
                if work_summary.status in include_filter:
                    filtered_work_summaries.append(work_summary)
                    continue
            if exclude_filter is not None:
                if work_summary.status not in exclude_filter:
                    filtered_work_summaries.append(work_summary)
                    continue

    return filtered_work_summaries


@lru_cache
def get_worker_pool_by_id(client: PlatformClient, worker_pool_id: str) -> WorkerPool:
    """
    Pass-through function to cache results.
    """
    return client.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id=worker_pool_id
    )


def get_worker_pool_id_by_name(
    client: PlatformClient, worker_pool_name: str
) -> Optional[str]:
    """
    Find a Worker Pool ID by its name.
    """
    namespace, name = split_namespace_and_name(worker_pool_name)
    if namespace is not None:  # Direct lookup for fully-qualified names
        try:
            worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_name(
                namespace, name
            )
            return worker_pool.id
        except:
            return

    return _find_id_by_name(worker_pool_name, client, get_all_worker_pools)


def get_compute_requirement_id_by_name(
    client: PlatformClient,
    compute_requirement_name: str,
    statuses: List[ComputeRequirementStatus],
) -> Optional[str]:
    """
    Find a Compute Requirement ID by its name.
    Restrict search by status.
    """
    cr_search = ComputeRequirementSearch(statuses=statuses)
    search_client: SearchClient = client.compute_client.get_compute_requirements(
        cr_search
    )
    compute_requirements: List[ComputeRequirement] = search_client.list_all()

    for compute_requirement in compute_requirements:
        if compute_requirement.name == compute_requirement_name:
            return compute_requirement.id


def get_work_requirement_summary_by_name_or_id(
    client: PlatformClient, work_requirement_name_or_id: str
) -> Optional[WorkRequirementSummary]:
    """
    Get a Work Requirement Summary by its name or ID.
    """
    work_requirement_summaries: List[WorkRequirementSummary] = (
        client.work_client.find_all_work_requirements()
    )
    for work_requirement_summary in work_requirement_summaries:
        if (
            work_requirement_summary.name == work_requirement_name_or_id
            or work_requirement_summary.id == work_requirement_name_or_id
        ):
            return work_requirement_summary


def _find_id_by_name(
    name: str, client: PlatformClient, find_function: callable
) -> Optional[str]:
    """
    Generic function to find the ID of an entity by namespace and name.
    """
    namespace, name = split_namespace_and_name(name)

    entities = find_function(client)

    exact_matching_entities = []
    inexact_matching_entities = []

    # Exact match: namespace and name (including matching namespace = None)
    # Inexact match: if name matches but namespace is None
    for entity in entities:
        if entity.name == name:
            if entity.namespace == namespace:
                exact_matching_entities.append(entity)
            elif namespace is None:
                inexact_matching_entities.append(entity)

    if len(exact_matching_entities) == 0 and len(inexact_matching_entities) == 0:
        return

    if len(exact_matching_entities) == 1:
        return exact_matching_entities[0].id

    if len(inexact_matching_entities) == 1:
        return inexact_matching_entities[0].id

    matches = [
        f"{entity.namespace}/{entity.name} ({entity.id})"
        for entity in exact_matching_entities + inexact_matching_entities
    ]
    raise Exception(
        f"'{name}' has multiple matches: {matches}. "
        f"Please specify the required namespace."
    )


def find_compute_source_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find a Compute Source Template id by name.
    Compute Source Template names are unique within a namespace.
    """
    return _find_id_by_name(name, client, get_all_compute_source_templates)


@lru_cache
def get_all_compute_source_templates(
    client: PlatformClient,
) -> List[ComputeSourceTemplateSummary]:
    """
    Cache the list of Sources.
    """
    return client.compute_client.find_all_compute_source_templates()


def clear_compute_source_template_cache():
    """
    Clear the cache of Compute Source Templates.
    """
    get_all_compute_source_templates.cache_clear()


def find_compute_requirement_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find the Compute Requirement Template ID that matches the
    provided name. Names are unique within a namespace.
    """
    return _find_id_by_name(name, client, get_all_compute_requirement_templates)


@lru_cache
def get_all_compute_requirement_templates(
    client: PlatformClient,
) -> List[ComputeRequirementTemplateSummary]:
    """
    Cache the list of Compute Requirement Templates.
    """
    return client.compute_client.find_all_compute_requirement_templates()


def clear_compute_requirement_template_cache():
    """
    Clear the cache of Compute Requirement Templates.
    """
    get_all_compute_requirement_templates.cache_clear()


def get_compute_requirement_id_by_worker_pool_id(
    client: PlatformClient, worker_pool_id: str
) -> Optional[str]:
    """
    Get a Compute Requirement ID from a Provisioned Worker Pool ID.
    """
    worker_pool: WorkerPool = client.worker_pool_client.get_worker_pool_by_id(
        worker_pool_id
    )
    if isinstance(worker_pool, ProvisionedWorkerPool):
        return worker_pool.computeRequirementId


def get_all_worker_pools(client: PlatformClient) -> List[WorkerPoolSummary]:
    """
    Return all Worker Pool summaries.
    """
    return client.worker_pool_client.find_all_worker_pools()


@lru_cache
def find_image_family_reference_by_name(
    client: PlatformClient, image_family_name
) -> Optional[str]:
    """
    Resolve image family references. Complicated logic.
    Fully qualified name is used for non-ambiguous PRIVATE image families.
    """

    original_image_family_name = image_family_name

    # Remove leading 'yd/' prefix if necessary
    image_family_name = (
        image_family_name[3:]
        if image_family_name.startswith("yd/")
        else image_family_name
    )
    namespace, name = split_namespace_and_name(image_family_name)

    if_search = MachineImageFamilySearch(
        familyName=name, namespace=namespace, includePublic=True
    )
    search_client: SearchClient = client.images_client.get_image_families(if_search)
    image_families: List[MachineImageFamilySummary] = search_client.list_all()

    # Partial names will match, so filter for exact matches only
    image_families = [
        img_family for img_family in image_families if img_family.name == name
    ]

    # No matches
    if len(image_families) == 0:
        return

    # It's possible to have both a PRIVATE and a PUBLIC match for the same
    # namespace/image_family_name. This is a corner case, but ...
    if len(image_families) == 2:
        image_families_public = [
            img_family
            for img_family in image_families
            if img_family.access.name == "PUBLIC"
        ]
        image_families_private = [
            img_family
            for img_family in image_families
            if img_family.access.name == "PRIVATE"
        ]
        if len(image_families_public) == 1 and len(image_families_private) == 1:
            # Favour the PRIVATE image
            print_warning(
                f"Image Family '{name}' has both PUBLIC and PRIVATE "
                "variants; using the PRIVATE image family: "
                f"{image_families_private[0].namespace}/{image_families_private[0].name} "
                f"({image_families_private[0].id})"
            )
            image_families = image_families_private

    # Single match
    if len(image_families) == 1:
        substituted_image_family_name = (
            f"yd/{image_families[0].namespace}/{image_families[0].name}"
        )

        # If this is a PRIVATE image family, we can retain the fully-qualified
        # image family name instead of substituting the ID
        if image_families[0].access.name == "PRIVATE":
            if original_image_family_name != substituted_image_family_name:
                print_log(
                    f"Substituting Image Family name '{original_image_family_name}' "
                    f"with fully qualified name '{substituted_image_family_name}' "
                    f"({image_families[0].id})"
                )
            return substituted_image_family_name

        # If PUBLIC, we need to replace with the YDID
        else:
            mid_msg = (
                ""
                if original_image_family_name == substituted_image_family_name
                else f"('{substituted_image_family_name}') "
            )
            print_log(
                f"Substituting Image Family name '{original_image_family_name}' {mid_msg}"
                f"with ID {image_families[0].id}"
            )
            return image_families[0].id

    # Multiple matches
    matches = [
        f"{img_fam.namespace}/{img_fam.name} [{img_fam.access.name}] ({img_fam.id})"
        for img_fam in image_families
    ]

    raise Exception(
        f"Ambiguous Image Family name '{name}': "
        f"{matches}. "
        "Please specify a namespace. Note: PRIVATE image family is selected "
        "over PUBLIC if namespace/name are identical."
    )


def clear_image_family_search_cache():
    """
    Clear the cache of Image Family name searches.
    """
    find_image_family_reference_by_name.cache_clear()


def remove_allowances_matching_description(
    client: PlatformClient, description: str
) -> int:
    """
    Remove Allowances that match on the description property.
    Return the number of allowances removed.
    """
    allowances = client.allowances_client.get_allowances(
        AllowanceSearch(description=description)
    ).list_all()

    if len(allowances) > 1:
        print_log(f"Multiple Allowances match the description '{description}'")
        print_log("Please select which Allowance(s) to remove")
        allowances = select(
            client=client,
            objects=allowances,
            object_type_name="Allowance",
            single_result=False,
            force_interactive=True,
        )

    for allowance in allowances:
        if confirmed(f"Remove Allowance with YellowDog ID {allowance.id}?"):
            client.allowances_client.delete_allowance_by_id(allowance.id)
            print_log(f"Removed Allowance with YellowDog ID {allowance.id}")

    return len(allowances)


def list_matching_object_paths(
    client: PlatformClient, namespace: str, prefix: str, flat: bool
) -> List[ObjectPath]:
    """
    List object paths matching the namespace and starting with the prefix.
    """
    object_paths: List[ObjectPath] = (
        client.object_store_client.get_namespace_object_paths(
            ObjectPathsRequest(namespace=namespace, prefix=prefix, flat=flat)
        )
    )

    if object_paths is None:
        return []

    # Check the prefix actually matches!
    return [
        object_path
        for object_path in object_paths
        if object_path.name.startswith(prefix)
    ]


@lru_cache
def get_tasks(client: PlatformClient, wr_id: str, task_group_id: str) -> List[Task]:
    """
    Return all the tasks in a task group, with caching.
    """
    task_search = TaskSearch(
        workRequirementId=wr_id,
        taskGroupId=task_group_id,
    )
    tasks: List[Task] = client.work_client.find_tasks(task_search)
    return tasks


def get_non_exact_namespace_matches(
    client: PlatformClient, namespace_to_match: str
) -> List[str]:
    """
    Find namespaces which contain 'namespace_to_match'.
    """
    all_namespaces = client.object_store_client.get_namespaces() + [
        nssc.namespace
        for nssc in client.object_store_client.get_namespace_storage_configurations()
    ]
    matching_namespaces = sorted(
        list(
            {  # Note: use set because duplicate namespaces can be returned
                ns for ns in all_namespaces if namespace_to_match in ns
            }
        )
    )
    return matching_namespaces


def split_namespace_and_name(reference: str) -> (Optional[str], str):
    """
    Split a name into an (optional) namespace and a name.
    """
    parts = reference.strip().split(NAMESPACE_PREFIX_SEPARATOR)
    if len(parts) == 1:
        return None, reference
    if len(parts) == 2:
        if parts[0] == "":  # Handle the case of a leading slash
            return None, parts[1]
        else:
            return parts[0], parts[1]

    raise Exception(f"Malformed name '{reference}'")


def substitute_ids_for_names_in_crt(
    client: PlatformClient, crt: ComputeRequirementTemplate
) -> ComputeRequirementTemplate:
    """
    Substitute CST and Image Family IDs for namespace/name,
    if option is selected.
    """
    if not ARGS_PARSER.substitute_ids:
        return crt

    # Image family
    try:
        crt.imagesId = _get_image_family_name_from_id(client, crt.imagesId)
    except:
        pass

    # Source templates
    try:
        for source in crt.sources:
            source.sourceTemplateId = _get_source_template_name_from_id(
                client, source.sourceTemplateId
            )
            source.imageId = _get_image_family_name_from_id(client, source.imageId)
    except:
        pass

    return crt


@lru_cache
def _get_source_template_name_from_id(
    client: PlatformClient, cst_id: Optional[str]
) -> Optional[str]:
    """
    Obtain the namespace/name of a source template.
    Otherwise, return the original value.
    """
    if get_ydid_type(cst_id) != YDIDType.COMPUTE_SOURCE_TEMPLATE:
        return cst_id
    try:
        cst: ComputeSourceTemplate = client.compute_client.get_compute_source_template(
            cst_id
        )
        return f"{cst.namespace}/{cst.source.name}"
    except:
        return cst_id


@lru_cache
def _get_image_family_name_from_id(
    client: PlatformClient, image_family_id: Optional[str]
) -> Optional[str]:
    """
    Obtain the namespace/name of an image family.
    Otherwise, return the original value.
    """
    if get_ydid_type(image_family_id) != YDIDType.IMAGE_FAMILY:
        return image_family_id
    try:
        image_family: MachineImageFamily = client.images_client.get_image_family_by_id(
            image_family_id
        )
        return f"yd/{image_family.namespace}/{image_family.name}"
    except:
        return image_family_id
