"""
Helper utilities for YDIDs.
"""

import re
from enum import Enum


class YDIDType(Enum):
    ALLOWANCE = "Allowance"
    APPLICATION = "Application"
    COMPUTE_REQUIREMENT = "Compute Requirement"
    COMPUTE_REQUIREMENT_TEMPLATE = "Compute Requirement Template"
    COMPUTE_SOURCE = "Compute Source"
    COMPUTE_SOURCE_TEMPLATE = "Compute Source Template"
    GROUP = "Group"
    IMAGE = "Machine Image"
    IMAGE_FAMILY = "Machine Image Family"
    IMAGE_GROUP = "Machine Image Group"
    KEYRING = "Keyring"
    NODE = "Node"
    ROLE = "Role"
    TASK = "Task"
    TASK_GROUP = "Task Group"
    USER = "User"
    WORKER = "Worker"
    WORKER_POOL = "Worker Pool"
    WORK_REQUIREMENT = "Work Requirement"


def get_ydid_type(ydid: str | None) -> YDIDType | None:
    """
    Find the type of YellowDog ID.
    """
    if not is_valid_ydid(ydid):
        return None

    if ydid.startswith("ydid:workreq:"):
        return YDIDType.WORK_REQUIREMENT
    if ydid.startswith("ydid:taskgrp:"):
        return YDIDType.TASK_GROUP
    if ydid.startswith("ydid:task:"):
        return YDIDType.TASK
    if ydid.startswith("ydid:wrkrpool:"):
        return YDIDType.WORKER_POOL
    if ydid.startswith("ydid:wrkr:"):
        return YDIDType.WORKER
    if ydid.startswith("ydid:compreq:"):
        return YDIDType.COMPUTE_REQUIREMENT
    if ydid.startswith("ydid:compsrc:"):
        return YDIDType.COMPUTE_SOURCE
    if ydid.startswith("ydid:node:"):
        return YDIDType.NODE
    if ydid.startswith("ydid:crt:"):
        return YDIDType.COMPUTE_REQUIREMENT_TEMPLATE
    if ydid.startswith("ydid:cst:"):
        return YDIDType.COMPUTE_SOURCE_TEMPLATE
    if ydid.startswith("ydid:imgfam:"):
        return YDIDType.IMAGE_FAMILY
    if ydid.startswith("ydid:imggrp:"):
        return YDIDType.IMAGE_GROUP
    if ydid.startswith("ydid:image:"):
        return YDIDType.IMAGE
    if ydid.startswith("ydid:keyring:"):
        return YDIDType.KEYRING
    if ydid.startswith("ydid:allow:"):
        return YDIDType.ALLOWANCE
    if ydid.startswith("ydid:app:"):
        return YDIDType.APPLICATION
    if ydid.startswith("ydid:user:"):
        return YDIDType.USER
    if ydid.startswith("ydid:group:"):
        return YDIDType.GROUP
    if ydid.startswith("ydid:role:"):
        return YDIDType.ROLE

    return None


_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_HEX = r"[0-9a-fA-F]+"
_TYPES = (
    "workreq", "taskgrp", "task", "wrkrpool", "wrkr", "compreq", "compsrc",
    "node", "crt", "cst", "imgfam", "imggrp", "image", "keyring", "allow",
    "app", "user", "group", "role",
)
_YDID_RE = re.compile(
    rf"^ydid:(?:{'|'.join(_TYPES)}):{_HEX}(?::{_HEX})?:{_UUID}(?::\d+)*$"
)


def is_valid_ydid(ydid: str | None) -> bool:
    """
    Return True if the YDID is well-formed.
    """
    if ydid is None:
        return False
    return bool(_YDID_RE.match(ydid))
