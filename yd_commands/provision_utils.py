"""
Utility functions for provisioning
"""

from typing import Optional

from yd_commands.config import ConfigWorkerPool
from yd_commands.config_keys import USERDATA, USERDATAFILE, USERDATAFILES


def get_user_data_property(config: ConfigWorkerPool) -> Optional[str]:
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
    if config.user_data:
        return config.user_data
    if config.user_data_file:
        with open(config.user_data_file, "r") as f:
            return f.read()
    if config.user_data_files:
        user_data_contents = ""
        for user_data_file in config.user_data_files:
            with open(user_data_file, "r") as f:
                user_data_contents += f.read()
                user_data_contents += "\n"
        return user_data_contents
