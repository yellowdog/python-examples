"""
General utility functions.
"""
import re
from os.path import join, normpath, relpath
from random import randint
from typing import Optional
from urllib.parse import urlparse

from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)

from yd_commands.config_types import NAMESPACE_SEPARATOR
from yd_commands.variables import UTCNOW


def unpack_namespace_in_prefix(namespace: str, prefix: str) -> (str, str):
    """
    Allow the prefix to include the namespace, which can override the supplied
    namespace. Return the unpacked (namespace, prefix) tuple.
    """
    elems = prefix.split(NAMESPACE_SEPARATOR)
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


PREVIOUS_ID = ""


def generate_id(prefix: str, max_length: int = 60) -> str:
    """
    Add a UTC timestamp and check length. Mitigate against duplicates.
    """
    global PREVIOUS_ID

    generated_id = prefix + UTCNOW.strftime("_%y%m%d-%H%M%S")

    if generated_id == PREVIOUS_ID:
        generated_id = generated_id + f"-{randint(0, 9)}"
    PREVIOUS_ID = generated_id

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