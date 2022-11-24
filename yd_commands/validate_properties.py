"""
Validate property dictionaries.
"""

from typing import Dict, List, Union

from yd_commands.config_keys import *


def validate_properties(data: Dict, context: str):
    """
    Check that all keys in the supplied dictionary are found in the
    ALL_KEYS list. Raise an exception if not.
    """
    keys_set = set(_get_keys(data))
    all_keys_set = set(ALL_KEYS)
    invalid_keys = keys_set - all_keys_set
    if len(invalid_keys) > 0:
        raise Exception(f"Invalid properties in {context}: {invalid_keys}")


def _get_keys(data: Union[Dict, List]) -> List[str]:
    """
    Recursively walks a dictionary or list collecting keys.
    Ignore dictionaries mapped to the 'environment' and 'dockerEnvironment' keys,
    # as these will contain user-specified keys.
    """
    keys: List[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            keys.append(key)
            if (
                isinstance(value, dict) and key != ENV and key != DOCKER_ENV
            ) or isinstance(value, list):
                keys += _get_keys(value)
    elif isinstance(data, list):
        for element in data:
            if isinstance(element, dict):
                keys += _get_keys(element)
    return keys
