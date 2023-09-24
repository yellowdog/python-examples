"""
General utility functions.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from os.path import join, normpath, relpath
from typing import List, Optional
from urllib.parse import urlparse

from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)

from yd_commands.settings import NAMESPACE_PREFIX_SEPARATOR

UTCNOW = datetime.utcnow()


def unpack_namespace_in_prefix(namespace: str, prefix: str) -> (str, str):
    """
    Allow the prefix to include the namespace, which can override the supplied
    namespace. Return the unpacked (namespace, prefix) tuple.
    """
    elems = prefix.split(NAMESPACE_PREFIX_SEPARATOR)
    if len(elems) == 1:
        return namespace, prefix.lstrip("/")
    if len(elems) == 2:
        return elems[0] if elems[0] != "" else namespace, elems[1].lstrip("/")


def pathname_relative_to_config_file(config_file_dir: str, file: str) -> str:
    """
    Find the pathname of a file relative to the location
    of the config file
    """
    return normpath(relpath(join(config_file_dir, file)))


def generate_id(prefix: str = "", max_length: int = 60) -> str:
    """
    Add a UTC timestamp and check length.
    """
    # Include seconds to two decimals
    generated_id = prefix + UTCNOW.strftime("_%y%m%d-%H%M%S%f")[:-4]
    if len(generated_id) > max_length:
        raise Exception(
            f"Error: Generated ID '{generated_id}' would exceed "
            f"maximum length ({max_length})"
        )
    return generated_id


# Utility functions for creating links to YD entities
def link_entity(base_url: str, entity: object) -> str:
    entity_type = type(entity)
    return link(
        base_url,
        "#/%s/%s" % ((entities.get(entity_type)), entity.id),
        camel_case_split(entity_type.__name__).upper(),
    )


def link(base_url: str, url_suffix: str = "", text: Optional[str] = None) -> str:
    url_parts = urlparse(base_url)
    base_url = url_parts.scheme + "://" + url_parts.netloc
    url = base_url + "/" + url_suffix
    if not text:
        text = url
    if text == url:
        return url
    else:
        return "%s (%s)" % (text, url)


def camel_case_split(value: str) -> str:
    return " ".join(re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", value))


entities = {
    ConfiguredWorkerPool: "workers",
    ProvisionedWorkerPool: "workers",
    WorkRequirement: "work",
    ComputeRequirement: "compute",
}


def add_batch_number_postfix(name: str, batch_number: int, num_batches: int) -> str:
    """
    Generate a name using batch details.
    """
    if num_batches > 1:
        name += "_" + str(batch_number + 1).zfill(len(str(num_batches)))
    return name


#
# Functions for handling delimited variables within strings.
#
@dataclass(order=True)
class Substring:
    start: int
    end: int


def get_delimited_string_boundaries(
    input_string: str,
    opening_delimiter: str,
    closing_delimiter: str,
) -> List[Substring]:
    """
    Given an input string and a pair of opening and closing delimiter strings,
    find the list of start and end indices for the top-level strings enclosed
    by the opening and closing delimiters.

    For example:
        if input_string = "abc {{{{x}}_hello}} 234 {{{{world}}}}",
        and opening_delimiter = "{{", closing_delimiter = "}}",
        the function will return Substring objects: [(4, 19), (24, 37)]

    Opening and closing delimiters must be balanced across the entire
    input_string, otherwise an exception will be raised.
    """
    openings = [(x.span()[0], 1) for x in re.finditer(opening_delimiter, input_string)]
    closings = [(x.span()[0], -1) for x in re.finditer(closing_delimiter, input_string)]

    mismatched_delimiters_exception = Exception(
        f"Mismatched variable delimiters ('{opening_delimiter}', '{closing_delimiter}')"
        f" in '{input_string}'"
    )

    if len(openings) != len(closings):
        raise mismatched_delimiters_exception

    slate = 0
    start = None
    substrings: List[Substring] = []

    for boundary in sorted(openings + closings):
        slate += boundary[1]
        if slate < 0:
            raise mismatched_delimiters_exception
        if slate == 1 and start is None:
            start = boundary[0]
        elif slate == 0:
            substrings.append(
                Substring(start=start, end=boundary[0] + len(closing_delimiter))
            )
            start = None

    if slate > 0:
        raise mismatched_delimiters_exception

    return substrings


def split_delimited_string(
    s: str, opening_delimiter: str, closing_delimiter: str
) -> List[str]:
    """
    This function takes a string containing delimited sections and breaks it
    into a list of strings, including the non-delimited sections.
    Delimiters are retained.

    For example:
      when called with ("one{{two}}three{{{{four}}}}five", "{{", "}}")
      the result is: ['one', '{{two}}', 'three', '{{{{four}}}}', 'five']
    """

    # Get delimited boundaries
    delimited_boundaries: List[Substring] = get_delimited_string_boundaries(
        s, opening_delimiter, closing_delimiter
    )

    if len(delimited_boundaries) == 0:
        return [s]

    # Get non-delimited boundaries (i.e., the gaps)
    non_delimited_boundaries: List[Substring] = []
    if delimited_boundaries[0].start > 0:  # Non-variable text at start?
        non_delimited_boundaries.insert(
            0, Substring(start=0, end=delimited_boundaries[0].start)
        )
    for index in range(len(delimited_boundaries) - 1):
        non_delimited_boundaries.insert(
            index + 1,
            (
                Substring(
                    start=delimited_boundaries[index].end,
                    end=delimited_boundaries[index + 1].start,
                )
            ),
        )
    # Non-variable text at end?
    final_boundary: int = delimited_boundaries[len(delimited_boundaries) - 1].end
    if len(s) > final_boundary:
        non_delimited_boundaries.append(Substring(start=final_boundary, end=len(s)))

    return [
        s[boundary.start : boundary.end]
        for boundary in sorted(non_delimited_boundaries + delimited_boundaries)
    ]


def remove_outer_delimiters(
    input_string: str, opening_delimiter: str, closing_delimiter: str
) -> str:
    """
    Remove the outermost delimiters from a string.
    There is no checking for a well-formed string.
    """
    # The string and the closing delimiter must be reversed ([::-1]) for
    # removal, then re-reversed
    return input_string.replace(f"{opening_delimiter}", "", 1)[::-1].replace(
        f"{closing_delimiter[::-1]}", "", 1
    )[::-1]
