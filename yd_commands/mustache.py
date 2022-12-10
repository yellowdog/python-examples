"""
Utilities for applying Mustache substitutions.
"""
import os
import sys
from datetime import datetime
from getpass import getuser
from io import StringIO
from json import load as json_load
from json import loads as json_loads
from random import randint
from typing import Dict, List, Optional, Union

from chevron import render as chevron_render
from toml import load as toml_load

from yd_commands.args import ARGS_PARSER
from yd_commands.check_imports import check_jsonnet_import
from yd_commands.config_keys import *
from yd_commands.printing import print_error, print_log

# Set up default Mustache directives
UTCNOW = datetime.utcnow()
RAND_SIZE = 0xFFF
MUSTACHE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_").lower(),
    "date": UTCNOW.strftime("%y%m%d"),
    "time": UTCNOW.strftime("%H%M%S"),
    "datetime": UTCNOW.strftime("%y%m%d-%H%M%S"),
    "random": hex(randint(0, RAND_SIZE + 1))[2:].lower().zfill(len(hex(RAND_SIZE)) - 2),
}

# Add user-defined Mustache directives
# Can supersede the existing directives above
USER_MUSTACHE_PREFIX = "YD_SUB_"

# Directives from environment variables
for key, value in os.environ.items():
    if key.startswith(USER_MUSTACHE_PREFIX):
        key = key[len(USER_MUSTACHE_PREFIX) :]
        MUSTACHE_SUBSTITUTIONS[key] = value
        print_log(f"Adding user-defined Mustache substitution: '{key}' = '{value}'")

# Directives from the command line (take precedence over environment variables)
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


def add_substitutions(subs: Dict):
    """
    Add a dictionary of substitutions. Do not overwrite existing values.
    """
    global MUSTACHE_SUBSTITUTIONS
    subs.update(MUSTACHE_SUBSTITUTIONS)
    MUSTACHE_SUBSTITUTIONS = subs


def simple_mustache_substitution(input_string: Optional[str]) -> Optional[str]:
    """
    Apply basic Mustache substitutions.

    Note that any unsatisfied directives will simply be erased. This is
    undesirable. A new version of Chevron needs to be uploaded to PyPI,
    enabling the 'keep' option. See:
    https://github.com/noahmorrison/chevron/issues/114#issuecomment-1328948904
    """
    if input_string is None:
        return None

    # Trap stderror to capture Chevron misses, if 'debug' is specified
    if ARGS_PARSER.debug:
        error = StringIO()
        sys.stderr = error

    result = chevron_render(
        input_string, MUSTACHE_SUBSTITUTIONS, warn=ARGS_PARSER.debug
    )

    # Restore stderror and report missing substitutions
    if ARGS_PARSER.debug:
        sys.stderr = sys.__stderr__
        error_msg = error.getvalue().rstrip()
        if error_msg != "":
            print_log(f"Note: Mustache substitution error: '{error_msg}'")

    return result


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

    def _remove_mustache_brackets(mustache_str: str) -> str:
        return mustache_str.replace("{{", "").replace("}}", "")

    if input.startswith(f"{{{{{number_}"):
        input_var_mustache = input.replace(number_, "")
        if _remove_mustache_brackets(input_var_mustache) not in MUSTACHE_SUBSTITUTIONS:
            if ARGS_PARSER.debug:
                print_log(f"Note: No Mustache substitution found for '{input}'")
            return input
        replaced = simple_mustache_substitution(input_var_mustache)
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
        input_var_mustache = input.replace(bool_, "")
        if _remove_mustache_brackets(input_var_mustache) not in MUSTACHE_SUBSTITUTIONS:
            if ARGS_PARSER.debug:
                print_log(f"Note: No Mustache substitution found for '{input}'")
            return input
        replaced = simple_mustache_substitution(input_var_mustache)
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
        dict_data = json_load(f)
    process_mustache_substitutions(dict_data, prefix=prefix)
    return dict_data


def load_jsonnet_file_with_mustache_substitutions(filename: str, prefix="") -> Dict:
    """
    Takes a JSONNET filename and returns a dictionary with its mustache
    substitutions processed.
    """

    check_jsonnet_import()
    from _jsonnet import evaluate_file

    dict_data = json_loads(evaluate_file(filename))
    process_mustache_substitutions(dict_data, prefix=prefix)
    return dict_data


def load_toml_file_with_mustache_substitutions(filename: str, prefix: str = "") -> Dict:
    """
    Takes a TOML filename and returns a dictionary with its mustache
    substitutions processed.
    """
    with open(filename, "r") as f:
        config = toml_load(f)

    # Add any Mustache substitutions in the TOML file before processing the
    # file as a whole
    try:
        add_substitutions(config[COMMON_SECTION][MUSTACHE])
    except KeyError:
        pass

    process_mustache_substitutions(config, prefix=prefix)
    return config
