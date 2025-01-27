"""
Utility functions for provisioning and instantiating.
"""

from os import chdir
from typing import Optional

from yellowdog_client import PlatformClient

from yellowdog_cli.utils.config_types import ConfigWorkerPool
from yellowdog_cli.utils.entity_utils import (
    find_compute_requirement_template_id_by_name,
    find_image_family_reference_by_name,
    split_namespace_and_name,
)
from yellowdog_cli.utils.load_config import CONFIG_FILE_DIR
from yellowdog_cli.utils.printing import print_log
from yellowdog_cli.utils.property_names import USERDATA, USERDATAFILE, USERDATAFILES
from yellowdog_cli.utils.settings import WP_VARIABLES_POSTFIX, WP_VARIABLES_PREFIX
from yellowdog_cli.utils.variables import (
    process_variable_substitutions_in_file_contents,
)
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


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

    # Switch to the directory containing the config file; will use the current
    # directory if the config file is absent
    source_directory = (
        CONFIG_FILE_DIR if content_path is None or content_path == "" else content_path
    )
    try:
        if source_directory != "":
            chdir(source_directory)
    except Exception as e:
        raise Exception(
            f"Unable to switch to content directory '{source_directory}': {e}"
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
    Check if 'template_id_or_name' looks like a valid CRT ID; if not,
    assume it's a CRT name and perform a lookup.
    """
    if get_ydid_type(template_id_or_name) == YDIDType.COMPUTE_REQUIREMENT_TEMPLATE:
        return template_id_or_name

    # If this is a fully qualified CRT name, allow server-side lookup
    namespace, name = split_namespace_and_name(template_id_or_name)
    if namespace is not None:
        return template_id_or_name

    template_id = find_compute_requirement_template_id_by_name(
        client=client, name=template_id_or_name
    )
    if template_id is None:
        return template_id_or_name  # Return the original input

    print_log(
        f"Substituting Compute Requirement Template name '{template_id_or_name}'"
        f" with ID {template_id}"
    )
    return template_id


def get_image_family_id(client: PlatformClient, image_family_id_or_name: str) -> str:
    """
    Check if 'image_id_or_name' looks like a valid IF ID; if not,
    assume it's an IF name and perform a lookup.
    """
    if get_ydid_type(image_family_id_or_name) in [
        YDIDType.IMAGE_FAMILY,
        YDIDType.IMAGE_GROUP,
        YDIDType.IMAGE,
    ]:
        return image_family_id_or_name

    image_family_id = find_image_family_reference_by_name(
        client=client, image_family_name=image_family_id_or_name
    )

    # If a specific image (e.g., an AMI) has been supplied, we'll get here
    # and will return the original value. This does incur the cost of
    # listing image families, and there's a small chance of a collision
    # between a supplied specific image and an Image Family name.

    if image_family_id is None:
        return image_family_id_or_name  # Return the original input

    return image_family_id
