"""
Common utility functions
"""

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

import toml
from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)


@dataclass
class Config:
    url: str
    key: str
    secret: str
    namespace: str
    name_tag: str
    worker_tags: List[str]
    task_type: str
    bash_script: str
    args: List[str]
    env: Dict
    input_files: List[str]
    output_files: List[str]
    max_retries: int
    task_count: int


def load_config() -> Config:
    """
    Load the config from a TOML file.
    Allow the optional use of a config file supplied on the command line.
    Supply defaults where possible.
    """
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.toml"
    # Load configuration from the config file
    with open(config_file, "r") as f:
        config = toml.load(f)
    return Config(
        url=config.get("URL", "https://portal.yellowdog.co/api"),
        key=config["KEY"],
        secret=config["SECRET"],
        namespace=config["NAMESPACE"],
        name_tag=config["NAME_TAG"],
        worker_tags=config.get("WORKER_TAGS", []),
        task_type=config.get("TASK_TYPE", "bash"),
        bash_script=config["BASH_SCRIPT"],
        args=config.get("ARGS", []),
        env=config.get("BASH_ENV", {}),
        input_files=config.get("INPUT_FILES", []),
        output_files=config.get("OUTPUT_FILES", []),
        max_retries=config.get("MAX_RETRIES", 1),
        task_count=config.get("TASK_COUNT", 1),
    )


def print_log(log_message: str):
    """Placeholder for more sophisticated logging."""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ":", log_message)


def generate_id(prefix: str) -> str:
    """
    Adds a combination of a UTC timestamp plus
    a few random hex characters
    """
    return (
        prefix
        + datetime.utcnow().strftime("_%y%m%dT%H%M%S-")
        + str(uuid4())[:3].upper()
    )


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
