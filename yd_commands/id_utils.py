"""
Helper utilities for YDIDs.
"""

from enum import Enum
from typing import Optional


class YDIDType(Enum):
    WORK_REQ = "Work Requirement"
    WORKER_POOL = "Worker Pool"
    COMPUTE_REQ = "Compute Requirement"


def get_ydid_type(ydid: str) -> Optional[YDIDType]:
    """
    Find the type of a YDID. Not an exhaustive list yet.
    """
    if ":workreq:" in ydid:
        return YDIDType.WORK_REQ
    elif ":wrkrpool:" in ydid:
        return YDIDType.WORKER_POOL
    elif ":compreq:" in ydid:
        return YDIDType.COMPUTE_REQ
    else:
        return None
