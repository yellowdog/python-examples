"""
Utilities for applying Mustache substitutions.
"""
import os
from datetime import datetime
from getpass import getuser
from json import load as json_load
from random import randint
from typing import Dict, List, Optional, Union

from chevron import render as chevron_render
from toml import load as toml_load

from yd_commands.args import ARGS_PARSER
from yd_commands.printing import print_error, print_log

# Set up Mustache substitutions
UTCNOW = datetime.utcnow()
RAND_SIZE = 0xFFF
MUSTACHE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_").lower(),
    "date": UTCNOW.strftime("%y%m%d"),
    "time": UTCNOW.strftime("%H%M%S"),
    "datetime": UTCNOW.strftime("%y%m%d-%H%M%S"),
    "random": hex(randint(0, RAND_SIZE + 1))[2:].lower().zfill(len(hex(RAND_SIZE)) - 2),
}

# Add user-defined Mustache substitutions
# Can overwrite the existing substitutions above
USER_MUSTACHE_PREFIX = "YD_SUB_"

# Environment variables
for key, value in os.environ.items():
    if key.startswith(USER_MUSTACHE_PREFIX):
        key = key[len(USER_MUSTACHE_PREFIX) :]
        MUSTACHE_SUBSTITUTIONS[key] = value
        print_log(f"Adding user-defined Mustache substitution: '{key}' = '{value}'")

# Command line (takes precedence over environment variables)
if ARGS_PARSER.mustache_subs is not None:
    for sub in ARGS_PARSER.mustache_subs:
        key_value: List = sub.split("=")
        if len(key_value) == 2:
            MUSTACHE_SUBSTITUTIONS[key_value[0]] = key_value[1]
            print_log(
                f"Adding user-defined Mustache substitution: "
                f"'{key_value[0]}' = '{key_value[1]}'"
            )
        else:
            print_error(
                f"Error in Mustache substitution '{key_value[0]}'",
            )
            print_log("Done")
            exit(1)


def simple_mustache_substitution(input_string: Optional[str]) -> Optional[str]:
    """
    Apply basic Mustache substitutions.
    """
    if input_string is None:
        return None
    return chevron_render(input_string, MUSTACHE_SUBSTITUTIONS)


def process_mustache_substitutions(
    dict_data: Dict,
    prefix: str = "",
):
    """
    Process a dictionary representing JSON or TOML data.
    Edits the dictionary in-situ.

    Optional 'prefix' allows Mustache directives intended for this
    preprocessor to be disambiguated from those to be passed through
    (specifically for Node Actions in WP JSON documents).

    Allows the use of Mustache directives prefixed with 'num:' or
    'bool:' to be substituted for their correct types.
    """

    def _walk_data(data: Union[Dict, List]):
        """
        Helper function to walk the data structure performing
        Mustache substitutions.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = substitute_mustache_str(value, prefix=prefix)
                elif isinstance(value, dict) or isinstance(value, list):
                    _walk_data(value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, str):
                    data[index] = substitute_mustache_str(item, prefix=prefix)
                elif isinstance(item, dict) or isinstance(item, list):
                    _walk_data(item)

    _walk_data(dict_data)


def substitute_mustache_str(
    input: Optional[str], prefix: str = ""
) -> Optional[Union[str, int, bool, float]]:
    """
    Transform type-tagged and normal Mustache
    substitutions into their required types.
    """
    if input is None:
        return None

    if prefix not in input:
        return input

    input = input.replace(prefix, "")

    # Supported type annotations
    number_ = "num:"
    bool_ = "bool:"

    if input.startswith(f"{{{{{number_}"):
        replaced = simple_mustache_substitution(
            input.replace(number_, ""),
        )
        try:
            replaced_number = int(replaced)
        except ValueError:
            try:
                replaced_number = float(replaced)
            except ValueError:
                raise Exception(
                    f"Non-number used in Mustache number "
                    f"substitution: '{input}':'{replaced}'"
                )
        return replaced_number

    if input.startswith(f"{{{{{bool_}"):
        replaced = simple_mustache_substitution(
            input.replace(bool_, ""),
        )
        if replaced.lower() == "true":
            return True
        if replaced.lower() == "false":
            return False
        raise Exception(
            f"Non-boolean used in Mustache boolean "
            f"substitution: '{input}':'{replaced}'"
        )

    # Note: this will break if Mustache substitutions intended for this
    # preprocessor are mixed with those intended to be passed through
    return simple_mustache_substitution(input)


def load_json_file_with_mustache_substitutions(filename: str, prefix: str = "") -> Dict:
    """
    Takes a JSON filename and returns a dictionary with its mustache
    substitutions processed.
    """
    with open(filename, "r") as f:
        wr_data = json_load(f)
    process_mustache_substitutions(wr_data, prefix=prefix)
    return wr_data


def load_toml_file_with_mustache_substitutions(filename: str, prefix: str = "") -> Dict:
    """
    Takes a TOML filename and returns a dictionary with its mustache
    substitutions processed.
    """
    with open(filename, "r") as f:
        config = toml_load(f)
    process_mustache_substitutions(config, prefix=prefix)
    return config
