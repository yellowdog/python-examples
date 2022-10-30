"""
Interactive selection from a list of objects,
and check for user confirmation of actions.
"""

from os import getenv
from typing import List, Set, TypeVar

from yellowdog_client.model import (
    ComputeRequirementSummary,
    ObjectPath,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

from common import ARGS_PARSER, print_log

try:
    import readline
except ImportError:
    pass

Item = TypeVar(
    "Item",
    ComputeRequirementSummary,
    ObjectPath,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

# Environment variable to use --proceed-without-confirmation by default
# Set to any non-empty string
YD_NO_CONFIRM = "YD_NO_CONFIRM"


def select(objects: List[Item]) -> List[Item]:
    """
    Manually select objects from a list. Return the list of selected objects.
    """
    print()
    indent = " " * 3
    index_len = len(str(len(objects)))
    objects = sorted(objects, key=lambda x: x.name, reverse=True)
    for index, obj in enumerate(objects):
        print(f"{indent}{str(index + 1).rjust(index_len)} :   {obj.name}")

    def in_range(num: int) -> bool:
        if 1 <= num <= len(objects):
            return True
        else:
            print_log(f"Error: '{num}' is out of range")
            return False

    while True:
        print()
        selector_string = input(
            "Please select items to be deleted (e.g.: 1,2,4-7,9) "
            "or Return for none: "
        )
        selector_list = selector_string.split(",")
        selector_set: Set[int] = set()
        error_flag = False
        for selector in selector_list:
            try:
                if "-" in selector:
                    low, high = selector.split("-")
                    for i in range(int(low), int(high) + 1):
                        if in_range(i):
                            selector_set.add(i)
                        else:
                            error_flag = True
                elif not (selector.isspace() or len(selector) == 0):
                    i = int(selector)
                    if in_range(i):
                        selector_set.add(i)
                    else:
                        error_flag = True
            except ValueError as e:
                print_log(f"Error: '{selector}' is not a valid selection")
                error_flag = True
        if error_flag:
            continue
        else:
            break

    returned_objects: List[Item] = []
    for item in selector_set:
        returned_objects.append(objects[item - 1])
    return returned_objects


def confirmed(msg: str) -> bool:
    """
    Confirm an action.
    """
    # Confirmed on the command line?
    if ARGS_PARSER.yes:
        print_log("Action proceeding without user confirmation")
        return True

    # Confirmed using the environment variable?
    yd_no_confirm = getenv(YD_NO_CONFIRM, "")
    if yd_no_confirm != "":
        print_log(
            f"'{YD_NO_CONFIRM}={yd_no_confirm}': "
            "Action proceeding without user confirmation"
        )
        return True

    # Seek user confirmation
    response = input(f"{msg} (y/N): ")

    if response.lower() == "y":
        print_log("Action confirmed by user")
        return True
    else:
        print_log("Action cancelled by user")
        return False
