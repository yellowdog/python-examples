"""
User interaction processing
"""

from os import getenv
from typing import List, Optional, Set

from yellowdog_client import PlatformClient

from yd_commands.args import ARGS_PARSER
from yd_commands.object_utilities import Item
from yd_commands.printing import (
    CONSOLE,
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

# Environment variable to use --yes by default
# Set to any non-empty string
YD_YES = "YD_YES"


def select(
    client: PlatformClient,
    objects: List[Item],
    parent: Optional[Item] = None,
    override_quiet: bool = False,
    single_result: bool = False,
    showing_all: bool = False,
) -> List[Item]:
    """
    Print a numbered list of objects.
    Manually select objects from a list if --interactive is set.
    Return the list of objects.
    """

    if len(objects) == 0:
        return objects

    objects = sorted_objects(objects)

    if not ARGS_PARSER.quiet or override_quiet or ARGS_PARSER.interactive:
        print_numbered_object_list(
            client, objects, override_quiet=override_quiet, showing_all=showing_all
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
        input_string = (
            "Please select an item number or press <Return> to cancel:"
            if single_result
            else (
                "Please select items (e.g.: 1,2,4-7 / *) or press <Return> to cancel:"
            )
        )
        selector_string = CONSOLE.input(print_string(input_string) + " ")
        if selector_string == "":  # A quirk of Rich?
            print()
        if selector_string.strip() == "*":
            selector_string = f"1-{len(objects)}"
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
                print_error(f"'{selector}' is not a valid selection")
                error_flag = True
        if error_flag:
            continue
        elif len(selector_set) == 0:
            break
        elif single_result and len(selector_set) != 1:
            print_error("please enter a single item number")
            continue
        else:
            break

    selected_list = sorted(list(selector_set))
    if len(selected_list) > 0:
        if not single_result:
            if len(selected_list) > 20:
                display_selections = (
                    ", ".join([str(x) for x in selected_list[:10]])
                    + " ... "
                    + ", ".join([str(x) for x in selected_list[-8:]])
                )
            else:
                display_selections = ", ".join([str(x) for x in selected_list])
            print_log(f"Selected item number(s): {display_selections}")
    else:
        print_log("No items selected")

    return [objects[x - 1] for x in selected_list]


def confirmed(msg: str) -> bool:
    """
    Confirm an action.
    """
    # Confirmed on the command line?
    if ARGS_PARSER is not None and ARGS_PARSER.yes:
        print_log("Action proceeding without user confirmation")
        return True

    # Confirmed using the environment variable?
    yd_yes = getenv(YD_YES, "")
    if yd_yes != "":
        print_log(f"'{YD_YES}={yd_yes}': Action proceeding without user confirmation")
        return True

    # Seek user confirmation
    while True:
        response = CONSOLE.input(print_string(f"{msg} (y/N):") + " ")
        if response == "":  # Seems to be a quirk of Rich
            print()
        if response.lower() in ["y", "yes"]:
            print_log("Action confirmed by user")
            return True
        elif response.lower() in ["n", "no", ""]:
            print_log("Action cancelled by user")
            return False
