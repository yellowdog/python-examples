"""
Load data for resource creation/update/removal requests.
"""

from sys import exit
from typing import Dict, List

from yd_commands.args import ARGS_PARSER
from yd_commands.printing import print_log, print_warning
from yd_commands.settings import (
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
from yd_commands.variables import (
    load_json_file_with_variable_substitutions,
    load_jsonnet_file_with_variable_substitutions,
    load_toml_file_with_variable_substitutions,
    process_variable_substitutions_insitu,
)


def load_resource_specifications(creation_or_update: bool = True) -> List[Dict]:
    """
    Load and return a list of resource specifications assembled from the
    resources described in a set of resource description files.
    """
    resources = []
    for resource_spec in ARGS_PARSER.resource_specifications:
        if resource_spec.lower().endswith(".jsonnet"):
            resources_loaded = load_jsonnet_file_with_variable_substitutions(
                resource_spec, exit_on_dry_run=False
            )
        elif ARGS_PARSER.jsonnet_dry_run:
            print_warning(
                f"['{resource_spec}'] Option '--jsonnet-dry-run' can only be applied"
                f" to files ending in '.jsonnet'"
            )
            continue
        elif resource_spec.lower().endswith(".toml"):
            resources_loaded = load_toml_file_with_variable_substitutions(resource_spec)
        elif resource_spec.lower().endswith(".json"):
            resources_loaded = load_json_file_with_variable_substitutions(resource_spec)
        else:
            exception_message = (
                f"['{resource_spec}'] Resource specifications must end in '.toml', "
                "'.json' or '.jsonnet'"
            )
            if resource_spec.startswith("ydid:") and "":
                exception_message += "; did you mean to use the '--ids' option?"
            raise Exception(exception_message)

        # Transform single resource items into lists
        if isinstance(resources_loaded, dict):
            resources_loaded = [resources_loaded]

        # Secondary variable processing pass
        for resource in resources_loaded:
            process_variable_substitutions_insitu(resource)

        print_log(
            f"Including {len(resources_loaded)} resource(s) from '{resource_spec}'"
        )
        resources += resources_loaded

    if ARGS_PARSER.jsonnet_dry_run:
        exit(0)

    if len(ARGS_PARSER.resource_specifications) > 1:
        print_log(f"Including {len(resources)} resources in total")

    return _resequence_resources(resources, creation_or_update=creation_or_update)


def _resequence_resources(
    resources: List[Dict], creation_or_update: bool = True
) -> List[Dict]:
    """
    Re-sequence resources so that possible dependencies are evaluated in the
    correct order. If 'creation_or_update' is True this is a creation/update
    action, otherwise it's a removal action -- the sequencing differs for each.
    """

    if ARGS_PARSER.no_resequence:
        print_log("Not re-sequencing the resource list")
        return resources

    if len(resources) == 1:
        return resources

    resource_creation_order = [
        RN_KEYRING,
        RN_CREDENTIAL,
        RN_IMAGE_FAMILY,
        RN_STRING_ATTRIBUTE_DEFINITION,
        RN_NUMERIC_ATTRIBUTE_DEFINITION,
        RN_SOURCE_TEMPLATE,
        RN_REQUIREMENT_TEMPLATE,
        RN_ALLOWANCE,
        RN_NAMESPACE_POLICY,
        RN_STORAGE_CONFIGURATION,
        RN_CONFIGURED_POOL,
    ]

    try:
        resources.sort(
            key=lambda resource: resource_creation_order.index(resource["resource"]),
            reverse=not creation_or_update,
        )
    except KeyError:
        raise Exception(
            "Property 'resource' is not specified for one or more resource specifications"
        )
    except ValueError as e:
        resource_type = str(e).split("'")[1]
        raise Exception(f"Unknown resource type: '{resource_type}'")

    return resources
