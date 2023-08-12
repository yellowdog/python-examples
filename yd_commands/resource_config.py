"""
Handle configuration of resource creation requests.
"""

from typing import List

from yd_commands.args import ARGS_PARSER
from yd_commands.printing import print_log
from yd_commands.variables import (
    load_json_file_with_variable_substitutions,
    load_jsonnet_file_with_variable_substitutions,
    load_toml_file_with_variable_substitutions,
)


def load_resource_specifications() -> List:
    """
    Load and return a list of resource specifications.
    """
    resources = []
    for resource_spec in ARGS_PARSER.resource_specifications:
        if resource_spec.lower().endswith(".toml"):
            resources_toml = load_toml_file_with_variable_substitutions(resource_spec)
            # Extract the list of resources stored under key 'resources'
            # Because TOML doesn't support a top-level enclosing list.
            resources_list = resources_toml.get("resources", [])
        elif resource_spec.lower().endswith(".json"):
            resources_list = load_json_file_with_variable_substitutions(resource_spec)
        elif resource_spec.lower().endswith(".jsonnet"):
            resources_list = load_jsonnet_file_with_variable_substitutions(
                resource_spec
            )
        else:
            raise Exception(
                f"['{resource_spec}'] Resource specifications must end in '.toml',"
                " '.json' or '.jsonnet'"
            )
        print_log(f"Including {len(resources_list)} resource(s) from '{resource_spec}'")
        resources += resources_list

    if len(ARGS_PARSER.resource_specifications) > 1:
        print_log(f"Including {len(resources)} resources in total")

    return resources
