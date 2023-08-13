#!/usr/bin/env python3

"""
A script to create YellowDog items.
"""

from typing import Dict, List

import yellowdog_client.model as model

from yd_commands.interactive import confirmed
from yd_commands.object_utilities import (
    find_compute_source_id_by_name,
    find_compute_template_id_by_name,
)
from yd_commands.printing import print_log
from yd_commands.resource_config import load_resource_specifications
from yd_commands.wrapper import CLIENT, main_wrapper


@main_wrapper
def main():
    resources = load_resource_specifications()
    for resource in resources:
        resource_type = resource.pop("resource", "")
        if resource_type == "ComputeSourceTemplate":
            create_compute_source(resource)
        if resource_type == "ComputeRequirementTemplate":
            create_cr_template(resource)
        if resource_type == "Keyring":
            create_keyring(resource)


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
            if not confirmed(
                    f"Keyring '{name}' already exists: delete and recreate?"):
                return
            CLIENT.keyring_client.delete_keyring_by_name(name)
            print_log(
                f"Deleted Keyring '{name}'"
            )

    CLIENT.keyring_client.create_keyring(name, description)
    print_log(f"Created Keyring '{name}'")


def get_model_class(classname):
    """
    Return a YellowDog model class using its classname.
    """
    return getattr(model, classname)


# Entry point
if __name__ == "__main__":
    main()
