import pytest
from cli_test_helpers import shell

from yellowdog_cli.utils.settings import (
    ET_ALLOWANCES,
    ET_COMPUTE_REQUIREMENT_TEMPLATES,
    ET_COMPUTE_REQUIREMENTS,
    ET_COMPUTE_SOURCE_TEMPLATES,
    ET_GROUPS,
    ET_IMAGE_FAMILIES,
    ET_KEYRINGS,
    ET_PERMISSIONS,
    ET_ROLES,
    ET_WORK_REQUIREMENTS,
    ET_WORKER_POOLS,
)


@pytest.mark.system
@pytest.mark.parametrize(
    "cmd",
    [
        "yd-list --help",
        f"yd-list {ET_ALLOWANCES} -n='' -t=''",
        f"yd-list {ET_COMPUTE_REQUIREMENT_TEMPLATES} -n='' -t=''",
        f"yd-list {ET_IMAGE_FAMILIES} -n='' -t=''",
        f"yd-list {ET_KEYRINGS} -n='' -t=''",
        f"yd-list {ET_COMPUTE_SOURCE_TEMPLATES} -n='' -t=''",
        f"yd-list {ET_WORKER_POOLS} -n='' -t=''",
        f"yd-list {ET_COMPUTE_REQUIREMENTS} -n='' -t=''",
        f"yd-list {ET_WORK_REQUIREMENTS} -n='' -t=''",
        f"yd-list {ET_GROUPS} -n='' -t=''",
        f"yd-list {ET_PERMISSIONS} -n='' -t=''",
        f"yd-list {ET_ROLES} -n='' -t=''",
    ],
)
def test_list(cmd):
    assert shell(cmd).exit_code == 0
