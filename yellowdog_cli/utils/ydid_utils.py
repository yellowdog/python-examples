"""
Helper utilities for YDIDs.
"""

from enum import Enum
from typing import Optional


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


def get_ydid_type(ydid: Optional[str]) -> Optional[YDIDType]:
    """
    Find the type of a YellowDog ID.
    """
    if ydid is None or not ydid.startswith("ydid:"):
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
