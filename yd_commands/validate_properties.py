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
    invalid_keys = set(_get_keys(data)) - set(ALL_KEYS)
    if len(invalid_keys) > 0:
        raise Exception(f"Invalid properties in {context}: {invalid_keys}")


def _get_keys(data: Union[Dict, List]) -> List[str]:
    """
    Recursively walk a dictionary or list collecting keys.
    Exclude dictionaries with user-specified keys.
    """
    keys: List[str] = []
    excluded_keys = [ENV, DOCKER_ENV, MUSTACHE, INSTANCE_TAGS]
    if isinstance(data, dict):
        for key, value in data.items():
            keys.append(key)
            if (isinstance(value, dict) and key not in excluded_keys) or isinstance(
                value, list
            ):
                keys += _get_keys(value)
    elif isinstance(data, list):
        for element in data:
            if isinstance(element, dict):
                keys += _get_keys(element)
    return keys
