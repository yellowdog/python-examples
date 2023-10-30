"""
Validate property dictionaries.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Union

from yd_commands.printing import print_log
from yd_commands.property_names import *


def validate_properties(data: Dict, context: str):
    """
    Check that all keys in the supplied dictionary are found in the
    ALL_KEYS list. Raise an exception if not.
    """
    invalid_keys = set(_get_keys(data)) - set(ALL_KEYS)
    if len(invalid_keys) > 0:
        raise Exception(f"Invalid properties in {context}: {invalid_keys}")


@dataclass
class DeprecatedKey:
    old_key: str
    new_key: str


DEPRECATED_KEYS = [
    DeprecatedKey("autoShutdown", f"Set {IDLE_POOL_SHUTDOWN_TIMEOUT} to zero"),
    DeprecatedKey("autoShutdownDelay", IDLE_POOL_SHUTDOWN_TIMEOUT),
    DeprecatedKey("nodeBootTimeLimit", NODE_BOOT_TIMEOUT),
    DeprecatedKey("nodeIdleTimeLimit", IDLE_NODE_SHUTDOWN_TIMEOUT),
    DeprecatedKey("idleNodeShutdownEnabled", f"{IDLE_NODE_SHUTDOWN_TIMEOUT} = 0"),
    DeprecatedKey("idlePoolShutdownEnabled", f"{IDLE_POOL_SHUTDOWN_TIMEOUT} = 0"),
]

EXCLUDED_KEYS = [ENV, DOCKER_ENV, VARIABLES, INSTANCE_TAGS]


def _get_keys(data: Union[Dict, List]) -> List[str]:
    """
    Recursively walk a dictionary or list collecting keys.
    Exclude dictionaries with user-specified keys.
    Replace deprecated keys and issue warnings.
    """
    keys: List[str] = []

    if isinstance(data, dict):
        data_copy = deepcopy(data)
        for key, value in data_copy.items():
            key_to_add = key
            for d_key in DEPRECATED_KEYS:
                if key == d_key.old_key:
                    raise Exception(
                        f"Property '{d_key.old_key}' is "
                        f"no longer supported; please replace with '{d_key.new_key}'"
                    )
            keys.append(key_to_add)

            if (isinstance(value, dict) and key not in EXCLUDED_KEYS) or isinstance(
                value, list
            ):
                keys += _get_keys(value)

    elif isinstance(data, list):
        for element in data:
            if isinstance(element, dict):
                keys += _get_keys(element)

    return keys
