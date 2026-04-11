"""
System tests: resource CRUD lifecycle with state verification.

Each test follows the pattern:
    create → yd-list confirms presence → yd-show returns valid JSON
           → remove → yd-list confirms absence

Run with: pytest --run-system tests/test_system_resources.py

Prerequisites: YD_KEY, YD_SECRET (and optionally YD_URL) must be set in the
environment, or a config.toml must be present.
"""

import json

import pytest
from cli_test_helpers import shell

from yellowdog_cli.utils.ydid_utils import YDID

R = "tests/resource-examples"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ydids(list_cmd: str) -> set[str]:
    """Return the set of YDIDs from a 'yd-list --ids-only' call."""
    result = shell(list_cmd)
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith(f"{YDID}:")
    }


def _assert_show(ydid: str) -> None:
    """Assert that yd-show on a YDID exits 0 and returns valid JSON."""
    result = shell(f"yd-show --quiet {ydid}")
    assert result.exit_code == 0, f"yd-show {ydid} failed:\n{result.stdout}"
    json.loads(result.stdout)  # raises ValueError if not valid JSON


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.system
@pytest.mark.parametrize(
    "create_cmd,remove_cmd,name,list_cmd,ids_cmd",
    [
        pytest.param(
            f"yd-create {R}/keyring.json",
            f"yd-remove -y {R}/keyring.json",
            "aaa-test-1",
            "yd-list keyrings -n='' -t=''",
            "yd-list keyrings -D -n='' -t=''",
            id="keyring",
        ),
        pytest.param(
            f"yd-create {R}/namespace.json",
            f"yd-remove -y {R}/namespace.json",
            "delete-me",
            "yd-list namespaces -t=''",
            "yd-list namespaces -D -t=''",
            id="namespace",
        ),
        pytest.param(
            f"yd-create {R}/image-family.json",
            f"yd-remove -y {R}/image-family.json",
            "aaa-test",
            "yd-list image-families -n=pyexamples-pwt -t=''",
            "yd-list image-families -D -n=pyexamples-pwt -t=''",
            id="image_family",
        ),
        pytest.param(
            f"yd-create -y {R}/namespace_policies.json",
            f"yd-remove -y {R}/namespace_policies.json",
            "test_namespace_policy_1",
            "yd-list namespace-policies -t=''",
            "yd-list namespace-policies -D -t=''",
            id="namespace_policy",
        ),
        pytest.param(
            f"yd-create {R}/stringattribute.json",
            f"yd-remove -y {R}/stringattribute.json",
            "user.pwt-test-3",
            "yd-list attribute-definitions -n='' -t=''",
            "yd-list attribute-definitions -D -n='' -t=''",
            id="string_attribute",
        ),
        pytest.param(
            f"yd-create -y {R}/group.json",
            f"yd-remove -y {R}/group.json",
            "aaa",
            "yd-list groups -n='' -t=''",
            "yd-list groups -D -n='' -t=''",
            id="group",
        ),
    ],
)
def test_resource_lifecycle(create_cmd, remove_cmd, name, list_cmd, ids_cmd, cleanup):
    cleanup(remove_cmd)

    before = _ydids(ids_cmd)

    result = shell(create_cmd)
    assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

    result = shell(list_cmd)
    assert result.exit_code == 0
    assert name in result.stdout, f"'{name}' not found in yd-list output"

    new_ydids = _ydids(ids_cmd) - before
    if new_ydids:
        _assert_show(next(iter(new_ydids)))

    result = shell(remove_cmd)
    assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

    result = shell(list_cmd)
    assert result.exit_code == 0
    assert name not in result.stdout, f"'{name}' still present after removal"
