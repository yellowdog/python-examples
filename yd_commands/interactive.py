"""
User interaction processing
"""

from os import getenv
from typing import List, Optional, Set

from yellowdog_client import PlatformClient

from yd_commands.args import ARGS_PARSER
from yd_commands.object_utilities import Item
from yd_commands.printing import (
    print_error,
    print_log,
    print_numbered_object_list,
    print_string,
    sorted_objects,
)

try:
    import readline
except ImportError:
    pass

# Environment variable to use --no-confirmation by default
# Set to any non-empty string
YD_YES = "YD_YES"


def select(
    client: PlatformClient,
    objects: List[Item],
    parent: Optional[Item] = None,
    override_quiet: bool = False,
) -> List[Item]:
    """
    Print a numbered list of objects.
    Manually select objects from a list if --interactive is set.
    Return the list of objects.
    """
    objects = sorted_objects(objects)

    if not ARGS_PARSER.quiet or override_quiet or ARGS_PARSER.interactive:
        print_numbered_object_list(
            client, objects, parent, override_quiet=override_quiet
        )

    if not ARGS_PARSER.interactive:
        return objects

    def in_range(num: int) -> bool:
        if 1 <= num <= len(objects):
            return True
        else:
            print_error(f"'{num}' is out of range")
            return False

    while True:
        selector_string = input(
            print_string(
                "Please select items (e.g.: 1,2,4-7) or press <Return> for none: "
            )
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
                print(print_string(f"Error: '{selector}' is not a valid selection"))
                error_flag = True
        if error_flag:
            continue
        else:
            break

    selected_list = sorted(list(selector_set))
    if len(selected_list) > 0:
        print(
            print_string(
                f"Selected item number(s): "
                f"{', '.join([str(x) for x in selected_list])}"
            )
        )
    else:
        print_log("No items selected")

    return [objects[x - 1] for x in selected_list]


def confirmed(msg: str) -> bool:
    """
    Confirm an action.
    """
    # Confirmed on the command line?
    if ARGS_PARSER.yes:
        print_log("Action proceeding without user confirmation")
        return True

    # Confirmed using the environment variable?
    yd_yes = getenv(YD_YES, "")
    if yd_yes != "":
        print_log(f"'{YD_YES}={yd_yes}': Action proceeding without user confirmation")
        return True

    # Seek user confirmation
    while True:
        response = input(print_string(f"{msg} (y/N): "))
        if response.lower() in ["y", "yes"]:
            print_log("Action confirmed by user")
            return True
        elif response.lower() in ["n", "no", ""]:
            print_log("Action cancelled by user")
            return False
