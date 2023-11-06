"""
Utility functions for provisioning and instantiating.
"""

from os import chdir
from typing import Optional

from yellowdog_client import PlatformClient

from yd_commands.config_types import ConfigWorkerPool
from yd_commands.id_utils import YDIDType, get_ydid_type
from yd_commands.object_utilities import find_compute_template_ids_by_name
from yd_commands.printing import print_log
from yd_commands.property_names import USERDATA, USERDATAFILE, USERDATAFILES
from yd_commands.settings import WP_VARIABLES_POSTFIX, WP_VARIABLES_PREFIX
from yd_commands.variables import process_variable_substitutions_in_file_contents


def get_user_data_property(
    config: ConfigWorkerPool, content_path: str = None
) -> Optional[str]:
    """
    Get the 'userData' property, either using the string specified in
    'userData', the file specified in 'userDataFile', or a concatenation
    of the files listed in 'userDataFiles'.
    Raise exception if more than one of these properties is set.
    """
    options = [config.user_data, config.user_data_file, config.user_data_files]
    if options.count(None) < 2:
        raise Exception(
            f"Only one of '{USERDATA}', '{USERDATAFILE}' or '{USERDATAFILES}' "
            "should be set"
        )

    if content_path is not None and content_path != "":
        try:
            chdir(content_path)
        except Exception as e:
            raise Exception(
                f"Unable to switch to content directory '{content_path}': {e}"
            )

    user_data = None

    if config.user_data:
        user_data = config.user_data

    elif config.user_data_file:
        with open(config.user_data_file, "r") as f:
            user_data = f.read()

    elif config.user_data_files:
        user_data = ""
        for user_data_file in config.user_data_files:
            with open(user_data_file, "r") as f:
                user_data += f.read()
                user_data += "\n"

    if user_data is not None:
        try:
            return process_variable_substitutions_in_file_contents(
                user_data, prefix=WP_VARIABLES_PREFIX, postfix=WP_VARIABLES_POSTFIX
            )
        except Exception as e:
            raise Exception(f"Error processing variable substitutions: {e}")


def get_template_id(client: PlatformClient, template_id_or_name: str) -> str:
    """
    Check if 'template_id' looks like a valid CRT ID; if not,
    assume it's a CRT name and perform a lookup.
    """
    if get_ydid_type(template_id_or_name) == YDIDType.CR_TEMPLATE:
        return template_id_or_name

    template_ids = find_compute_template_ids_by_name(
        client=client, name=template_id_or_name
    )
    if len(template_ids) == 0:
        return template_id_or_name  # Return the original input

    if len(template_ids) == 1:
        print_log(
            f"Substituting Compute Requirement Template name '{template_id_or_name}'"
            f" with ID {template_ids[0]}"
        )
    else:
        print_log(
            "Multiple matches for Compute Requirement Template name"
            f" '{template_id_or_name}'; using the first ID {template_ids[0]}"
        )
    return template_ids[0]
