"""
Load data for resource creation/update/removal requests.
"""

from typing import Dict, List

from yd_commands.args import ARGS_PARSER
from yd_commands.printing import print_log
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
        if resource_spec.lower().endswith(".toml"):
            resources_loaded = load_toml_file_with_variable_substitutions(resource_spec)
        elif resource_spec.lower().endswith(".json"):
            resources_loaded = load_json_file_with_variable_substitutions(resource_spec)
        elif resource_spec.lower().endswith(".jsonnet"):
            resources_loaded = load_jsonnet_file_with_variable_substitutions(
                resource_spec
            )
        else:
            raise Exception(
                f"['{resource_spec}'] Resource specifications must end in '.toml',"
                " '.json' or '.jsonnet'"
            )

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

    if len(ARGS_PARSER.resource_specifications) > 1:
        print_log(f"Including {len(resources)} resources in total")

    return _resequence_resources(resources, creation_or_update=creation_or_update)


def _resequence_resources(
    resources: List[Dict], creation_or_update: bool = True
) -> List[Dict]:
    """
    Resequence resources so that possible dependencies are evaluated in the
    correct order. If 'creation_or_update' is True this is a creation/update
    action, otherwise it's a removal action -- the sequencing differs for each.
    """
    if len(resources) == 1:
        return resources

    # Move Compute Source Templates to the beginning or end of the list
    resources.sort(
        key=lambda resource: (
            1 if resource.get("resource", "") == "ComputeSourceTemplate" else 0
        ),
        reverse=creation_or_update,
    )

    # Move Keyrings to the beginning or end of the list
    resources.sort(
        key=lambda resource: (1 if resource.get("resource", "") == "Keyring" else 0),
        reverse=creation_or_update,
    )

    return resources
