#!/usr/bin/env python3

"""
A script to remove YellowDog items.
"""

from typing import Dict

from requests.exceptions import HTTPError

from yd_commands.interactive import confirmed
from yd_commands.object_utilities import (
    find_compute_source_id_by_name,
    find_compute_template_id_by_name,
)
from yd_commands.printing import print_error, print_log
from yd_commands.resource_config import load_resource_specifications
from yd_commands.wrapper import CLIENT, main_wrapper


@main_wrapper
def main():
    resources = load_resource_specifications()
    for resource in resources:
        resource_type = resource.pop("resource", "")
        if resource_type == "ComputeSourceTemplate":
            remove_compute_source(resource)
        if resource_type == "ComputeRequirementTemplate":
            remove_compute_template(resource)
        if resource_type == "Keyring":
            remove_keyring(resource)
        if resource_type == "Credential":
            remove_credential(resource)


def remove_compute_source(resource: Dict):
    """
    Remove a Compute Source using a resource specification.
    Should handle any Source Type.
    """
    try:
        source = resource.pop("source")  # Extract the Source properties
        name = source["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    source_id = find_compute_source_id_by_name(CLIENT, name)
    if source_id is None:
        print_error(f"Cannot find Source Template '{name}'")
    else:
        if not confirmed(f"Remove Source Template '{name}'?"):
            return
        CLIENT.compute_client.delete_compute_source_template_by_id(source_id)
        print_log(f"Removed Compute Source '{name}' ({source_id})")


def remove_compute_template(resource: Dict):
    """
    Remove a Compute Requirement Template.
    """
    try:
        name = resource["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    template_id = find_compute_template_id_by_name(CLIENT, name)
    if template_id is None:
        print_error(f"Cannot find Compute Requirement Template '{name}'")
    else:
        if not confirmed(f"Remove Compute Requirement Template '{name}'?"):
            return
        CLIENT.compute_client.delete_compute_requirement_template_by_id(template_id)
        print_log(f"Removed Compute Requirement Template '{name}' ({template_id})")


def remove_keyring(resource: Dict):
    """
    Remove a Keyring.
    """
    try:
        name = resource["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

    if not confirmed(f"Delete Keyring '{name}'?"):
        return

    try:
        CLIENT.keyring_client.delete_keyring_by_name(name)
        print_log(f"Deleted Keyring '{name}'")
    except HTTPError as e:
        if e.response.status_code == 404:
            print_error(f"Keyring '{name}' not found")
        else:
            raise e


def remove_credential(resource: Dict):
    """
    Remove a Credential from a Keyring.
    """
    try:
        keyring_name = resource["keyringName"]
        credential_data = resource["credential"]
        credential_name = credential_data["name"]
    except KeyError as e:
        raise Exception(f"Expected property to be defined ({e})")

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
            print_error(f"Keyring '{keyring_name}' not found")
        else:
            print_error(e)


# Entry point
if __name__ == "__main__":
    main()
