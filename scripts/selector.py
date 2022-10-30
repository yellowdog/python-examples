"""
Interactive selection from a list of objects
"""

from typing import List, Set, TypeVar

from yellowdog_client.model import (
    ComputeRequirementSummary,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

from common import print_log

try:
    import readline
except ImportError:
    pass

Item = TypeVar(
    "Item", ComputeRequirementSummary, WorkerPoolSummary, WorkRequirementSummary
)


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

    def in_range(item: int) -> bool:
        if 1 <= item <= len(objects):
            return True
        else:
            print_log(f"Error: '{i}' is out of range")
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
    print()

    returned_objects: List[WorkRequirementSummary] = []
    for item in selector_set:
        returned_objects.append(objects[item - 1])
    return returned_objects
