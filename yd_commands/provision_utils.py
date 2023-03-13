"""
Utility functions for provisioning
"""

from typing import Optional

from yd_commands.config import ConfigWorkerPool
from yd_commands.config_keys import USERDATA, USERDATAFILE


def get_user_data_property(config: ConfigWorkerPool) -> Optional[str]:
    """
    Get the 'userData' property, either using the contents of the file
    specified in 'userDataFile' or using the string specified in 'userData'.
    Raise exception if both 'userData' and 'userDataFile' are set.
    """
    if config.user_data and config.user_data_file:
        raise Exception(f"Only one of '{USERDATA}' or '{USERDATAFILE}' should be set")
    if config.user_data:
        return config.user_data
    if config.user_data_file:
        with open(config.user_data_file, "r") as f:
            return f.read()
