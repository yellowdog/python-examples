"""
Utilities for applying variable substitutions.
"""
import os
import re
import sys
import tempfile
from ast import literal_eval
from getpass import getuser
from json import loads as json_loads
from random import randint
from typing import Dict, List, Optional, Union

from toml import load as toml_load

from yd_commands.args import ARGS_PARSER
from yd_commands.check_imports import check_jsonnet_import
from yd_commands.config_types import WP_VARIABLES_POSTFIX, WP_VARIABLES_PREFIX
from yd_commands.printing import print_error, print_json, print_log
from yd_commands.property_names import *
from yd_commands.utils import UTCNOW, remove_outer_delimiters, split_delimited_string

# Set up default variable substitutions
RAND_SIZE = 0xFFF
VARIABLE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_").lower(),
    "date": UTCNOW.strftime("%y%m%d"),
    "time": UTCNOW.strftime("%H%M%S"),
    "datetime": UTCNOW.strftime("%y%m%d-%H%M%S"),
    "random": hex(randint(0, RAND_SIZE + 1))[2:].lower().zfill(len(hex(RAND_SIZE)) - 2),
}

VAR_OPENING_DELIMITER = "{{"
VAR_CLOSING_DELIMITER = "}}"

# Lazy substitutions: 'submit' only
if "submit" in sys.argv[0]:
    L_WR_NAME = "wr_name"
    L_TASK_NAME = "task_name"
    L_TASK_NUMBER = "task_number"
    L_TASK_GROUP_NAME = "task_group_name"
    L_TASK_GROUP_NUMBER = "task_group_number"
    L_TASK_COUNT = "task_count"
    L_TASK_GROUP_COUNT = "task_group_count"

# Type annotations for variable type substitutions
NUMBER_SUB = "num:"
BOOL_SUB = "bool:"
ARRAY_SUB = "array:"
TABLE_SUB = "table:"

# Allow the use of default variables
DEFAULT_VAR_SEPARATOR = ":="

# Nested variables depth supported in TOML files
NESTED_DEPTH = 3

# Add user-defined variable substitutions
# Can supersede the existing substitutions above
ENV_VAR_PREFIX = "YD_VAR_"

# Substitutions from environment variables
for key, value in os.environ.items():
    if key.startswith(ENV_VAR_PREFIX):
        key = key[len(ENV_VAR_PREFIX) :]
        VARIABLE_SUBSTITUTIONS[key] = value
        print_log(
            f"Adding environment-defined variable substitution: '{key}' = '{value}'"
        )

# Substitutions from the command line (take precedence over environment variables)
if ARGS_PARSER.variables is not None:
    for variable in ARGS_PARSER.variables:
        key_value: List = variable.split("=")
        if len(key_value) == 2:
            VARIABLE_SUBSTITUTIONS[key_value[0]] = key_value[1]
            print_log(
                "Adding command-line-defined variable substitution: "
                f"'{key_value[0]}' = '{key_value[1]}'"
            )
        else:
            print_error(
                f"Error in variable substitution '{key_value[0]}'",
            )
            exit(1)  # Note: exception trap not yet in place


def add_substitutions(subs: Dict):
    """
    Add a dictionary of substitutions. Do not overwrite existing values, but
    resolve remaining variables if possible.
    """
    global VARIABLE_SUBSTITUTIONS
    subs.update(VARIABLE_SUBSTITUTIONS)
    VARIABLE_SUBSTITUTIONS = subs

    # Populate variables that can now be substituted
    # Ensure that the value is stored as a string
    for key, value in VARIABLE_SUBSTITUTIONS.items():
        VARIABLE_SUBSTITUTIONS[key] = process_variable_substitutions(str(value))


def add_substitution_overwrite(key: str, value: str):
    """
    Add a substitution to the dictionary, overwriting existing values.
    """
    VARIABLE_SUBSTITUTIONS[key] = str(value)


def process_variable_substitutions_in_dict_insitu(
    dict_data: Dict, prefix: str = "", postfix: str = ""
):
    """
    Process a dictionary representing JSON or TOML data.
    Updates the dictionary in-situ.

    Optional 'prefix' and 'postfix' allow variable substitutions intended
    for this preprocessor to be disambiguated from those to be passed through
    (specifically for Node Actions in WP JSON documents).
    """

    def _walk_data(data: Union[Dict, List]):
        """
        Helper function to walk the data structure performing
        variable substitutions.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Require the use of post/prefix only for userData in TOML
                    if key == USERDATA:
                        data[key] = process_variable_substitutions(
                            value,
                            prefix=WP_VARIABLES_PREFIX,
                            postfix=WP_VARIABLES_POSTFIX,
                        )
                    else:
                        data[key] = process_variable_substitutions(
                            value, prefix=prefix, postfix=postfix
                        )
                elif isinstance(value, dict) or isinstance(value, list):
                    _walk_data(value)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, str):
                    data[index] = process_variable_substitutions(
                        item, prefix=prefix, postfix=postfix
                    )
                elif isinstance(item, dict) or isinstance(item, list):
                    _walk_data(item)

    _walk_data(dict_data)


def process_variable_substitutions(
    input_string: Optional[str], prefix: str = "", postfix: str = ""
) -> Optional[Union[str, int, bool, float, List, Dict]]:
    """
    Transform type-tagged and normal variable substitutions into their
    required types.
    """
    if input_string is None:
        return None

    opening_delimiter = prefix + VAR_OPENING_DELIMITER
    closing_delimiter = VAR_CLOSING_DELIMITER + postfix

    if opening_delimiter not in input_string or closing_delimiter not in input_string:
        return input_string  # Nothing to process

    # Remember the top-level type tag, if present; a type-tag is only
    # relevant if at the start of the string to be processed;
    # 'None' indicates no type, i.e., a string
    try:
        type_tag = re.findall(
            f"^{opening_delimiter}({NUMBER_SUB}|{BOOL_SUB}|{TABLE_SUB}|{ARRAY_SUB})",
            input_string,
        )[0].replace(opening_delimiter, "")
    except IndexError:
        type_tag = None

    # Now remove all other type-tags
    for type_sub in [NUMBER_SUB, BOOL_SUB, TABLE_SUB, ARRAY_SUB]:
        input_string = input_string.replace(type_sub, "")

    # Disassemble and rebuild the input string, with substitutions processed
    # in each element in turn
    return_str = ""
    for element in split_delimited_string(
        input_string, opening_delimiter, closing_delimiter
    ):
        if element.startswith(opening_delimiter):
            return_str += process_untyped_variable_substitutions(
                element, opening_delimiter, closing_delimiter
            )
        else:
            return_str += element

    if type_tag is None:
        return return_str
    else:
        # Return the requested type
        return process_typed_variable_substitution(type_tag, return_str)


def process_untyped_variable_substitutions(
    input_string: Optional[str],
    opening_delimiter: str,
    closing_delimiter: str,
) -> Optional[str]:
    """
    Apply untyped variable substitutions to a supplied input string,
    including applying default values if present and required.
    Uses recursion to process variables from the innermost level outwards.
    """
    if input_string is None:
        return None

    # Check if there are inner variables
    undelimited_input_string = remove_outer_delimiters(
        input_string, opening_delimiter, closing_delimiter
    )
    if (
        opening_delimiter in undelimited_input_string
        and closing_delimiter in undelimited_input_string
    ):
        # Recursive call to resolve innermost variables first
        processed_string = ""
        for element in split_delimited_string(
            undelimited_input_string, opening_delimiter, closing_delimiter
        ):
            processed_string += process_untyped_variable_substitutions(
                element, opening_delimiter, closing_delimiter
            )
        input_string = opening_delimiter + processed_string + closing_delimiter

    # Perform initial substitutions from the substitutions dictionary; this
    # will not substitute variables that have default values
    for substitution, value in VARIABLE_SUBSTITUTIONS.items():
        input_string = input_string.replace(
            f"{opening_delimiter}{substitution}{closing_delimiter}", str(value)
        )

    # Create list of variable substitutions with their default values
    substitutions_with_defaults = re.findall(
        f"{opening_delimiter}.*" + DEFAULT_VAR_SEPARATOR + f".*{closing_delimiter}",
        input_string,
    )
    default_value_substitutions = []  # List of (variable_name, default_value)
    for substitution in substitutions_with_defaults:
        variable_default = remove_outer_delimiters(
            substitution, opening_delimiter, closing_delimiter
        ).split(DEFAULT_VAR_SEPARATOR)
        if (
            variable_default[0] == ""
            or variable_default[1] == ""
            or len(variable_default) != 2
        ):
            raise Exception(
                f"Malformed '<variable>:=<default>' substitution: '{substitution}'"
            )
        default_value_substitutions.append(variable_default)

    # Remove default variable values if present (i.e., remove ':=<default>')
    input_string = re.sub(
        DEFAULT_VAR_SEPARATOR + f".*{closing_delimiter}",
        f"{closing_delimiter}",
        input_string,
    )

    # Repeat substitutions from the substitutions dictionary, now that defaults
    # have been removed
    for substitution, value in VARIABLE_SUBSTITUTIONS.items():
        input_string = input_string.replace(
            f"{opening_delimiter}{substitution}{closing_delimiter}", str(value)
        )

    # Perform default substitutions for variables that remain unpopulated;
    # allows for multiple variables with the same name, but with different
    # default values
    for var_name, default_value in default_value_substitutions:
        input_string = input_string.replace(
            f"{opening_delimiter}{var_name}{closing_delimiter}",
            str(default_value),
            1,
        )

    return input_string


def process_typed_variable_substitution(
    type_string: str, input_string: str
) -> Optional[Union[str, int, bool, float, List, Dict]]:
    """
    Process a single typed substitution, returning the appropriate type.
    Assumes there is a substitution present.
    """
    if type_string == NUMBER_SUB:
        try:
            return int(input_string)
        except ValueError:
            try:
                return float(input_string)
            except ValueError:
                raise Exception(
                    f"Non-number used in variable number substitution: '{input_string}'"
                )

    if type_string == BOOL_SUB:
        if input_string.lower() == "true":
            return True
        if input_string.lower() == "false":
            return False
        raise Exception(
            f"Non-boolean used in variable boolean substitution: '{input_string}'"
        )

    if type_string == ARRAY_SUB:
        try:
            return_value = literal_eval(input_string)
            if not isinstance(return_value, List):
                raise Exception("Not an array/list")
            return return_value
        except Exception as e:
            raise Exception(
                f"Property cannot be parsed as an array: '{input_string}' ({e})"
            )

    if type_string == TABLE_SUB:
        try:
            return_value = literal_eval(input_string)
            if not isinstance(return_value, Dict):
                raise Exception("Not a table/dict")
            return return_value
        except Exception as e:
            raise Exception(
                f"Property cannot be parsed as a table: '{input_string}' ({e})"
            )


def load_json_file_with_variable_substitutions(
    filename: str, prefix: str = "", postfix: str = ""
) -> Dict:
    """
    Takes a JSON filename and returns a dictionary with its variable
    substitutions processed.
    """
    with open(filename, "r") as f:
        file_contents = f.read()
    file_contents = process_variable_substitutions_in_file_contents(
        file_contents, prefix=prefix, postfix=postfix
    )
    return json_loads(file_contents)


def load_jsonnet_file_with_variable_substitutions(
    filename: str, prefix: str = "", postfix: str = ""
) -> Dict:
    """
    Takes a Jsonnet filename and returns a dictionary with its variable
    substitutions processed.
    """
    check_jsonnet_import()
    from _jsonnet import evaluate_file

    with VariableSubstitutedJsonnetFile(
        filename=filename, prefix=prefix, postfix=postfix
    ) as preprocessed_filename:
        dict_data = json_loads(evaluate_file(preprocessed_filename))

    # Secondary processing after Jsonnet expansion
    process_variable_substitutions_in_dict_insitu(dict_data, prefix, postfix)

    if ARGS_PARSER.jsonnet_dry_run:
        print_log("Dry-run: Printing Jsonnet to JSON conversion")
        print_json(dict_data)
        print_log("Dry run: Complete")
        exit(0)

    return dict_data


def load_toml_file_with_variable_substitutions(
    filename: str, prefix: str = "", postfix: str = ""
) -> Dict:
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

    # Repeat processing to resolve variables
    for _ in range(NESTED_DEPTH):
        process_variable_substitutions_in_dict_insitu(
            config, prefix=prefix, postfix=postfix
        )

    return config


def process_variable_substitutions_in_file_contents(
    file_contents: str, prefix: str = "", postfix: str = ""
) -> str:
    """
    Process substitutions in the raw contents of a complete file.
    """
    v_expressions = set(
        re.findall(
            prefix + f"{VAR_OPENING_DELIMITER}.*{VAR_CLOSING_DELIMITER}" + postfix,
            file_contents,
        )
    )

    for v_expression in v_expressions:
        replacement_expression = process_variable_substitutions(
            v_expression, prefix=prefix, postfix=postfix
        )
        if isinstance(replacement_expression, str):
            file_contents = file_contents.replace(v_expression, replacement_expression)
        else:
            # If the replacement is a number, a boolean, a table, or an array,
            # we need to remove the enclosing quotes when we substitute, and
            # also ensure that lower case 'false' & 'true' are used.
            # Account for both double and single quotes (for Jsonnet support).
            file_contents = file_contents.replace(
                f'"{v_expression}"', str(replacement_expression).lower()
            )
            file_contents = file_contents.replace(
                f"'{v_expression}'", str(replacement_expression).lower()
            )

    return file_contents


class VariableSubstitutedJsonnetFile:
    """
    The jsonnet 'evaluate_file' function will only operate on files,
    not strings, so this context manager class will create a
    temporary, variable-processed file that can be used by the
    evaluator, then deleted.
    """

    def __init__(self, filename: str, prefix: str = "", postfix: str = ""):
        self.filename = filename
        self.prefix = prefix
        self.postfix = postfix

    def __enter__(self) -> str:
        """
        Return the filename of the temporary variable-processed
        jsonnet file.
        """
        with open(self.filename, "r") as file:
            file_contents = file.read()
        processed_file_contents: str = process_variable_substitutions_in_file_contents(
            file_contents, self.prefix, self.postfix
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(processed_file_contents)
        self.temp_filename: str = temp_file.name
        return self.temp_filename

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.temp_filename)
