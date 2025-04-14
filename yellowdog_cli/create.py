#!/usr/bin/env python3

"""
A script to create or update YellowDog resources.
"""

from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Optional

import yellowdog_client.model as model
from dateparser import parse as date_parse
from requests import post, put
from requests.exceptions import HTTPError
from yellowdog_client.model import (
    AccountAllowance,
    AddConfiguredWorkerPoolResponse,
    AllowanceLimitEnforcement,
    AllowanceResetType,
    AwsFleetComputeSource,
    AwsFleetPurchaseOption,
    CloudProvider,
    ImageOsType,
    Keyring,
    MachineImage,
    MachineImageFamily,
    MachineImageGroup,
    NamespacePolicy,
    NamespaceStorageConfiguration,
    RequirementsAllowance,
    SourceAllowance,
    SourcesAllowance,
)
from yellowdog_client.model.exceptions import InvalidRequestException

from yellowdog_cli.utils.entity_utils import (
    clear_compute_source_template_cache,
    clear_image_family_search_cache,
    find_compute_requirement_template_id_by_name,
    find_compute_source_template_id_by_name,
    find_image_family_reference_by_name,
    remove_allowances_matching_description,
)
from yellowdog_cli.utils.interactive import confirmed
from yellowdog_cli.utils.load_resources import load_resource_specifications
from yellowdog_cli.utils.printing import (
    print_error,
    print_json,
    print_log,
    print_warning,
)
from yellowdog_cli.utils.settings import (
    DEFAULT_NAMESPACE,
    NAMESPACE_PREFIX_SEPARATOR,
    PROP_AUTOSCALING_MAX_NODES,
    PROP_CREDENTIAL,
    PROP_CST_ID,
    PROP_DEFAULT_RANK_ORDER,
    PROP_DESCRIPTION,
    PROP_EFFECTIVE_FROM,
    PROP_EFFECTIVE_UNTIL,
    PROP_IMAGE,
    PROP_IMAGE_ID,
    PROP_IMAGES_ID,
    PROP_KEYRING_NAME,
    PROP_NAME,
    PROP_NAMESPACE,
    PROP_OPTIONS,
    PROP_OS_TYPE,
    PROP_RANGE,
    PROP_REQUIREMENT_CREATED_FROM,
    PROP_RESOURCE,
    PROP_SOURCE,
    PROP_SOURCE_CREATED_FROM,
    PROP_SOURCES,
    PROP_TITLE,
    PROP_TYPE,
    PROP_UNITS,
    RN_ALLOWANCE,
    RN_CONFIGURED_POOL,
    RN_CREDENTIAL,
    RN_IMAGE_FAMILY,
    RN_KEYRING,
    RN_NAMESPACE_POLICY,
    RN_NUMERIC_ATTRIBUTE_DEFINITION,
    RN_REQUIREMENT_TEMPLATE,
    RN_SOURCE_TEMPLATE,
    RN_STORAGE_CONFIGURATION,
    RN_STRING_ATTRIBUTE_DEFINITION,
)
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type

CLEAR_CST_CACHE: bool = False  # Track whether the CST cache needs to be cleared
CLEAR_IMAGE_FAMILY_CACHE: bool = False  # Track whether the IF cache needs to be cleared


@main_wrapper
def main():
    create_resources()


def create_resources(
    resources: Optional[List[Dict]] = None, show_secrets: bool = False
):
    """
    Create a list of resources. Resources can be supplied as an argument, or
    loaded from one or more files.
    """
    if resources is None:
        resources = load_resource_specifications(creation_or_update=True)
    else:
        resources = deepcopy(resources)  # Avoid overwriting the input argument

    if ARGS_PARSER.dry_run:
        print_log(
            "Dry-run: displaying processed JSON resource specifications. Note:"
            " 'resource' property is removed."
        )

    for resource in resources:
        try:
            resource_type = resource.pop(PROP_RESOURCE)
            # There is potential additional processing for CRTs, CSTs and
            # Allowances; print JSON from within their creation functions
            if ARGS_PARSER.dry_run and resource_type not in [
                RN_ALLOWANCE,
                RN_REQUIREMENT_TEMPLATE,
                RN_SOURCE_TEMPLATE,
            ]:
                print_json(resource)
                continue
        except KeyError:
            print_error(
                f"Missing required '{PROP_RESOURCE}' property in the following resource"
                f" specification: {resource}"
            )
            continue
        try:
            if resource_type == RN_SOURCE_TEMPLATE:
                create_compute_source_template(resource)
            elif resource_type == RN_REQUIREMENT_TEMPLATE:
                create_compute_requirement_template(resource)
            elif resource_type == RN_KEYRING:
                create_keyring(resource, show_secrets)
            elif resource_type == RN_CREDENTIAL:
                create_credential(resource)
            elif resource_type == RN_IMAGE_FAMILY:
                create_image_family(resource)
            elif resource_type == RN_STORAGE_CONFIGURATION:
                create_namespace_configuration(resource)
            elif resource_type == RN_CONFIGURED_POOL:
                create_configured_worker_pool(resource)
            elif resource_type == RN_ALLOWANCE:
                create_allowance(resource)
            elif resource_type in [
                RN_STRING_ATTRIBUTE_DEFINITION,
                RN_NUMERIC_ATTRIBUTE_DEFINITION,
            ]:
                create_attribute_definition(resource, resource_type)
            elif resource_type == RN_NAMESPACE_POLICY:
                create_namespace_policy(resource)
            else:
                print_error(f"Unknown resource type '{resource_type}'")
        except Exception as e:
            print_error(f"Failed to create resource: {e}")
            # Allow resource creation to continue, if exceptions were not
            # already caught in the creation functions


def create_compute_source_template(resource: Dict):
    """
    Create or update a Compute Source Template using a resource specification.
    Handles all Source types.
    """
    try:
        namespace = resource.get(PROP_NAMESPACE, DEFAULT_NAMESPACE)
        resource[PROP_NAMESPACE] = namespace
        source = resource.pop(PROP_SOURCE)  # Extract the Source properties
        source_type = source.pop(PROP_TYPE).split(".")[-1]  # Extract Source type
        name = source[PROP_NAME]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Allow image families (etc.) to be referenced by name rather than ID
    global CLEAR_IMAGE_FAMILY_CACHE
    if CLEAR_IMAGE_FAMILY_CACHE:  # Update the IF cache if required
        clear_image_family_search_cache()
        CLEAR_IMAGE_FAMILY_CACHE = False

    # Google CSTs use property name 'image' instead of 'imageId'
    image_property_name = (
        PROP_IMAGE_ID
        if source_type
        not in ["GceInstancesComputeSource", "GceInstanceGroupComputeSource"]
        else PROP_IMAGE
    )

    image_id = source.get(image_property_name)
    if get_ydid_type(image_id) not in [
        YDIDType.IMAGE_FAMILY,
        YDIDType.IMAGE_GROUP,
        YDIDType.IMAGE,
    ]:
        image_family_id = find_image_family_reference_by_name(
            client=CLIENT, image_family_name=image_id
        )
        if image_family_id is not None:
            source[image_property_name] = image_family_id

    if ARGS_PARSER.dry_run:
        resource[PROP_SOURCE] = source
        _get_model_object(source_type, source)  # Report extras and omissions
        print_json(resource)
        return

    # Create the Compute Source
    compute_source = _get_model_object(source_type, source)

    # Create the Compute Source Template
    compute_source_template = _get_model_object(
        "ComputeSourceTemplate", resource, source=compute_source
    )

    # Prepend the namespace when searching for existing templates
    name = f"{namespace}{NAMESPACE_PREFIX_SEPARATOR}{name}"

    # Check for an existing ID
    source_id = find_compute_source_template_id_by_name(CLIENT, name)
    if source_id is None:
        compute_source = CLIENT.compute_client.add_compute_source_template(
            compute_source_template
        )
        print_log(f"Created Compute Source Template '{name}'" f" ({compute_source.id})")
    else:
        if not confirmed(f"Update existing Compute Source Template '{name}'?"):
            return
        compute_source_template.id = source_id
        compute_source = CLIENT.compute_client.update_compute_source_template(
            compute_source_template
        )
        print_log(
            f"Updated existing Compute Source Template '{name}'"
            f" ({compute_source.id})"
        )

    global CLEAR_CST_CACHE
    CLEAR_CST_CACHE = True

    if ARGS_PARSER.quiet and compute_source.id is not None:
        print(compute_source.id)


def create_compute_requirement_template(resource: Dict):
    """
    Create or update a Compute Requirement Template. Handles all
    Compute Requirement types.
    """
    try:
        type = resource.pop(PROP_TYPE).split(".")[-1]  # Extract type
        name = resource[PROP_NAME]
        namespace = resource.get(PROP_NAMESPACE, DEFAULT_NAMESPACE)
        resource[PROP_NAMESPACE] = namespace
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Allow source templates to be referenced by name instead of ID:
    # substitute ID for name
    global CLEAR_CST_CACHE
    if CLEAR_CST_CACHE:  # Update the CST cache if required
        clear_compute_source_template_cache()
        CLEAR_CST_CACHE = False

    # Allow image families to be referenced by name rather than ID
    global CLEAR_IMAGE_FAMILY_CACHE
    if CLEAR_IMAGE_FAMILY_CACHE:  # Update the IF cache if required
        clear_compute_source_template_cache()
        CLEAR_IMAGE_FAMILY_CACHE = False

    def _get_images_id(image_str: str, context: Dict, key: str) -> int:
        """
        Helper function to match an image family name into an ID.
        """
        if get_ydid_type(image_str) not in [
            YDIDType.IMAGE_FAMILY,
            YDIDType.IMAGE_GROUP,
            YDIDType.IMAGE,
        ]:
            image_family_id = find_image_family_reference_by_name(
                client=CLIENT, image_family_name=image_str
            )
            if image_family_id is not None:
                context[key] = image_family_id
                return 1
        return 0

    # Prepend the namespace when searching for existing templates
    name = f"{namespace}{NAMESPACE_PREFIX_SEPARATOR}{name}"

    source_template_substitutions = 0
    source_image_id_substitutions = 0

    # Dynamic templates don't have 'sources'; return '[]'
    for source in resource.get(PROP_SOURCES, []):
        template_name_or_id = source[PROP_CST_ID]
        if get_ydid_type(template_name_or_id) != YDIDType.COMPUTE_SOURCE_TEMPLATE:
            template_id = find_compute_source_template_id_by_name(
                client=CLIENT, name=template_name_or_id
            )
            if template_id is None:
                print_error(
                    f"Compute Source Template name '{template_name_or_id}' not found"
                )
                return
            source[PROP_CST_ID] = template_id
            source_template_substitutions += 1

        source_image_id = source.get(PROP_IMAGE_ID)
        if source_image_id is not None:
            source_image_id_substitutions += _get_images_id(
                source_image_id, source, PROP_IMAGE_ID
            )

    if source_template_substitutions > 0:
        print_log(
            f"Replaced {source_template_substitutions} Compute Source Template name(s) with ID(s)"
        )
    if source_image_id_substitutions > 0:
        print_log(f"Replaced {source_image_id_substitutions} Image name(s) with ID(s)")

    images_id = resource.get(PROP_IMAGES_ID)
    if images_id is not None:
        _get_images_id(images_id, resource, PROP_IMAGES_ID)

    if ARGS_PARSER.dry_run:
        _get_model_object(type, resource)  # Report omissions, extras, errors
        print_json(resource)
        return

    # Overwrite source dictionaries with ComputeSourceUsage objects
    resource[PROP_SOURCES] = [
        _get_model_object("ComputeSourceUsage", source)
        for source in resource.get(PROP_SOURCES, [])
    ]

    compute_template = _get_model_object(type, resource)

    # Check for an existing ID
    template_id = find_compute_requirement_template_id_by_name(CLIENT, name)

    if template_id is None:  # Creation
        template = CLIENT.compute_client.add_compute_requirement_template(
            compute_template
        )
        print_log(f"Created Compute Requirement Template '{name}' ({template.id})")
        if ARGS_PARSER.quiet:
            print(template.id)
        return

    # Update
    compute_template.id = template_id
    if not confirmed(
        f"Update existing Compute Requirement Template '{name}' ({template_id})?"
    ):
        return
    template = CLIENT.compute_client.update_compute_requirement_template(
        compute_template
    )
    print_log(
        f"Updated existing Compute Requirement Template '{name}'" f" ({template.id})"
    )
    if ARGS_PARSER.quiet:
        print(template.id)


def create_keyring(resource: Dict, show_secrets: bool = False):
    """
    Create or delete/recreate a Keyring.
    """
    try:
        name = resource[PROP_NAME]
        description = resource[PROP_DESCRIPTION]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    keyrings: List[model.KeyringSummary] = CLIENT.keyring_client.find_all_keyrings()
    for keyring in keyrings:
        if keyring.name == name:
            if not confirmed(f"Keyring '{name}' already exists: delete and recreate?"):
                return
            CLIENT.keyring_client.delete_keyring_by_name(name)
            print_log(f"Deleted Keyring '{name}'")

    try:
        keyring, keyring_password = create_keyring_via_api(name, description)
        keyring_password = (
            keyring_password
            if ARGS_PARSER.show_keyring_passwords or show_secrets
            else "<REDACTED>"
        )
        print_log(
            f"Created Keyring '{name}' ({keyring.id}): Password = {keyring_password}"
        )
        if ARGS_PARSER.quiet:
            print(f"{keyring.id} {keyring_password}")
    except Exception as e:
        print_error(f"Failed to create Keyring '{name}': {e}")


def create_keyring_via_api(name: str, description: str) -> (Keyring, str):
    """
    Temporary direct API call to create a Keyring and return the shown-once
    password. The password is not available via the SDK call.
    """
    response = post(
        url=f"{CONFIG_COMMON.url}/keyrings",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json={
            PROP_NAME: name,
            PROP_DESCRIPTION: description,
        },
    )
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} ({response.text})")
    return Keyring(**response.json()["keyring"]), response.json()["keyringPassword"]


def create_credential(resource: Dict):
    """
    Create or update a Credential.
    """
    try:
        keyring_name = resource[PROP_KEYRING_NAME]
        credential_data = resource[PROP_CREDENTIAL]
        credential_type = credential_data.pop(PROP_TYPE).split(".")[
            -1
        ]  # Extract Source type
        name = credential_data[PROP_NAME]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    credential = _get_model_object(credential_type, credential_data)
    try:
        CLIENT.keyring_client.put_credential_by_name(keyring_name, credential)
        print_log(f"Added Credential '{name}' to Keyring '{keyring_name}'")
    except HTTPError as e:
        print_error(f"Failed to add Credential '{name}' to Keyring '{keyring_name}'")
        if e.response.status_code == 400:
            print_error(f"{e.response.text}")
        elif e.response.status_code == 404:
            print_error(f"Keyring '{keyring_name}' not found")
        else:
            print_error(e)


def create_image_family(resource):
    """
    Create or update an Image Family.
    """
    try:
        family_name = resource[PROP_NAME]
        namespace = resource[PROP_NAMESPACE]
        os_type_str = resource.pop(PROP_OS_TYPE)
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    fq_name = f"{namespace}{NAMESPACE_PREFIX_SEPARATOR}{family_name}"

    try:
        os_type = ImageOsType[os_type_str]  # Change to Enum
    except KeyError:
        raise Exception(
            f"Property '{PROP_OS_TYPE}' has invalid value '{os_type_str}'; valid values are"
            f" {[e.value for e in ImageOsType]}"
        )

    # Start by updating the outer Image Family
    image_family = _get_model_object("MachineImageFamily", resource, osType=os_type)

    # Check for existing Image Family
    try:
        existing_image_family: MachineImageFamily = (
            CLIENT.images_client.get_image_family_by_name(
                namespace=namespace, family_name=family_name
            )
        )  # Raises HTTP 404 Error if not found
        if not confirmed(f"Update existing Machine Image Family '{fq_name}'?"):
            return
        image_family.id = existing_image_family.id
        # This will update the Image Family but not its constituent
        # Image Group/Image resources
        CLIENT.images_client.update_image_family(image_family)
        print_log(
            f"Updated existing Machine Image Family '{fq_name}' ('{image_family.id}')"
        )
        if ARGS_PARSER.quiet:
            print(image_family.id)
    except HTTPError as e:
        if e.response.status_code == 404:
            # This will create the Image Family and all of its constituent
            # Image Group/Image resources
            image_family = CLIENT.images_client.add_image_family(image_family)
            print_log(f"Created Machine Image Family '{fq_name}' ('{image_family.id}')")
            if ARGS_PARSER.quiet:
                print(image_family.id)
        else:
            print_error(f"Failed to create/update Image Family '{fq_name}': {e}")
        return

    # This is an update, so Image Groups have been ignored
    image_groups: List[MachineImageGroup] = image_family.imageGroups

    # Delete Image Groups that have been removed from
    # the new resource specification
    updated_image_group_names = [image_group[PROP_NAME] for image_group in image_groups]
    for existing_image_group in existing_image_family.imageGroups:
        if existing_image_group.name not in updated_image_group_names:
            if confirmed(f"Remove existing Image Group '{existing_image_group.name}'?"):
                CLIENT.images_client.delete_image_group(existing_image_group)
                print_log(f"Deleted Image Group '{existing_image_group.name}'")

    # Update Image Groups
    for image_group in image_groups:
        # Ensure well-formed MachineImageGroup object
        image_group = _get_model_object("MachineImageGroup", image_group)
        image_group.osType = ImageOsType[str(image_group.osType)]  # Replace with Enum
        _create_image_group(namespace, image_family, image_group)

    global CLEAR_IMAGE_FAMILY_CACHE
    CLEAR_IMAGE_FAMILY_CACHE = True


def _create_image_group(
    namespace: str, image_family: MachineImageFamily, image_group: MachineImageGroup
):
    """
    Create or update a Machine Image Group.
    """
    # Check for existing Image Group
    try:
        existing_image_group: MachineImageGroup = (
            CLIENT.images_client.get_image_group_by_name(
                namespace=namespace,
                family_name=image_family.name,
                group_name=image_group.name,
            )
        )  # Raises HTTP 404 Error if not found
        if not confirmed(f"Update existing Machine Image Group '{image_group.name}'?"):
            return
        image_group.id = existing_image_group.id
        CLIENT.images_client.update_image_group(image_group)
        print_log(f"Updated existing Machine Image Group '{image_group.name}'")
        if ARGS_PARSER.quiet:
            print(image_group.id)
    except HTTPError as e:
        if e.response.status_code == 404:
            image_group = CLIENT.images_client.add_image_group(
                image_family, image_group
            )
            print_log(f"Created Machine Image Group '{image_group.name}'")
            if ARGS_PARSER.quiet:
                print(image_group.id)
        else:
            print_error(
                f"Failed to create/update Image Group '{image_group.name}': {e}"
            )
        return

    # This is an update, so Images have been ignored
    images: List[MachineImage] = image_group.images

    # Delete Images that have been removed from
    # the new resource specification
    updated_image_names = [image[PROP_NAME] for image in images]
    for existing_image in existing_image_group.images:
        if existing_image.name not in updated_image_names:
            if confirmed(f"Remove existing Image '{existing_image.name}'?"):
                CLIENT.images_client.delete_image(existing_image)
                print_log(f"Deleted Image '{existing_image.name}'")

    # Update Images
    for image in images:
        # Ensure well-formed MachineImage object
        image = _get_model_object("MachineImage", image)
        image.osType = ImageOsType[str(image.osType)]  # Replace with Enum
        image.provider = CloudProvider[str(image.provider)]  # Replace with Enum
        # Populate the Image ID (this could be made more efficient)
        for existing_image in existing_image_group.images:
            if image.name == existing_image.name:
                image.id = existing_image.id
                break
        _create_image(image, image_group)


def _create_image(image: MachineImage, image_group: MachineImageGroup):
    """
    Create or update a Machine Image.
    """
    try:
        if image.id is not None:  # Existing Image
            if confirmed(f"Update existing Machine Image '{image.name}'?"):
                image = CLIENT.images_client.update_image(image)
                print_log(f"Updated existing Machine Image '{image.name}'")
        else:  # New Image
            image = CLIENT.images_client.add_image(image_group, image)
            print_log(f"Created Machine Image '{image.name}'")
    except InvalidRequestException as e:
        print_error(f"Unable to create/update Image '{image.name}': {e}")

    if ARGS_PARSER.quiet:
        print(image.id)


def create_namespace_configuration(resource: Dict):
    """
    Create or update a Namespace Configuration.
    """
    try:
        namespace_type = resource.pop(PROP_TYPE).split(".")[-1]  # Extract Source type
        namespace = resource[PROP_NAMESPACE]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    namespace_configurations: List[NamespaceStorageConfiguration] = (
        CLIENT.object_store_client.get_namespace_storage_configurations()
    )
    for config in namespace_configurations:
        if config.namespace == namespace:
            print_log(
                f"Updating existing Namespace Storage Configuration '{namespace}'"
            )

    namespace_configuration = _get_model_object(namespace_type, resource)
    try:
        CLIENT.object_store_client.put_namespace_storage_configuration(
            namespace_configuration
        )
        print_log(f"Created/updated Namespace Storage Configuration '{namespace}'")
    except Exception as e:
        print_error(
            "Unable to create/update Namespace Storage Configuration"
            f" '{namespace}': {e}"
        )


def create_configured_worker_pool(resource: Dict):
    """
    Create a Configured Worker Pool. There's no API support for update.
    """
    try:
        name = resource[PROP_NAME]
        namespace = resource.get(PROP_NAMESPACE, DEFAULT_NAMESPACE)
        resource[PROP_NAMESPACE] = namespace
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    name = f"{namespace}{NAMESPACE_PREFIX_SEPARATOR}{name}"

    try:
        cwp_request = _get_model_object("AddConfiguredWorkerPoolRequest", resource)
        cwp_response: AddConfiguredWorkerPoolResponse = (
            CLIENT.worker_pool_client.add_configured_worker_pool(cwp_request)
        )
        print_log(
            f"Created Configured Worker Pool '{name}' ({cwp_response.workerPool.id})"
        )
        print_log(
            f"                   Worker Pool Token = '{cwp_response.token.secret}'"
        )
        print_log(
            "                   Worker Pool Expiry Time = "
            f"{str(cwp_response.token.expiryTime).split('.')[0]}"
        )
        if ARGS_PARSER.quiet:
            print(cwp_response.workerPool.id)

    except Exception as e:
        print_error(f"Unable to created Configured Worker Pool '{name}': {e}")


def create_allowance(resource: Dict):
    """
    Create an allowance.
    """
    try:
        original_type = resource.pop(PROP_TYPE)
        type = original_type.split(".")[-1]  # Extract type
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    if type == "SourcesAllowance":
        template_name_or_id = resource.get(PROP_SOURCE_CREATED_FROM, None)
        if template_name_or_id is not None:
            if get_ydid_type(template_name_or_id) != YDIDType.COMPUTE_SOURCE_TEMPLATE:
                template_id = find_compute_source_template_id_by_name(
                    client=CLIENT, name=template_name_or_id
                )
                if template_id is None:
                    print_error(
                        f"Compute Source Template name '{template_name_or_id}' not found"
                    )
                    return
                print_log(
                    f"Replaced Source Template name '{template_name_or_id}'"
                    f" with ID {template_id}"
                )
                resource[PROP_SOURCE_CREATED_FROM] = template_id

    elif type == "RequirementsAllowance":
        template_name_or_id = resource.get(PROP_REQUIREMENT_CREATED_FROM, None)
        if template_name_or_id is not None:
            if (
                get_ydid_type(template_name_or_id)
                != YDIDType.COMPUTE_REQUIREMENT_TEMPLATE
            ):
                template_id = find_compute_requirement_template_id_by_name(
                    client=CLIENT, name=template_name_or_id
                )
                if template_id is None:
                    print_error(
                        f"Compute Requirement Template name '{template_name_or_id}' not found"
                    )
                    return
                print_log(
                    f"Replaced Requirement Template name '{template_name_or_id}'"
                    f" with ID {template_id}"
                )
                resource[PROP_REQUIREMENT_CREATED_FROM] = template_id

    # Datetime string conversion
    def _display_datetime(dt: datetime, canonical: bool = False) -> str:
        if canonical:
            return dt.strftime("%Y-%m-%dT%H:%M:%S%Z%z").rstrip()
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z%z").rstrip()

    effective_from = resource.get(PROP_EFFECTIVE_FROM, None)
    if effective_from is not None:
        resource[PROP_EFFECTIVE_FROM] = date_parse(effective_from)
        if resource[PROP_EFFECTIVE_FROM] is None:
            raise Exception(
                f"Unable to parse '{PROP_EFFECTIVE_FROM}' date '{effective_from}'"
            )
        print_log(
            f"Property '{PROP_EFFECTIVE_FROM}' = '{effective_from}' set to "
            f"'{_display_datetime(resource[PROP_EFFECTIVE_FROM])}'"
        )

    effective_until = resource.get(PROP_EFFECTIVE_UNTIL, None)
    if effective_until is not None:
        resource[PROP_EFFECTIVE_UNTIL] = date_parse(effective_until)
        if resource[PROP_EFFECTIVE_UNTIL] is None:
            raise Exception(
                f"Unable to parse '{PROP_EFFECTIVE_UNTIL}' date '{effective_until}'"
            )
        print_log(
            f"Property '{PROP_EFFECTIVE_UNTIL}' = '{effective_until}' set to "
            f"'{_display_datetime(resource[PROP_EFFECTIVE_UNTIL])}'"
        )

    if ARGS_PARSER.dry_run:
        _get_model_object(type, resource)  # Report extras and omissions
        # Datetime objects must be converted to strings for JSON presentation
        for property_ in [PROP_EFFECTIVE_FROM, PROP_EFFECTIVE_UNTIL]:
            if resource.get(property_, None) is not None:
                resource[property_] = _display_datetime(
                    resource[property_], canonical=True
                )
        resource[PROP_TYPE] = original_type  # Reinstate property
        print_json(resource)
        return

    description = resource.get(PROP_DESCRIPTION, None)
    if ARGS_PARSER.match_allowances_by_description:
        # Look for existing Allowances that match the description string
        if description is not None:
            print_log(
                "Checking for and removing existing Allowance(s) matching "
                f"description '{description}'"
            )
            remove_allowances_matching_description(CLIENT, description)

    try:
        allowance = CLIENT.allowances_client.add_allowance(
            _get_model_object(type, resource)
        )
        if description is None:
            print_log(f"Created new Allowance {allowance.id}")
        else:
            print_log(f"Created new Allowance '{description}' ({allowance.id})")
    except Exception as e:
        print_error(f"Unable to create Allowance: {e}")
        return

    if ARGS_PARSER.quiet and allowance.id is not None:
        print(allowance.id)


def _get_model_object(class_name: str, resource: Dict, **kwargs):
    """
    Return a populated YellowDog model object for the resource.
    Discard unexpected keywords.
    """

    def _patch_aws_fleet_enums():
        if isinstance(model_object, AwsFleetComputeSource):
            try:
                model_object.purchaseOption = AwsFleetPurchaseOption[
                    str(model_object.purchaseOption)
                ]
            except KeyError:
                raise Exception(
                    "Invalid AWS Fleet Compute Source Purchase Option property: "
                    f"'{str(model_object.purchaseOption)}'"
                )

    def _patch_allowance_enums():
        if (
            isinstance(model_object, SourceAllowance)
            or isinstance(model_object, SourcesAllowance)
            or isinstance(model_object, RequirementsAllowance)
            or isinstance(model_object, AccountAllowance)
        ):
            try:
                model_object.limitEnforcement = AllowanceLimitEnforcement(
                    model_object.limitEnforcement
                )
                model_object.resetType = AllowanceResetType(model_object.resetType)
            except KeyError as e:
                raise Exception(f"Invalid Allowance property: {e}")

    while True:
        try:
            model_object = _get_model_class(class_name)(**resource, **kwargs)
            _patch_aws_fleet_enums()
            _patch_allowance_enums()
            return model_object
        except Exception as e:
            # Unexpected/missing keyword argument Exception of form:
            # __init__() got an unexpected keyword argument 'keyword', or
            # __init__() missing 1 required positional argument: 'credential'
            if "unexpected" in str(e):
                keyword = str(e).split("'")[1]
                print_warning(f"Ignoring unexpected property '{keyword}'")
                resource.pop(keyword)
            elif "missing" in str(e):
                keyword = str(e).split("'")[1]
                raise Exception(f"Missing expected property '{keyword}'")
            else:
                raise e


def _get_model_class(class_name: str):
    """
    Return a YellowDog model class using its class name.
    """
    return getattr(model, class_name)


def create_attribute_definition(resource: Dict, resource_type: str):
    """
    Use the API to create/update user attribute definitions.
    """
    try:
        name = resource[PROP_NAME]
        title = resource[PROP_TITLE]
        if resource_type == RN_NUMERIC_ATTRIBUTE_DEFINITION:
            default_rank_order = resource[PROP_DEFAULT_RANK_ORDER]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    url = f"{CONFIG_COMMON.url}/compute/attributes/user"
    headers = {"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"}
    if resource_type == RN_STRING_ATTRIBUTE_DEFINITION:
        payload = {
            # Required
            PROP_TYPE: "co.yellowdog.platform.model.StringAttributeDefinition",
            PROP_NAME: name,
            PROP_TITLE: title,
            # Optional
            PROP_DESCRIPTION: resource.get(PROP_DESCRIPTION),
            PROP_OPTIONS: resource.get(PROP_OPTIONS),
        }
    else:  # RN_NUMERIC_ATTRIBUTE_DEFINITION
        payload = {
            # Required
            PROP_TYPE: "co.yellowdog.platform.model.NumericAttributeDefinition",
            PROP_NAME: name,
            PROP_TITLE: title,
            PROP_DEFAULT_RANK_ORDER: default_rank_order,
            # Optional
            PROP_DESCRIPTION: resource.get(PROP_DESCRIPTION),
            PROP_UNITS: resource.get(PROP_UNITS),
            # Note: Only one of 'range', 'options' can be supplied
            # Allow the API to error-check
            PROP_RANGE: resource.get(PROP_RANGE),
            PROP_OPTIONS: resource.get(PROP_OPTIONS),
        }

    # Attempt attribute creation
    print_log(f"Attempting to create or update Attribute Definition '{name}'")
    response = post(url=url, headers=headers, json=payload)

    if response.status_code == 200:
        print_log(f"Created new Attribute Definition '{name}'")
        return

    if "Attribute already exists" in response.text:
        if not confirmed(f"Update existing Attribute Definition '{name}'?"):
            return

        response = put(url=url, headers=headers, json=payload)
        if response.status_code == 200:
            print_log(f"Updated existing Attribute Definition '{name}'")
            return

    raise Exception(f"HTTP {response.status_code} ({response.text})")


def create_namespace_policy(resource: Dict):
    """
    Create or update a namespace policy.
    """
    try:
        namespace_policy = NamespacePolicy(
            namespace=resource[PROP_NAMESPACE],
            autoscalingMaxNodes=resource.get(PROP_AUTOSCALING_MAX_NODES),
        )
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Test for existing policy
    try:
        CLIENT.namespaces_client.get_namespace_policy(
            namespace=namespace_policy.namespace
        )
        if not confirmed(
            f"Update existing Namespace Policy '{namespace_policy.namespace}'?"
        ):
            return
    except Exception:
        # Assume it's not found ... 404 from API
        pass

    try:
        CLIENT.namespaces_client.save_namespace_policy(namespace_policy)
    except Exception as e:
        print_error(
            f"Unable to create or update Namespace Policy for '{namespace_policy.namespace}': {e}"
        )
        return

    print_log(
        f"Created or updated  Namespace Policy '{namespace_policy.namespace}' with "
        f"'autoscalingMaxNodes={namespace_policy.autoscalingMaxNodes}'"
    )


# Entry point
if __name__ == "__main__":
    main()
