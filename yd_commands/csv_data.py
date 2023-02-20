"""
Module for handling Task data supplied in a CSV file
"""

import csv
import re
from ast import literal_eval
from collections import OrderedDict
from json import load as json_load
from typing import Dict, List, Optional

from toml import load as toml_load

from yd_commands.args import ARGS_PARSER
from yd_commands.config import ConfigWorkRequirement
from yd_commands.config_keys import *
from yd_commands.mustache import (
    BOOL_SUB,
    NUMBER_SUB,
    load_jsonnet_file_with_mustache_substitutions,
    process_mustache_substitutions,
)
from yd_commands.printing import print_json, print_log


class CSVTaskData:
    """
    A class for reading and storing CSV data
    """

    def __init__(self, csv_filename: str):
        """
        Load the data from the CSV file; validate row lengths
        """
        self._csv_data = []
        row_length = None

        with open(csv_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",", skipinitialspace=True)
            for row_number, row in enumerate(csv_reader):
                if row_length is None:
                    row_length = len(row)
                else:
                    if len(row) != row_length:
                        raise Exception(
                            f"Malformed CSV file (row {row_number + 1}): "
                            "all rows must have the same number of items"
                        )
                self._csv_data.append(row)

        self._index = 0
        self._total_tasks = len(self._csv_data) - 1

    def __iter__(self):
        return self

    @property
    def var_names(self) -> List[str]:
        """
        Return the list of headings (variable names)
        """
        return self._csv_data[0]

    def __next__(self):
        """
        Iterate through the task data rows
        """
        if self.remaining_tasks == 0:
            raise StopIteration
        self._index += 1
        return self._csv_data[self._index]

    def reset(self):
        """
        Rewind the list of Tasks to the beginning
        """
        self._index = 0

    @property
    def total_tasks(self):
        return self._total_tasks

    @property
    def remaining_tasks(self):
        return self._total_tasks - self._index


class CSVDataCache:
    """
    Caches CSV data to prevent multiple loads of the same CSV file
    """

    def __init__(self, max_entries: Optional[int] = None):
        """
        'max_entries' limits the size of the cache.
        - Use default 'None' for unlimited caching
        - Set to zero to disable caching
        """
        self._max_entries: Optional[int] = max_entries
        self._csv_task_data_objects: OrderedDict[str, CSVTaskData] = OrderedDict()

    def get_csv_task_data(self, csv_filename: str) -> CSVTaskData:
        csv_task_data = self._csv_task_data_objects.get(csv_filename, None)
        if csv_task_data:  # Cache hit
            csv_task_data.reset()
        else:  # Cache miss
            if self._max_entries is not None:
                if (
                    len(self._csv_task_data_objects) == self._max_entries
                    and len(self._csv_task_data_objects) > 0
                ):
                    self._csv_task_data_objects.popitem(last=False)
            csv_task_data = CSVTaskData(csv_filename)
            if self._max_entries != 0:
                self._csv_task_data_objects[csv_filename] = csv_task_data
        return csv_task_data


# Singleton instance of the CSVDataCache class
CSV_DATA_CACHE = CSVDataCache(max_entries=2)


def load_json_file_with_csv_task_expansion(
    json_file: str, csv_files: List[str]
) -> Dict:
    """
    Load a JSON file, expanding its Task lists using data from CSV
    files. Return the expanded and Mustache-processed Work Requirement data.
    """

    with open(json_file, "r") as f:
        wr_data = json_load(f)

    return perform_csv_task_expansion(wr_data, csv_files)


def load_jsonnet_file_with_csv_task_expansion(
    jsonnet_file: str, csv_files: List[str]
) -> Dict:
    """
    Load a Jsonnet file, expanding its Task lists using data from CSV
    files. Return the expanded and Mustache-processed Work Requirement data.
    """

    wr_data = load_jsonnet_file_with_mustache_substitutions(jsonnet_file)
    return perform_csv_task_expansion(wr_data, csv_files)


def load_toml_file_with_csv_task_expansion(
    toml_file: str, csv_files: List[str]
) -> Dict:
    """
    Load a TOML file Work Requirement, expanding its Task lists using data
    from CSV files. Return the expanded and Mustache-processed Work Requirement
    data.
    """

    with open(toml_file, "r") as f:
        wr_data = toml_load(f)

    return perform_csv_task_expansion(wr_data, csv_files)


def perform_csv_task_expansion(wr_data: Dict, csv_files: List[str]) -> Dict:
    """
    Expand a Work Requirement using CSV data.
    """
    if len(wr_data[TASK_GROUPS]) > len(csv_files):
        print_log(
            f"Note: Number of Task Groups ({len(wr_data[TASK_GROUPS])}) "
            f"in Work Requirement is greater than number of CSV files "
            f"({len(csv_files)})"
        )

    if len(csv_files) > len(wr_data[TASK_GROUPS]):
        raise Exception("Number of CSV files exceeds number of Task Groups")

    for counter, csv_file in enumerate(csv_files):
        csv_file, index = get_csv_file_index(csv_file, wr_data[TASK_GROUPS])
        if index is None:
            index = counter

        task_group = wr_data[TASK_GROUPS][index]
        print_log(
            f"Loading CSV Task data for Task Group {index + 1} from: '{csv_file}'"
        )
        if len(wr_data[TASK_GROUPS][index][TASKS]) != 1:
            raise Exception(
                f"Task Group {index + 1} must have only a single (prototype) Task "
                "when using CSV file for data"
            )

        csv_data = CSV_DATA_CACHE.get_csv_task_data(csv_file)
        task_prototype = task_group[TASKS][0]

        if not substitions_present(csv_data.var_names, str(task_prototype)):
            print_log(
                f"Warning: No CSV substitutions to apply to Task Group "
                f"{index + 1}; not expanding Task list"
            )
            continue

        generated_task_list = []
        for task_data in csv_data:
            generated_task_list.append(
                csv_mustache_substitution(task_prototype, csv_data.var_names, task_data)
            )
        task_group[TASKS] = generated_task_list
        print_log(f"Generated {len(generated_task_list)} Task(s) from CSV data")

    if ARGS_PARSER.process_csv_only:
        print_log("Displaying CSV substitutions only:")
        print_json(wr_data)
        exit(0)

    # Process remaining substitutions
    process_mustache_substitutions(wr_data)
    return wr_data


def csv_mustache_substitution(
    task_prototype: Dict, csv_var_names: List, task_data: List
) -> Dict:
    """
    Helper function to substitute using CSV data only. Leave all other
    substitutions unchanged.
    """
    subs_dict = {var_name: task_data[i] for i, var_name in enumerate(csv_var_names)}
    new_task = str(task_prototype)
    for var_name, value in subs_dict.items():
        new_task = make_string_substitutions(new_task, var_name, value)
    return literal_eval(new_task)  # Convert back from string


def make_string_substitutions(input: str, var_name: str, value: str) -> str:
    """
    Helper function to make string substitutions for CSV variables only.
    """
    input = input.replace(f"{{{{{var_name}}}}}", value)

    num_sub_str = f"{{{{{NUMBER_SUB}{var_name}}}}}"
    if num_sub_str in input:
        try:
            float(value)
        except ValueError:
            raise Exception(f"Invalid number substitution in CSV: '{value}'")
        input = input.replace(f"'{num_sub_str}'", value)

    bool_sub_str = f"{{{{{BOOL_SUB}{var_name}}}}}"
    if bool_sub_str in input:
        if value.lower() == "true":
            value = "True"
        elif value.lower() == "false":
            value = "False"
        else:
            raise Exception(f"Invalid Boolean substitution in CSV: '{value}'")
        input = input.replace(f"'{bool_sub_str}'", value)

    return input


USED_FILE_INDEXES = []


def get_csv_file_index(
    csv_filename: str, task_groups: List[Dict]
) -> [str, Optional[int]]:
    """
    Check if the CSV filename ends in an integer index (':<integer>'),
    or in a Task Group name (':<task_group_name>').
    If so, return the filename with the index stripped, and the index
    integer (zero-based).
    """

    # Task Group number matching
    matches = re.findall(":\d+$", csv_filename)
    if len(matches) == 1:
        index = int(matches[0][1:])
        if not 0 < index <= len(task_groups):
            raise Exception(
                f"CSV file Task Group index '{index}' is outside Task Group range"
            )
        if index in USED_FILE_INDEXES:
            raise Exception(f"CSV file Task Group index '{index}' used more than once")
        USED_FILE_INDEXES.append(index)
        return csv_filename.replace(matches[0], ""), index - 1

    # Task Group name matching; filter on valid name patterns
    matches = re.findall(":[a-z][a-z0-9_-]+$", csv_filename)
    if len(matches) == 1:
        for index, task_group in enumerate(task_groups):
            try:
                if matches[0][1:] == task_group[NAME]:
                    return csv_filename.replace(matches[0], ""), index
            except KeyError:
                pass
        else:
            raise Exception(f"No matches for Task Group name '{matches[0][1:]}'")

    # Invalid Task Group naming?
    split_name = csv_filename.split(":")
    if len(split_name) > 1:
        print_log(
            f"Warning: Possible invalid Task Group name/number '{split_name[-1:]}'?"
        )

    return csv_filename, None


def substitions_present(var_names: List[str], task_prototype: str) -> bool:
    """
    Check if there are any CSV substitutions present in the Task prototype.
    """
    return (
        any(f"{{{{{var_name}}}}}" in task_prototype for var_name in var_names)
        or any(
            f"{{{{{NUMBER_SUB}{var_name}}}}}" in task_prototype
            for var_name in var_names
        )
        or any(
            f"{{{{{BOOL_SUB}{var_name}}}}}" in task_prototype for var_name in var_names
        )
    )


def csv_expand_toml_tasks(config_wr: ConfigWorkRequirement, csv_file: str) -> Dict:
    """
    When there's a CSV file specified, but no JSON file, create the expanded
    list of Tasks using the CSV data.
    """
    wr_data = {TASK_GROUPS: [{TASKS: [{}]}]}
    task_proto = wr_data[TASK_GROUPS][0][TASKS][0]
    csv_data = CSV_DATA_CACHE.get_csv_task_data(csv_file.split(":")[0])
    # Populate properties that can be set at Task level only
    for config_value, config_name in [
        (config_wr.args, ARGS),
        (config_wr.bash_script, BASH_SCRIPT),
        (config_wr.capture_taskoutput, CAPTURE_TASKOUTPUT),
        (config_wr.docker_env, DOCKER_ENV),
        (config_wr.docker_password, DOCKER_PASSWORD),
        (config_wr.docker_username, DOCKER_USERNAME),
        (config_wr.env, ENV),
        (config_wr.executable, EXECUTABLE),
        (config_wr.flatten_input_paths, FLATTEN_PATHS),
        (config_wr.input_files, INPUT_FILES),
        (config_wr.optional_inputs, OPTIONAL_INPUTS),
        (config_wr.output_files, OUTPUT_FILES),
        (config_wr.output_files_required, OUTPUT_FILES_REQUIRED),
        (config_wr.task_data, TASK_DATA),
        (config_wr.task_data_file, TASK_DATA_FILE),
        (config_wr.task_name, TASK_NAME),
        (config_wr.task_type, TASK_TYPE),
        (config_wr.upload_files, UPLOAD_FILES),
        (config_wr.verify_at_start, VERIFY_AT_START),
        (config_wr.verify_wait, VERIFY_WAIT),
    ]:
        if config_value is not None and substitions_present(
            csv_data.var_names, str(config_value)
        ):
            task_proto[config_name] = config_value

    return perform_csv_task_expansion(wr_data, [csv_file])
