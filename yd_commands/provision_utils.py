"""
Utility functions for provisioning
"""

from os import chdir
from typing import Optional

from yd_commands.config_types import ConfigWorkerPool
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
