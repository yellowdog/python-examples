#!/usr/bin/env python3

"""
A script to remove YellowDog resources.
"""

from copy import deepcopy
from typing import Dict, List, Optional

from requests.exceptions import HTTPError
from yellowdog_client.model import (
    NamespaceStorageConfiguration,
    WorkerPoolStatus,
    WorkerPoolSummary,
)

from yd_commands.interactive import confirmed
from yd_commands.load_resources import load_resource_specifications
from yd_commands.object_utilities import (
    find_compute_requirement_template_ids_by_name,
    find_compute_source_template_id_by_name,
    remove_allowances_matching_description,
)
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.settings import (
    RN_ALLOWANCE,
    RN_CONFIGURED_POOL,
    RN_CREDENTIAL,
    RN_IMAGE_FAMILY,
    RN_KEYRING,
    RN_REQUIREMENT_TEMPLATE,
    RN_SOURCE_TEMPLATE,
    RN_STORAGE_CONFIGURATION,
)
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():
    remove_resources()


def remove_resources(resources: Optional[List[Dict]] = None):
    """
    Remove a list of resources either supplied as an argument
    or loaded from files, or by ID.
    """
    if ARGS_PARSER.ids:
        for resource_id in ARGS_PARSER.resource_specifications:
            remove_resource_by_id(resource_id)
        return

    if resources is None:
        resources = load_resource_specifications(creation_or_update=False)
    else:
        resources = deepcopy(resources)  # Avoid overwriting the input argument

    for resource in resources:
        try:
            resource_type = resource.pop("resource")
        except KeyError:
            print_error(
                "Missing required 'resource' property in the following resource"
                f" specification: {resource}"
            )
            continue
        try:
            if resource_type == RN_SOURCE_TEMPLATE:
                remove_compute_source_template(resource)
            elif resource_type == RN_REQUIREMENT_TEMPLATE:
                remove_compute_requirement_template(resource)
            elif resource_type == RN_KEYRING:
                remove_keyring(resource)
            elif resource_type == RN_CREDENTIAL:
                remove_credential(resource)
            elif resource_type == RN_IMAGE_FAMILY:
                remove_image_family(resource)
            elif resource_type == RN_STORAGE_CONFIGURATION:
                remove_namespace_configuration(resource)
            elif resource_type == RN_CONFIGURED_POOL:
                remove_configured_worker_pool(resource)
            elif resource_type == RN_ALLOWANCE:
                if ARGS_PARSER.match_allowances_by_description:
                    remove_allowance(resource)
                else:
                    print_warning(
                        "To remove Allowances by matching on their 'description', "
                        "please use the '--match-allowances-by-description' flag; "
                        "alternatively, Allowances can be removed by their "
                        "YellowDog IDs (yd-remove --ids)"
                    )
            else:
                print_error(f"Unknown resource type '{resource_type}'")
        except Exception as e:
            print_error(f"Failed to remove resource: {e}")
            # Allow removal to continue


def remove_compute_source_template(resource: Dict):
    """
    Remove a Compute Source Template using a resource specification.
    Should handle any Source Type.
    """
    try:
        source = resource.pop("source")  # Extract the Source properties
        name = source["name"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    source_id = find_compute_source_template_id_by_name(CLIENT, name)
    if source_id is None:
        print_warning(f"Cannot find Compute Source Template '{name}'")
        return

    if not confirmed(f"Remove Compute Source Template '{name}'?"):
        return

    try:
        CLIENT.compute_client.delete_compute_source_template_by_id(source_id)
        print_log(f"Removed Compute Source Template '{name}' ({source_id})")
    except Exception as e:
        print_error(
            f"Unable to remove Compute Source Template '{name}' ({source_id}): {e}"
        )


def remove_compute_requirement_template(resource: Dict):
    """
    Remove a Compute Requirement Template.
    """
    try:
        name = resource["name"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    template_ids = find_compute_requirement_template_ids_by_name(CLIENT, name)
    if len(template_ids) == 0:
        print_warning(f"Cannot find Compute Requirement Template '{name}'")
        return

    if len(template_ids) > 1:
        print_warning(
            f"{len(template_ids)} Compute Requirement Templates with the name '{name}'"
        )

    for template_id in template_ids:
        if not confirmed(
            f"Remove Compute Requirement Template '{name}' ({template_id})?"
        ):
            return
        try:
            CLIENT.compute_client.delete_compute_requirement_template_by_id(template_id)
            print_log(f"Removed Compute Requirement Template '{name}' ({template_id})")
        except Exception as e:
            print_error(
                f"Unable to remove Compute Requirement Template '{name}'"
                f" ({template_id}): {e}"
            )


def remove_keyring(resource: Dict):
    """
    Remove a Keyring.
    """
    try:
        name = resource["name"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    if not confirmed(f"Delete Keyring '{name}'?"):
        return

    try:
        CLIENT.keyring_client.delete_keyring_by_name(name)
        print_log(f"Deleted Keyring '{name}'")
    except HTTPError as e:
        if e.response.status_code == 404:
            print_warning(f"Keyring '{name}' not found")
        else:
            print_error(f"Unable to delete Keyring '{name}': {e}")


def remove_credential(resource: Dict):
    """
    Remove a Credential from a Keyring.
    """
    try:
        keyring_name = resource["keyringName"]
        credential_data = resource["credential"]
        credential_name = credential_data["name"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    if not confirmed(
        f"Remove Credential '{credential_name}' from Keyring '{keyring_name}'?"
    ):
        return

    try:
        CLIENT.keyring_client.delete_credential_by_name(keyring_name, credential_name)
        print_log(
            f"Removed Credential '{credential_name}' from Keyring '{keyring_name}' (if"
            " it was present)"
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            print_warning(
                f"Keyring '{keyring_name}' not found (possibly already deleted,"
                " including its credentials?)"
            )
        else:
            print_error(f"Unable to remove Keyring '{keyring_name}': {e}")


def remove_image_family(resource: Dict):
    """
    Remove an Image Family.
    """
    try:
        family_name = resource["name"]
        namespace = resource["namespace"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    # Check for existence of Image Family
    try:
        image_family = CLIENT.images_client.get_image_family_by_name(
            namespace=namespace, family_name=family_name
        )
        if not confirmed(f"Remove Machine Image Family '{namespace}/{family_name}'?"):
            return
    except HTTPError as e:
        if e.response.status_code == 404:
            print_warning(f"Machine Image Family '{namespace}/{family_name}' not found")
            return
        else:
            raise e

    try:
        CLIENT.images_client.delete_image_family(image_family)
        print_log(f"Deleted Image Family '{namespace}/{family_name}'")
    except Exception as e:
        print_error(f"Unable to delete Image Family '{namespace}/{family_name}': {e}")


def remove_namespace_configuration(resource: Dict):
    """
    Remove a Namespace Storage Configuration.
    """
    try:
        namespace = resource["namespace"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    namespaces: List[NamespaceStorageConfiguration] = (
        CLIENT.object_store_client.get_namespace_storage_configurations()
    )
    if namespace not in [x.namespace for x in namespaces]:
        print_warning(f"Namespace Storage Configuration '{namespace}' not found")
        return

    if not confirmed(f"Remove Namespace Storage Configuration '{namespace}'?"):
        return

    try:
        CLIENT.object_store_client.delete_namespace_storage_configuration(namespace)
        print_log(f"Removed Namespace Storage Configuration '{namespace}'")
    except Exception as e:
        print_error(
            f"Unable to remove Namespace Storage Configuration '{namespace}': {e}"
        )


def remove_configured_worker_pool(resource: Dict):
    """
    Shutdown a Configured Worker Pool.
    """
    try:
        name = resource["name"]
    except KeyError as e:
        print_error(f"Expected property to be defined ({e})")
        return

    worker_pools: List[WorkerPoolSummary] = (
        CLIENT.worker_pool_client.find_all_worker_pools()
    )

    # Shut down all matching Configured Worker Pools in appropriate states.
    for worker_pool in worker_pools:
        if (
            worker_pool.name == name
            and worker_pool.type.split(".")[-1] == "ConfiguredWorkerPool"
        ):
            if worker_pool.status not in [
                WorkerPoolStatus.SHUTDOWN,
                WorkerPoolStatus.TERMINATED,
            ]:
                if not confirmed(
                    f"Shut down Configured Worker Pool '{worker_pool.name}'"
                    f" ({worker_pool.id})?"
                ):
                    continue
                try:
                    CLIENT.worker_pool_client.shutdown_worker_pool_by_id(worker_pool.id)
                    print_log(
                        f"Shutting down [{worker_pool.status}] Configured Worker Pool"
                        f" '{name}' ({worker_pool.id})"
                    )
                except Exception as e:
                    print_error(f"Failed to shut down Configured Worker Pool: {e}")
            else:
                print_log(
                    f"Not shutting down [{worker_pool.status}] Configured Worker Pool"
                    f" '{name}' ({worker_pool.id})"
                )


def remove_allowance(resource: Dict):
    """
    Remove an allowance, matching on the 'description' property.
    """
    description = resource.get("description", None)
    if description is not None:
        print_log(f"Removing allowance(s) matching description '{description}'")
        num_removed = remove_allowances_matching_description(CLIENT, description)
        print_log(f"Removed {num_removed} Allowance(s)")


def remove_resource_by_id(resource_id: str):
    """
    Remove a resource by its YDID.
    """
    try:
        if resource_id.startswith("ydid:cst:"):
            if confirmed(f"Remove Compute Source Template {resource_id}?"):
                CLIENT.compute_client.delete_compute_source_template_by_id(resource_id)
                print_log(f"Removed Compute Source Template {resource_id} (if present)")

        elif resource_id.startswith("ydid:crt:"):
            if confirmed(f"Remove Compute Requirement Template {resource_id}?"):
                CLIENT.compute_client.delete_compute_requirement_template_by_id(
                    resource_id
                )
                print_log(
                    f"Removed Compute Requirement Template {resource_id} (if present)"
                )

        elif resource_id.startswith("ydid:imgfam:"):
            if confirmed(f"Remove Image Family '{resource_id}'?"):
                CLIENT.images_client.delete_image_family(resource_id)
                print_log(f"Removed Image Family {resource_id} (if present)")

        elif resource_id.startswith("ydid:keyring:"):
            if confirmed(f"Remove Keyring {resource_id}?"):
                keyrings = CLIENT.keyring_client.find_all_keyrings()
                for keyring in keyrings:
                    if keyring.id == resource_id:
                        CLIENT.keyring_client.delete_keyring_by_name(keyring.name)
                        print_log(f"Removed Keyring {resource_id}")
                        return
                raise Exception(f"Keyring {resource_id} not found")

        elif resource_id.startswith("ydid:wrkrpool:"):
            if confirmed(f"Shut down Worker Pool {resource_id}?"):
                CLIENT.worker_pool_client.shutdown_worker_pool_by_id(resource_id)
                print_log(f"Shut down Worker Pool {resource_id}")

        elif resource_id.startswith("ydid:allow:"):
            if confirmed(f"Remove Allowance {resource_id}?"):
                CLIENT.allowances_client.delete_allowance_by_id(resource_id)
                print_log(f"Removed Allowance {resource_id} (if present)")

        else:
            print_error(f"Resource ID type is unknown/unsupported: {resource_id}")

    except Exception as e:
        print_error(f"Unable to remove resource with ID {resource_id}: {e}")


# Entry point
if __name__ == "__main__":
    main()
