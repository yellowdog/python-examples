"""
Various utility functions for finding objects, etc.
"""

from functools import lru_cache
from typing import Callable, List, Optional, Tuple, Union

from yellowdog_client import PlatformClient
from yellowdog_client.common import SearchClient
from yellowdog_client.model import (
    AccountAllowance,
    AllowanceSearch,
    Application,
    ApplicationSearch,
    ComputeRequirementStatus,
    ComputeRequirementSummary,
    ComputeRequirementSummarySearch,
    ComputeRequirementTemplate,
    ComputeRequirementTemplateSearch,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSearch,
    ComputeSourceTemplateSummary,
    ExternalUser,
    GroupSearch,
    GroupSummary,
    ImageAccess,
    InternalUser,
    MachineImageFamily,
    MachineImageFamilySearch,
    MachineImageFamilySummary,
    MachineImageGroup,
    NamespaceSearch,
    ObjectPath,
    ObjectPathsRequest,
    ProvisionedWorkerPool,
    RequirementsAllowance,
    RoleSearch,
    RoleSummary,
    SourceAllowance,
    SourcesAllowance,
    Task,
    TaskGroup,
    TaskSearch,
    User,
    UserSearch,
    WorkerPool,
    WorkerPoolSearch,
    WorkerPoolSummary,
    WorkRequirementSearch,
    WorkRequirementStatus,
    WorkRequirementSummary,
)

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.interactive import confirmed, select
from yellowdog_cli.utils.printing import print_log
from yellowdog_cli.utils.settings import NAMESPACE_PREFIX_SEPARATOR
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


@lru_cache
def get_task_groups_from_wr_by_id(
    client: PlatformClient, wr_id: str
) -> List[TaskGroup]:
    """
    Get the list of the Work Requirement's Task Groups.
    Cache results to avoid repeatedly hitting the API for the same thing.
    """
    work_requirement = client.work_client.get_work_requirement_by_id(wr_id)
    return work_requirement.taskGroups


def get_task_group_name(
    client: PlatformClient, wr_summary: WorkRequirementSummary, task: Task
) -> str:
    """
    Function to find the Task Group Name for a given Task
    within a Work Requirement.
    """
    for task_group in get_task_groups_from_wr_by_id(client, wr_summary.id):
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
    if include_filter is None:
        wr_search = WorkRequirementSearch(namespaces=[namespace], tag=tag)
    else:
        wr_search = WorkRequirementSearch(
            namespaces=[namespace], tag=tag, statuses=include_filter
        )

    wr_search_client = client.work_client.get_work_requirements(wr_search)
    work_requirement_summaries: List[WorkRequirementSummary] = (
        wr_search_client.list_all()
    )

    if include_filter is not None or exclude_filter is None:
        return work_requirement_summaries

    return [
        work_summary
        for work_summary in work_requirement_summaries
        if work_summary.status not in exclude_filter
    ]


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

    return _find_id_by_name(worker_pool_name, client, get_worker_pools)


def get_compute_requirement_id_by_name(
    client: PlatformClient,
    compute_requirement_name: str,
    statuses: List[ComputeRequirementStatus],
) -> Optional[str]:
    """
    Find a Compute Requirement ID by its name.
    Restrict search by status.
    """
    crs_search = ComputeRequirementSummarySearch(
        name=compute_requirement_name, statuses=statuses
    )
    search_client: SearchClient = (
        client.compute_client.get_compute_requirement_summaries(crs_search)
    )
    try:
        return search_client.list_all()[0].id
    except IndexError:
        return None


def get_work_requirement_summary_by_name_or_id(
    client: PlatformClient,
    work_requirement_name_or_id: str,
    namespace: str = None,
) -> Optional[WorkRequirementSummary]:
    """
    Get a Work Requirement Summary by its name or ID.
    Scoped by namespace.
    """
    work_requirement_summaries = get_work_requirement_summaries(
        client, namespace=namespace
    )

    for work_requirement_summary in work_requirement_summaries:
        if (
            work_requirement_summary.name == work_requirement_name_or_id
            or work_requirement_summary.id == work_requirement_name_or_id
        ):
            return work_requirement_summary

    return None


def _find_id_by_name(
    name: str, client: PlatformClient, find_function: Callable
) -> Optional[str]:
    """
    Generic function to find the ID of an entity by namespace and name.
    """
    namespace, name = split_namespace_and_name(name)

    entities = find_function(client, namespace)

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


@lru_cache
def find_compute_source_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find a Compute Source Template id by name.
    Compute Source Template names are unique within a namespace.
    """
    template_id = _find_id_by_name(name, client, get_compute_source_templates)
    if template_id is not None:
        print_log(
            f"Replaced Compute Source Template name '{name}' with ID {template_id}"
        )
    return template_id


@lru_cache
def get_compute_source_templates(
    client: PlatformClient,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
) -> List[ComputeSourceTemplateSummary]:
    """
    Cache the list of Compute Source Templates, scoped by namespace and name.
    """
    cst_search = ComputeSourceTemplateSearch(
        name=name, namespaces=None if namespace in [None, ""] else [namespace]
    )
    cst_search_client: SearchClient = (
        client.compute_client.get_compute_source_templates(cst_search)
    )
    return cst_search_client.list_all()


def get_work_requirement_summaries(
    client: PlatformClient,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
) -> List[WorkRequirementSummary]:
    """
    Get the list of Work Requirement summaries, scoped by namespace and name.
    """
    wr_search = WorkRequirementSearch(
        name=name, namespaces=None if namespace in [None, ""] else [namespace]
    )
    wr_search_client: SearchClient = client.work_client.get_work_requirements(wr_search)
    return wr_search_client.list_all()


def clear_compute_source_template_cache():
    """
    Clear the cache of Compute Source Templates.
    Clear name -> CST lookups.
    """
    get_compute_source_templates.cache_clear()
    find_compute_source_template_id_by_name.cache_clear()


def find_compute_requirement_template_id_by_name(
    client: PlatformClient, name: str
) -> Optional[str]:
    """
    Find the Compute Requirement Template ID that matches the
    provided name. Names are unique within a namespace.
    """
    return _find_id_by_name(name, client, get_compute_requirement_templates)


@lru_cache
def get_compute_requirement_templates(
    client: PlatformClient,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
) -> List[ComputeRequirementTemplateSummary]:
    """
    Cache the list of Compute Requirement Templates, scoped by namespace
    and name.
    """
    crt_search = ComputeRequirementTemplateSearch(
        name=name, namespaces=None if namespace in [None, ""] else [namespace]
    )
    crt_search_client: SearchClient = (
        client.compute_client.get_compute_requirement_templates(crt_search)
    )
    return crt_search_client.list_all()


def clear_compute_requirement_template_cache():
    """
    Clear the cache of Compute Requirement Templates.
    """
    get_compute_requirement_templates.cache_clear()


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
    return None


def get_worker_pools(
    client: PlatformClient,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
) -> List[WorkerPoolSummary]:
    """
    Return all Worker Pool summaries for a namespace, name.
    """
    wp_search = WorkerPoolSearch(
        name=name, namespaces=None if namespace in [None, ""] else [namespace]
    )
    wp_search_client: SearchClient = client.worker_pool_client.get_worker_pools(
        wp_search
    )
    return wp_search_client.list_all()


@lru_cache
def find_image_name_or_id(
    client: PlatformClient,
    image_name_or_id: Optional[str],
    always_return_id: bool = True,
    report_substitutions: bool = True,
) -> Optional[str]:
    """
    Attempts to resolve to a well-formed YD image name or ID, if it can.

    Argument 'image_name_or_id' can take one of the following forms:
     - Any image family or group YDID (returned unchanged)
     - Strings prefixed or not prefixed with 'yd/' (will be added if required)
     - Strings post-fixed or not post-fixed with '/latest' (will be removed)
     - Any standalone image-family-name
     - Any namespace/image-family-name combination
     - Any image-family-name/image-group-name combination
     - Any namespace/image-family-name/image-group-name combination

     The call will attempt to resolve the image into its fully qualified
     name if 'always_return_id' is false:
      - yd/namespace/image-family-name or
      - yd/namespace/image-family-name/image-group-name

    If the resolved image is PUBLIC or 'always_return_id' is True,
    the relevant YDID will always be returned; this is enforced for
    PUBLIC images.

    Finally, if nothing matches, the original ID is returned. This is
    likely to be a provider specific string.
    """
    if image_name_or_id is None:
        return None

    # Already a matching YDID?
    if get_ydid_type(image_name_or_id) in [
        YDIDType.IMAGE_FAMILY,
        YDIDType.IMAGE_GROUP,
        YDIDType.IMAGE,
    ]:
        return image_name_or_id

    original_image_name_or_id = image_name_or_id

    # Remove a leading 'yd/' prefix; will be reinstated later if required
    image_name_or_id = (
        image_name_or_id[3:] if image_name_or_id.startswith("yd/") else image_name_or_id
    )

    # Remove "/latest"; this is redundant/implied for YD image groups
    image_name_or_id = (
        image_name_or_id[:-7]
        if image_name_or_id.endswith("/latest")
        else image_name_or_id
    )

    def _replaced(return_val: str, is_ydid: bool = False):
        """
        Helper function to report the replacement.
        """
        if report_substitutions and return_val != original_image_name_or_id:
            msg = f"{return_val}" if is_ydid else f"'{return_val}'"
            print_log(f"Replaced Images ID '{original_image_name_or_id}' with {msg}")
        return return_val

    split_name = image_name_or_id.split("/")
    image_family_summaries = get_image_family_summaries(client)  # All namespaces

    # Search for image name (only) matches
    if len(split_name) == 1:
        matching_image_families = [
            ifs for ifs in image_family_summaries if ifs.name == split_name[0]
        ]
        if len(matching_image_families) > 1:
            namespaces = [ifs.namespace for ifs in matching_image_families]
            raise Exception(
                f"Ambiguous Images ID '{original_image_name_or_id}': please "
                f"specify a namespace from: {', '.join(namespaces)}"
            )
        elif len(matching_image_families) == 1:
            if (
                matching_image_families[0].access == ImageAccess.PUBLIC
                or always_return_id
            ):
                return _replaced(matching_image_families[0].id, True)
            else:
                return _replaced(
                    f"yd/{matching_image_families[0].namespace}/"
                    f"{matching_image_families[0].name}"
                )

    # Search for namespace/family_name matches, *or* family_name/group_name matches
    if len(split_name) == 2:
        # namespace/family-name match

        # This will be tidied up when the Application can
        # query its properties
        if len(image_family_summaries) == 0:  # Global search didn't work
            image_family_summaries = get_image_family_summaries(client, split_name[0])

        matching_image_families = [
            ifs
            for ifs in image_family_summaries
            if ifs.namespace == split_name[0] and ifs.name == split_name[1]
        ]
        if len(matching_image_families) == 1:
            if (
                matching_image_families[0].access == ImageAccess.PUBLIC
                or always_return_id
            ):
                return _replaced(matching_image_families[0].id, True)
            return _replaced(
                f"yd/{matching_image_families[0].namespace}/"
                f"{matching_image_families[0].name}"
            )

        # family-name/group-name match
        matching_image_families = [
            ifs for ifs in image_family_summaries if ifs.name == split_name[0]
        ]
        if_group_matches: List[Tuple[MachineImageFamilySummary, MachineImageGroup]] = []
        for ifs in matching_image_families:
            for if_group in get_image_family_groups(client, ifs.id):
                if if_group.name == split_name[1]:
                    if_group_matches.append((ifs, if_group))
                    break
        if len(if_group_matches) == 1:
            if if_group_matches[0][0].access == ImageAccess.PUBLIC or always_return_id:
                return _replaced(if_group_matches[0][1].id, True)
            else:
                return _replaced(
                    f"yd/{if_group_matches[0][0].namespace}/"
                    f"{if_group_matches[0][0].name}/"
                    f"{if_group_matches[0][1].name}"
                )
        if len(if_group_matches) > 1:
            namespaces = [match[0].namespace for match in if_group_matches]
            raise Exception(
                f"Ambiguous image-family/image-group '{original_image_name_or_id}': "
                f"please specify a namespace from: {', '.join(namespaces)}"
            )

    # Search for names of form 'namespace/image-family-name/image-group-name'
    # (the platform prevents duplicates)
    if len(split_name) == 3:

        # This will be tidied up when the Application can
        # query its properties
        if len(image_family_summaries) == 0:  # Global search didn't work
            image_family_summaries = get_image_family_summaries(client, split_name[0])

        for ifs in image_family_summaries:
            if ifs.namespace == split_name[0] and ifs.name == split_name[1]:
                for ig in get_image_family_groups(client, ifs.id):
                    if ig.name == split_name[2]:
                        if ifs.access == ImageAccess.PUBLIC or always_return_id:
                            return _replaced(ig.id, True)
                        else:
                            return _replaced(f"yd/{image_name_or_id}")
                else:
                    raise Exception(
                        "Image family found, but no matching image "
                        f"group for '{original_image_name_or_id}'"
                    )

    # Finally, fall through and return the unchanged, original ID string
    return original_image_name_or_id


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


def split_namespace_and_name(reference: str) -> Tuple[Optional[str], str]:
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
        crt.imagesId = _get_image_family_or_group_name_from_id(client, crt.imagesId)
    except:
        pass

    # Source templates
    try:
        for source in crt.sources:
            source.sourceTemplateId = _get_source_template_name_from_id(
                client, source.sourceTemplateId
            )
            source.imageId = _get_image_family_or_group_name_from_id(
                client, source.imageId
            )
    except:
        pass

    return crt


def substitute_image_family_id_for_name_in_cst(
    client: PlatformClient, cst: ComputeSourceTemplate
) -> ComputeSourceTemplate:
    """
    Substitute Image Family IDs for namespace/name,
    if option is selected.
    """
    if not ARGS_PARSER.substitute_ids:
        return cst

    try:
        cst.source.imageId = _get_image_family_or_group_name_from_id(
            client, cst.source.imageId
        )
        return cst
    except:
        pass

    try:
        # Google uses a different property name
        cst.source.image = _get_image_family_or_group_name_from_id(
            client, cst.source.image
        )
        return cst
    except:
        pass

    return cst


def substitute_id_for_name_in_allowance(
    client: PlatformClient,
    allowance: Union[
        AccountAllowance, RequirementsAllowance, SourcesAllowance, SourceAllowance
    ],
) -> Union[AccountAllowance, RequirementsAllowance, SourcesAllowance, SourceAllowance]:
    """
    Substitute IDs in Allowance objects.
    """
    if not ARGS_PARSER.substitute_ids:
        return allowance

    if isinstance(allowance, RequirementsAllowance):
        allowance.requirementCreatedFromId = _get_requirement_template_name_from_id(
            client, allowance.requirementCreatedFromId
        )

    elif isinstance(allowance, SourcesAllowance):
        allowance.sourceCreatedFromId = _get_source_template_name_from_id(
            client, allowance.sourceCreatedFromId
        )

    # No processing for other allowance types
    return allowance


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
def _get_requirement_template_name_from_id(
    client: PlatformClient, crt_id: Optional[str]
) -> Optional[str]:
    """
    Obtain the namespace/name of a requirement template.
    Otherwise, return the original value.
    """
    if get_ydid_type(crt_id) != YDIDType.COMPUTE_REQUIREMENT_TEMPLATE:
        return crt_id
    try:
        crt: ComputeRequirementTemplate = (
            client.compute_client.get_compute_requirement_template(crt_id)
        )
        return f"{crt.namespace}/{crt.name}"
    except:
        return crt_id


@lru_cache
def _get_image_family_or_group_name_from_id(
    client: PlatformClient, image_family_or_group_id: Optional[str]
) -> Optional[str]:
    """
    Obtain the namespace/name of an image family or image group.
    Otherwise, return the original value.
    """
    if get_ydid_type(image_family_or_group_id) == YDIDType.IMAGE_FAMILY:
        try:
            image_family: MachineImageFamily = (
                client.images_client.get_image_family_by_id(image_family_or_group_id)
            )
            return f"yd/{image_family.namespace}/{image_family.name}"
        except:
            return image_family_or_group_id

    elif get_ydid_type(image_family_or_group_id) == YDIDType.IMAGE_GROUP:
        try:
            image_group: MachineImageGroup = client.images_client.get_image_group_by_id(
                image_family_or_group_id
            )
            image_family: MachineImageFamily = (
                client.images_client.get_image_family_by_id(
                    # The image family ID can be derived from the group ID
                    image_family_or_group_id.replace("imggrp", "imgfam").rsplit(":", 1)[
                        0
                    ]
                )
            )
            return f"yd/{image_family.namespace}/{image_family.name}/{image_group.name}"
        except:
            return image_family_or_group_id

    return image_family_or_group_id


@lru_cache
def get_role_id_by_name(client: PlatformClient, role_name: str) -> Optional[str]:
    """
    Find the ID of a role by its name. Accept IDs and return unchanged.
    """
    if get_ydid_type(role_name) == YDIDType.ROLE:
        return role_name

    role_search = RoleSearch(name=role_name)
    search_client: SearchClient = client.account_client.get_roles(role_search)

    for role in search_client.list_all():
        if role.name == role_name:
            return role.id

    return None


@lru_cache
def get_role_name_by_id(client: PlatformClient, role_id: str) -> Optional[str]:
    """
    Get the name of a role by its ID.
    """
    for role in get_all_roles(client):
        if role.id == role_id:
            return role.name

    return None


@lru_cache
def get_all_roles(client: PlatformClient) -> List[RoleSummary]:
    """
    Cache all roles.
    """
    role_search = RoleSearch()
    search_client: SearchClient = client.account_client.get_roles(role_search)
    return search_client.list_all()


@lru_cache
def get_group_id_by_name(client: PlatformClient, group_name: str) -> Optional[str]:
    """
    Get a group's ID by its name. Accept IDs and return unchanged.
    """
    if get_ydid_type(group_name) == YDIDType.GROUP:
        return group_name

    group_search = GroupSearch(name=group_name)
    search_client: SearchClient = client.account_client.get_groups(group_search)
    group_summaries: List[GroupSummary] = search_client.list_all()

    for group_summary in group_summaries:
        if group_summary.name == group_name:
            return group_summary.id

    return None


@lru_cache
def get_group_name_by_id(client: PlatformClient, group_id: str) -> Optional[str]:
    """
    Get a group's name by its ID.
    """
    for group in get_all_groups(client):
        if group.id == group_id:
            return group.name

    return None


@lru_cache
def get_all_groups(client: PlatformClient) -> List[GroupSummary]:
    """
    Return a list of all the groups.
    """
    group_search = GroupSearch()
    search_client: SearchClient = client.account_client.get_groups(group_search)
    return search_client.list_all()


def clear_group_caches():
    """
    Clear the group caches.
    """
    get_all_groups.cache_clear()
    get_group_name_by_id.cache_clear()
    get_group_id_by_name.cache_clear()


@lru_cache
def get_all_applications(client: PlatformClient) -> List[Application]:
    """
    Return a list of all the applications.
    """
    application_search = ApplicationSearch()
    search_client: SearchClient = client.account_client.get_applications(
        application_search
    )
    return search_client.list_all()


@lru_cache
def get_application_id_by_name(client: PlatformClient, app_name: str) -> Optional[str]:
    """
    Get an application ID by its name. Accept IDs and return unchanged.
    """
    if get_ydid_type(app_name) == YDIDType.APPLICATION:
        return app_name

    for app in get_all_applications(client):
        if app.name == app_name:
            return app.id

    return None


def clear_application_caches():
    """
    Clear the application caches.
    """
    get_all_applications.cache_clear()
    get_application_id_by_name.cache_clear()


def get_application_groups(client: PlatformClient, app_id: str) -> List[GroupSummary]:
    """
    Get the groups to which an application belongs.
    """
    return client.account_client.get_application_groups(app_id).list_all()


def get_user_groups(client: PlatformClient, user_id: str) -> List[GroupSummary]:
    """
    Get the groups to which a user belongs.
    """
    return client.account_client.get_user_groups(user_id).list_all()


@lru_cache
def get_user_by_name_or_id(
    client: PlatformClient, user_name_or_id: str
) -> Optional[User]:
    """
    Get a user ID by name, username or ID.
    """
    for user in get_all_users(client):

        if user.id == user_name_or_id:
            return user

        if (
            isinstance(user, InternalUser)
            and (user.username == user_name_or_id or user.name == user_name_or_id)
        ) or (isinstance(user, ExternalUser) and user.name == user_name_or_id):
            return user

    return None


@lru_cache
def get_all_users(client: PlatformClient) -> List[User]:
    """
    Return a list of all users.
    """
    user_search = UserSearch()
    search_client: SearchClient = client.account_client.get_users(user_search)
    return search_client.list_all()


def get_namespace_id_by_name(
    client: PlatformClient, namespace_name: str
) -> Optional[str]:
    """
    Get a namespace's ID by its name.
    """
    search_client: SearchClient = client.namespaces_client.get_namespaces(
        NamespaceSearch(namespace_name)
    )
    for namespace in search_client.list_all():
        if namespace.namespace == namespace_name:
            return namespace.id

    return None


def get_compute_requirement_summaries(
    client: PlatformClient,
    namespace: Optional[str] = None,
    tag: Optional[str] = None,
    statuses: Optional[List[ComputeRequirementStatus]] = None,
) -> List[ComputeRequirementSummary]:
    """
    Get compute requirement summaries for a namespace, tag.
    Optionally filter on statuses.
    """
    crs_search = ComputeRequirementSummarySearch(
        namespaces=(None if namespace in [None, ""] else [namespace]),
        tag=tag,
        statuses=statuses,
    )
    search_client: SearchClient = (
        client.compute_client.get_compute_requirement_summaries(crs_search)
    )
    return search_client.list_all()


@lru_cache
def get_image_family_summaries(
    client: PlatformClient,
    namespace: Optional[str] = None,
) -> List[MachineImageFamilySummary]:
    """
    Obtain and cache the list of image families.
    """
    # Temporarily suppress most permission errors: will be improved
    # once the application can be queried for its admissible
    # IMAGE_READ namespaces
    try:
        if_search = MachineImageFamilySearch(
            familyName=None,
            namespaces=None if namespace is None else [namespace],
            includePublic=True,
        )
        search_client: SearchClient = client.images_client.get_image_families(if_search)
        return search_client.list_all()
    except Exception as e:
        if namespace is not None and "MissingPermissionException" in str(e):
            # Caching will prevent this warning appearing multiple times
            print_log(
                "Warning: Possible 'IMAGE_READ' permission missing if "
                f"'{namespace}' is meant as an Image namespace?"
            )
        pass

    return []


@lru_cache
def get_image_family_groups(
    client: PlatformClient, image_family_id: str
) -> List[MachineImageGroup]:
    """
    Obtain and cache the list of image groups for an image family.
    """
    return client.images_client.get_image_family_by_id(image_family_id).imageGroups


def clear_image_caches():
    """
    Clear the image caches.
    """
    find_image_name_or_id.cache_clear()
    get_image_family_summaries.cache_clear()
    get_image_family_groups.cache_clear()
