"""
User interaction processing
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

# Environment variable to use --no-confirmation by default
# Set to any non-empty string
YD_NO_CONFIRM = "YD_NO_CONFIRM"

TYPE_MAP = {
    "WorkerPool": "Worker Pool",
    "ComputeRequirement": "Compute Requirement",
    "WorkRequirement": "Work Requirement",
    "ObjectPath": "Object Path",
}


def get_type_name(object: Item) -> str:
    """
    Get the display name of an object's type
    """
    type_str = str(type(object))
    for key, value in TYPE_MAP.items():
        if key in type_str:
            return value
    return ""


def print_numbered_object_list(objects: List[Item]) -> None:
    """
    Print a numbered list of objects
    """
    if len(objects) == 0:
        return

    print_log(f"Displaying list of matching {get_type_name(objects[0])}(s):")
    print()
    indent = " " * 3
    index_len = len(str(len(objects)))
    objects = sorted(objects, key=lambda x: x.name)
    for index, obj in enumerate(objects):
        print(f"{indent}{str(index + 1).rjust(index_len)} : {obj.name}")
    print()


def select(objects: List[Item]) -> List[Item]:
    """
    Print a numbered list of objects.
    Manually select objects from a list if --interactive is set.
    Return the list of objects.
    """
    if not ARGS_PARSER.quiet or ARGS_PARSER.interactive:
        print_numbered_object_list(objects)

    if not ARGS_PARSER.interactive:
        return objects

    def in_range(num: int) -> bool:
        if 1 <= num <= len(objects):
            return True
        else:
            print_log(f"Error: '{num}' is out of range")
            return False

    while True:
        selector_string = input(
            "Please select items (e.g.: 1,2,4-7,9) or press <Return> for none: "
        )
        selector_list = selector_string.split(",")
        selector_set: Set[int] = set()
        error_flag = False
        for selector in selector_list:
            try:
                if "-" in selector:
                    low_s, high_s = selector.split("-")
                    low = int(low_s)
                    high = int(high_s)
                    if low > high:
                        raise ValueError
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
            except ValueError:
                print_log(f"Error: '{selector}' is not a valid selection")
                error_flag = True
        if error_flag:
            continue
        else:
            break

    if len(selector_set) > 0:
        print(
            "Selected item number(s): "
            f"{', '.join([str(x) for x in sorted(list(selector_set))])}"
        )

    returned_objects: List[Item] = []
    for item in selector_set:
        returned_objects.append(objects[item - 1])
    return returned_objects


def confirmed(msg: str) -> bool:
    """
    Confirm an action.
    """
    # Confirmed on the command line?
    if ARGS_PARSER.no_confirm:
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
    while True:
        response = input(f"{msg} (y/N): ")
        if response.lower() in ["y", "yes"]:
            print_log("Action confirmed by user")
            return True
        elif response.lower() in ["n", "no", ""]:
            print_log("Action cancelled by user")
            return False
