"""
Module for handling Task data supplied in a CSV file
"""

import csv
import re
from ast import literal_eval
from json import load as json_load
from typing import Dict, List, Optional

from yd_commands.config_keys import *
from yd_commands.mustache import BOOL_SUB, NUMBER_SUB, process_mustache_substitutions
from yd_commands.printing import print_log


class CSVTaskData:
    """
    A class for reading and storing CSV data
    """

    def __init__(self, csv_filename: str):
        """
        Load the data from the CSV file; validate row lengths
        """
        with open(csv_filename) as csv_file:
            self._csv_data = []
            row_length = None
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


def load_json_file_with_csv_task_expansion(
    json_file: str, csv_files: List[str]
) -> Dict:
    """
    Load a JSON file, expanding its Task lists using data from CSV
    files. Return the expanded and Mustache-processed Work Requirement data.
    """

    with open(json_file, "r") as f:
        wr_data = json_load(f)

    if len(wr_data[TASK_GROUPS]) > len(csv_files):
        print_log(
            f"Warning: Number of Task Groups ({len(wr_data[TASK_GROUPS])}) "
            f"in Work Requirement is greater than number of CSV files "
            f"({len(csv_files)})"
        )

    if len(csv_files) > len(wr_data[TASK_GROUPS]):
        raise Exception("Number of CSV files exceeds number of Task Groups")

    for i, csv_file in enumerate(csv_files):
        csv_file, index = _get_csv_file_index(csv_file, len(wr_data[TASK_GROUPS]))
        if index is None:
            index = i
        task_group = wr_data[TASK_GROUPS][index]
        print_log(
            f"Loading CSV Task data for Task Group {index + 1} from: '{csv_file}'"
        )
        if len(wr_data[TASK_GROUPS][index][TASKS]) != 1:
            raise Exception(
                f"Task Group {index + 1} must have only a single (prototype) Task "
                "when using CSV file for data"
            )
        csv_data = CSVTaskData(csv_file)
        task_prototype = task_group[TASKS][0]
        generated_task_list = []
        for task_data in csv_data:
            generated_task_list.append(
                _csv_mustache_substitution(
                    task_prototype, csv_data.var_names, task_data
                )
            )
        task_group[TASKS] = generated_task_list
        print_log(f"Generated {len(generated_task_list)} Task(s) from CSV data")

    # Process remaining substitutions
    process_mustache_substitutions(wr_data)
    return wr_data


def _csv_mustache_substitution(
    task_prototype: Dict, csv_var_names: List, task_data: List
) -> Dict:
    """
    Helper function to substitute using CSV data only. Leave all other
    substitutions unchanged.
    """
    subs_dict = {var_name: task_data[i] for i, var_name in enumerate(csv_var_names)}
    new_task = str(task_prototype)
    for var_name, value in subs_dict.items():
        new_task = _make_string_substitutions(new_task, var_name, value)
    return literal_eval(new_task)  # Convert back from string


def _make_string_substitutions(input: str, var_name: str, value: str) -> str:
    """
    Helper function to make string substitutions for CSV variables only.
    """
    input = input.replace(f"{{{{{var_name}}}}}", value)
    input = input.replace(f"'{{{{{NUMBER_SUB}{var_name}}}}}'", value)
    if value.lower() == "true":
        value = "True"
    elif value.lower() == "false":
        value = "False"
    input = input.replace(f"'{{{{{BOOL_SUB}{var_name}}}}}'", value)
    return input


USED_FILE_INDEXES = []


def _get_csv_file_index(
    csv_filename: str, num_task_groups: int
) -> [str, Optional[int]]:
    """
    Check if the CSV filename ends in an integer index (':<integer>).
    If so, return the filename with the index stripped, and the index
    integer (zero-based).
    """
    matches = re.findall(":\d+$", csv_filename)
    if len(matches) != 1:
        return csv_filename, None

    index = int(matches[0][1:])
    if index > num_task_groups:
        raise Exception(
            f"CSV file Task Group index '{index}' exceeds number of Task Groups"
        )
    if index in USED_FILE_INDEXES:
        raise Exception(f"CSV file Task Group index '{index}' used more than once")
    USED_FILE_INDEXES.append(index)
    return csv_filename.replace(matches[0], ""), index - 1
