#!/usr/bin/env python3

"""
A script to create YellowDog items.
"""

from typing import Dict, List

import yellowdog_client.model as model
from requests import post
from requests.exceptions import HTTPError
from yellowdog_client.model import (
    CloudProvider,
    ImageOsType,
    MachineImage,
    MachineImageFamily,
    MachineImageGroup,
    NamespaceStorageConfiguration,
)
from yellowdog_client.model.exceptions import InvalidRequestException

from yd_commands.interactive import confirmed
from yd_commands.object_utilities import (
    find_compute_source_id_by_name,
    find_compute_template_id_by_name,
)
from yd_commands.printing import print_error, print_log
from yd_commands.resource_config import load_resource_specifications
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


@main_wrapper
def main():
    resources = load_resource_specifications()
    for resource in resources:
        try:
            resource_type = resource.pop("resource")
        except KeyError:
            print_error(
                "Missing required 'resource' property in the following resource"
                f" specification: {resource}"
            )
            continue
        if resource_type == "ComputeSourceTemplate":
            create_compute_source(resource)
        elif resource_type == "ComputeRequirementTemplate":
            create_cr_template(resource)
        elif resource_type == "Keyring":
            create_keyring(resource)
        elif resource_type == "Credential":
            create_credential(resource)
        elif resource_type == "MachineImageFamily":
            create_image_family(resource)
        elif resource_type == "NamespaceStorageConfiguration":
            create_namespace_configuration(resource)
        else:
            print_error(f"Unknown resource type '{resource_type}'")


def create_compute_source(resource: Dict):
    """
    Create or update a Compute Source using a resource specification.
    Should handle any Source Type.
    """
    try:
        source = resource.pop("source")  # Extract the Source properties
        source_type = source.pop("type").split(".")[-1]  # Extract Source type
        name = source["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Discard invalid keyword arguments (not sure if this
    # is the exhaustive list)
    source.pop("provider", None)
    source.pop("createdFromId", None)
    source.pop("id", None)

    # Create the matching Compute Source type
    compute_source = get_model_class(source_type)(**source)

    # Create the ComputeSourceTemplate
    compute_source_template = model.ComputeSourceTemplate(
        **resource, source=compute_source
    )

    # Check for an existing ID
    source_id = find_compute_source_id_by_name(CLIENT, name)
    if source_id is None:
        compute_source = CLIENT.compute_client.add_compute_source_template(
            compute_source_template
        )
        print_log(
            f"Created Compute Source '{compute_source.source.name}'"
            f" ({compute_source.id})"
        )
    else:
        if not confirmed(f"Update existing Source Template '{name}'?"):
            return
        compute_source_template.id = source_id
        compute_source = CLIENT.compute_client.update_compute_source_template(
            compute_source_template
        )
        print_log(
            f"Updated existing Compute Source '{compute_source.source.name}'"
            f" ({compute_source.id})"
        )


def create_cr_template(resource: Dict):
    """
    Create or update a Compute Requirement Template.
    """
    try:
        type = resource.pop("type").split(".")[-1]  # Extract type
        name = resource["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Discard invalid properties
    resource.pop("id", None)

    compute_template = get_model_class(type)(**resource)

    # Check for an existing ID
    template_id = find_compute_template_id_by_name(CLIENT, name)
    if template_id is None:
        template = CLIENT.compute_client.add_compute_requirement_template(
            compute_template
        )
        print_log(
            f"Created Compute Requirement Template '{template.name}' ({template.id})"
        )
    else:
        compute_template.id = template_id
        if not confirmed(f"Update existing Compute Requirement Template '{name}'?"):
            return
        template = CLIENT.compute_client.update_compute_requirement_template(
            compute_template
        )
        print_log(
            f"Updated existing Compute Requirement Template '{template.name}'"
            f" ({template.id})"
        )


def create_keyring(resource: Dict):
    """
    Create or delete/recreate a Keyring.
    """
    try:
        name = resource["name"]
        description = resource["description"]
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
        keyring_password = create_keyring_via_api(name, description)
        if ARGS_PARSER.show_keyring_passwords:
            if not ARGS_PARSER.quiet:
                print_log(f"Created Keyring '{name}': Password = {keyring_password}")
            else:
                print(f"Keyring '{name}': Password = {keyring_password}")
        else:
            print_log(f"Created Keyring '{name}'")
    except Exception as e:
        print_error(f"Failed to create Keyring '{name}': {e}")


def create_keyring_via_api(name: str, description: str) -> str:
    """
    Temporary direct API call to create a Keyring and return the shown-once
    password. The password is not available via the SDK call.
    """
    response = post(
        url=f"{CONFIG_COMMON.url}/keyrings",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json={
            "name": name,
            "description": description,
        },
    )
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} ({response.text})")
    return response.json()["keyringPassword"]


def create_credential(resource: Dict):
    """
    Create or update a Credential.
    """
    try:
        keyring_name = resource["keyringName"]
        credential_data = resource["credential"]
        credential_type = credential_data.pop("type").split(".")[
            -1
        ]  # Extract Source type
        name = credential_data["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    credential = get_model_class(credential_type)(**credential_data)
    try:
        CLIENT.keyring_client.put_credential_by_name(keyring_name, credential)
        print_log(f"Added Credential '{name}' to Keyring '{keyring_name}'")
    except HTTPError as e:
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
        family_name = resource["name"]
        namespace = resource["namespace"]
        os_type = ImageOsType[resource.pop("osType")]  # Change to Enum
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    # Start by updating the outer Image Family
    image_family = MachineImageFamily(osType=os_type, **resource)

    # Check for existing Image Family
    try:
        existing_image_family: MachineImageFamily = (
            CLIENT.images_client.get_image_family_by_name(
                namespace=namespace, family_name=family_name
            )
        )  # Raises HTTP 404 Error if not found
        if not confirmed(f"Update existing Machine Image Family '{family_name}'?"):
            return
        image_family.id = existing_image_family.id
        CLIENT.images_client.update_image_family(image_family)
        print_log(f"Updated existing Machine Image Family '{family_name}'")
    except HTTPError as e:
        if e.response.status_code == 404:
            CLIENT.images_client.add_image_family(image_family)
            print_log(f"Created Machine Image Family '{family_name}'")
        else:
            print_error(f"Failed to create/update Image Family '{image_family}': {e}")
        return

    # This is an update, so Image Groups have been ignored
    image_groups: List[MachineImageGroup] = image_family.imageGroups
    for image_group in image_groups:
        # Ensure well-formed MachineImageGroup object
        image_group = MachineImageGroup(**image_group)
        image_group.osType = ImageOsType[str(image_group.osType)]  # Replace with Enum
        _create_image_group(namespace, image_family, image_group)


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
    except HTTPError as e:
        if e.response.status_code == 404:
            CLIENT.images_client.add_image_group(image_family, image_group)
            print_log(f"Created Machine Image Group '{image_group.name}'")
        else:
            print_error(
                f"Failed to create/update Image Group '{image_group.name}': {e}"
            )
        return

    # This is an update, so Images have been ignored
    images: List[MachineImage] = image_group.images
    for image in images:
        # Ensure well-formed MachineImage object
        image = MachineImage(**image)
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
                CLIENT.images_client.update_image(image)
                print_log(f"Updated existing Machine Image '{image.name}'")
        else:  # New Image
            CLIENT.images_client.add_image(image_group, image)
            print_log(f"Created Machine Image '{image.name}'")
    except InvalidRequestException as e:
        print_error(f"Unable to create/update Image '{image.name}': {e}")


def create_namespace_configuration(resource: Dict):
    """
    Create or update a Namespace Configuration.
    """
    try:
        namespace_type = resource.pop("type").split(".")[-1]  # Extract Source type
        namespace = resource["namespace"]
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

    namespace_configuration = get_model_class(namespace_type)(**resource)
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


def get_model_class(classname):
    """
    Return a YellowDog model class using its classname.
    """
    return getattr(model, classname)


# Entry point
if __name__ == "__main__":
    main()
