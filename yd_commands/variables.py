"""
Utilities for applying variable substitutions.
"""
import os
import re
import sys
import tempfile
from datetime import datetime
from getpass import getuser
from json import loads as json_loads
from random import randint
from typing import Dict, List, Optional, Union

from toml import load as toml_load

from yd_commands.args import ARGS_PARSER
from yd_commands.check_imports import check_jsonnet_import
from yd_commands.config_keys import *
from yd_commands.printing import print_error, print_json, print_log

# Set up default variable substitutions
UTCNOW = datetime.utcnow()
RAND_SIZE = 0xFFF
VARIABLE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_").lower(),
    "date": UTCNOW.strftime("%y%m%d"),
    "time": UTCNOW.strftime("%H%M%S"),
    "datetime": UTCNOW.strftime("%y%m%d-%H%M%S"),
    "random": hex(randint(0, RAND_SIZE + 1))[2:].lower().zfill(len(hex(RAND_SIZE)) - 2),
}

# Lazy substitutions: 'submit' only
if "submit" in sys.argv[0]:
    L_WR_NAME = "wr_name"
    L_TASK_NUMBER = "task_number"
    L_TASK_GROUP_NUMBER = "task_group_number"
    L_TASK_COUNT = "task_count"
    L_TASK_GROUP_COUNT = "task_group_count"

# Type annotations for variable type substitutions
NUMBER_SUB = "num:"
BOOL_SUB = "bool:"

# Add user-defined variable substitutions
# Can supersede the existing substitutions above
ENV_VAR_PREFIX = "YD_VAR_"

# Directives from environment variables
for key, value in os.environ.items():
    if key.startswith(ENV_VAR_PREFIX):
        key = key[len(ENV_VAR_PREFIX) :]
        VARIABLE_SUBSTITUTIONS[key] = value
        print_log(
            f"Adding environment-defined variable substitution: '{key}' = '{value}'"
        )

# Directives from the command line (take precedence over environment variables)
if ARGS_PARSER.variables is not None:
    for variable in ARGS_PARSER.variables:
        key_value: List = variable.split("=")
        if len(key_value) == 2:
            VARIABLE_SUBSTITUTIONS[key_value[0]] = key_value[1]
            print_log(
                f"Adding command-line-defined variable substitution: "
                f"'{key_value[0]}' = '{key_value[1]}'"
            )
        else:
            print_error(
                f"Error in variable substitution '{key_value[0]}'",
            )
            print_log("Done")
            exit(1)


def add_substitutions(subs: Dict):
    """
    Add a dictionary of substitutions. Do not overwrite existing values, but
    resolve remaining variables if possible.
    """
    global VARIABLE_SUBSTITUTIONS
    subs.update(VARIABLE_SUBSTITUTIONS)
    VARIABLE_SUBSTITUTIONS = subs

    # Populate variables that can now be substituted
    for key, value in VARIABLE_SUBSTITUTIONS.items():
        VARIABLE_SUBSTITUTIONS[key] = substitute_variable_str(value)


def simple_variable_substitution(input_string: Optional[str]) -> Optional[str]:
    """
    Apply basic variable substitutions.
    """
    if input_string is None:
        return None

    for sub, value in VARIABLE_SUBSTITUTIONS.items():
        input_string = input_string.replace(f"{{{{{sub}}}}}", value)

    return input_string


def process_variable_substitutions(
    dict_data: Dict,
    prefix: str = "",
):
    """
    Process a dictionary representing JSON or TOML data.
    Edits the dictionary in-situ.

    Optional 'prefix' allows variable substitutions intended for this
    preprocessor to be disambiguated from those to be passed through
    (specifically for Node Actions in WP JSON documents).

    Allows the use of variable substitutions prefixed with 'num:' or
    'bool:' to be substituted for their correct types.
    """

    def _walk_data(data: Union[Dict, List]):
        """
        Helper function to walk the data structure performing
        variable substitutions.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = substitute_variable_str(value, prefix=prefix)
                elif isinstance(value, dict) or isinstance(value, list):
                    _walk_data(value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, str):
                    data[index] = substitute_variable_str(item, prefix=prefix)
                elif isinstance(item, dict) or isinstance(item, list):
                    _walk_data(item)

    _walk_data(dict_data)


def substitute_variable_str(
    input: Optional[str], prefix: str = ""
) -> Optional[Union[str, int, bool, float]]:
    """
    Transform type-tagged and normal variable
    substitutions into their required types.
    """
    if input is None:
        return None

    if prefix not in input:
        return input

    input = input.replace(prefix, "")

    def _remove_variable_brackets(variable_str: str) -> str:
        return variable_str.replace("{{", "").replace("}}", "")

    if input.startswith(f"{{{{{NUMBER_SUB}"):
        input_variable = input.replace(NUMBER_SUB, "")
        if _remove_variable_brackets(input_variable) not in VARIABLE_SUBSTITUTIONS:
            if ARGS_PARSER.debug:
                print_log(f"Note: No variable substitution found for '{input}'")
            return input
        replaced = simple_variable_substitution(input_variable)
        try:
            replaced_number = int(replaced)
        except ValueError:
            try:
                replaced_number = float(replaced)
            except ValueError:
                raise Exception(
                    f"Non-number used in variable number "
                    f"substitution: '{input}':'{replaced}'"
                )
        return replaced_number

    if input.startswith(f"{{{{{BOOL_SUB}"):
        input_variable = input.replace(BOOL_SUB, "")
        if _remove_variable_brackets(input_variable) not in VARIABLE_SUBSTITUTIONS:
            if ARGS_PARSER.debug:
                print_log(f"Note: No variable substitution found for '{input}'")
            return input
        replaced = simple_variable_substitution(input_variable)
        if replaced.lower() == "true":
            return True
        if replaced.lower() == "false":
            return False
        raise Exception(
            f"Non-boolean used in variable boolean "
            f"substitution: '{input}':'{replaced}'"
        )

    # Note: this will break if variable substitutions intended for this
    # preprocessor are mixed with those intended to be passed through
    return simple_variable_substitution(input)


def load_json_file_with_variable_substitutions(filename: str, prefix: str = "") -> Dict:
    """
    Takes a JSON filename and returns a dictionary with its variable
    substitutions processed.
    """
    with open(filename, "r") as f:
        file_contents = f.read()
    file_contents = variable_process_file_contents(file_contents, prefix=prefix)
    return json_loads(file_contents)


def load_jsonnet_file_with_variable_substitutions(filename: str, prefix="") -> Dict:
    """
    Takes a Jsonnet filename and returns a dictionary with its variable
    substitutions processed.
    """
    check_jsonnet_import()
    from _jsonnet import evaluate_file

    with VariableSubstitutedJsonnetFile(
        filename=filename, prefix=prefix
    ) as preprocessed_filename:
        dict_data = json_loads(evaluate_file(preprocessed_filename))

    # Secondary processing after Jsonnet expansion
    process_variable_substitutions(dict_data, prefix)

    if ARGS_PARSER.jsonnet_dry_run:
        print_log("Dry-run: Printing Jsonnet to JSON conversion")
        print_json(dict_data)
        print_log("Dry run: Complete")
        exit(0)

    return dict_data


def load_toml_file_with_variable_substitutions(filename: str, prefix: str = "") -> Dict:
    """
    Takes a TOML filename and returns a dictionary with its variable
    substitutions processed.
    """
    with open(filename, "r") as f:
        config = toml_load(f)

    # Add any variable substitutions in the TOML file before processing the
    # file as a whole
    try:
        # Convert all values to strings before adding
        add_substitutions(
            {
                var_name: str(var_value)
                for var_name, var_value in config[COMMON_SECTION][VARIABLES].items()
            }
        )
    except KeyError:
        pass

    process_variable_substitutions(config, prefix=prefix)
    return config


class VariableSubstitutedJsonnetFile:
    """
    The jsonnet 'evaluate_file' function will only operate on files,
    not strings, so this context manager class will create a
    temporary, variable-processed file that can be used by the
    evaluator, then deleted.
    """

    def __init__(self, filename: str, prefix: str = ""):
        self.filename = filename
        self.prefix = prefix

    def __enter__(self) -> str:
        """
        Return the filename of the temporary variable-processed
        jsonnet file.
        """
        with open(self.filename, "r") as file:
            file_contents = file.read()
        processed_file_contents: str = variable_process_file_contents(
            file_contents, self.prefix
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(processed_file_contents)
        self.temp_filename: str = temp_file.name
        return self.temp_filename

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.temp_filename)


def variable_process_file_contents(file_contents: str, prefix: str) -> str:
    """
    Process substitutions in the raw contents of a complete file.
    """
    variable_regex = prefix + "{{[:,A-Z,a-z,0-9,_,-]*}}"
    m_expressions = set(re.findall(variable_regex, file_contents))
    for m_expression in m_expressions:
        replacement_expression = substitute_variable_str(m_expression, prefix=prefix)
        if isinstance(replacement_expression, str):
            file_contents = file_contents.replace(m_expression, replacement_expression)
        else:
            # If the replacement is an int, float, or bool, we need to
            # remove the enclosing quotes when we substitute, and ensure
            # that lower case 'false' & 'true' are used. Account for both
            # double and single quotes (for Jsonnet support).
            file_contents = file_contents.replace(
                f'"{m_expression}"', str(replacement_expression).lower()
            )
            file_contents = file_contents.replace(
                f"'{m_expression}'", str(replacement_expression).lower()
            )
    return file_contents
