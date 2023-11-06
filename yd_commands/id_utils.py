"""
Helper utilities for YDIDs.
"""

from enum import Enum
from typing import Optional


class YDIDType(Enum):
    WORK_REQ = "Work Requirement"
    WORKER_POOL = "Worker Pool"
    COMPUTE_REQ = "Compute Requirement"
    CR_TEMPLATE = "Compute Requirement Template"
    IMAGE_FAMILY = "Image Family"


def get_ydid_type(ydid: str) -> Optional[YDIDType]:
    """
    Find the type of a YDID. Not an exhaustive list yet.
    """
    if ydid is None:
        return None
    elif "ydid:workreq:" in ydid:
        return YDIDType.WORK_REQ
    elif "ydid:wrkrpool:" in ydid:
        return YDIDType.WORKER_POOL
    elif "ydid:compreq:" in ydid:
        return YDIDType.COMPUTE_REQ
    elif "ydid:crt:" in ydid:
        return YDIDType.CR_TEMPLATE
    elif "ydid:imgfam:" in ydid:
        return YDIDType.IMAGE_FAMILY
    else:
        return None
