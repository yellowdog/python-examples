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

RESOURCE_DIR = "tests/resource-examples"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ydids(list_cmd: str) -> set[str]:
    """Return the set of YDIDs from a 'yd-list --ids-only' call."""
    result = shell(list_cmd)
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("ydid:")
    }


def _assert_show(ydid: str) -> None:
    """Assert that yd-show on a YDID exits 0 and returns valid JSON."""
    result = shell(f"yd-show --quiet {ydid}")
    assert result.exit_code == 0, f"yd-show {ydid} failed:\n{result.stdout}"
    json.loads(result.stdout)  # raises ValueError if not valid JSON


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cleanup():
    """
    Safety-net teardown fixture. Tests register cleanup commands by calling
    the yielded function; all are executed in reverse order after the test,
    regardless of whether it passed or failed.
    """
    cmds: list[str] = []
    yield cmds.append
    for cmd in reversed(cmds):
        shell(cmd)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.system
class TestSystemResources:
    # ------------------------------------------------------------------
    # Keyring
    # ------------------------------------------------------------------

    def test_keyring_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/keyring.json"
        name = "aaa-test-1"
        list_cmd = "yd-list -K -n='' -t=''"
        ids_cmd = "yd-list -K -D -n='' -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"

    # ------------------------------------------------------------------
    # Namespace
    # ------------------------------------------------------------------

    def test_namespace_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/namespace.json"
        name = "delete-me"
        list_cmd = "yd-list -M -t=''"
        ids_cmd = "yd-list -M -D -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"

    # ------------------------------------------------------------------
    # Image family
    # ------------------------------------------------------------------

    def test_image_family_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/image-family.json"
        name = "aaa-test"
        namespace = "pyexamples-pwt"
        list_cmd = f"yd-list -I -n={namespace} -t=''"
        ids_cmd = f"yd-list -I -D -n={namespace} -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"

    # ------------------------------------------------------------------
    # Namespace policy
    # ------------------------------------------------------------------

    def test_namespace_policy_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/namespace_policies.json"
        name = "test_namespace_policy_1"
        list_cmd = "yd-list -P -t=''"
        ids_cmd = "yd-list -P -D -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create -y {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"

    # ------------------------------------------------------------------
    # String attribute definition
    # ------------------------------------------------------------------

    def test_string_attribute_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/stringattribute.json"
        name = "user.pwt-test-3"
        list_cmd = "yd-list -R -n='' -t=''"
        ids_cmd = "yd-list -R -D -n='' -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"

    # ------------------------------------------------------------------
    # Group
    # ------------------------------------------------------------------

    def test_group_lifecycle(self, cleanup):
        spec = f"{RESOURCE_DIR}/group.json"
        name = "aaa"
        list_cmd = "yd-list --groups -n='' -t=''"
        ids_cmd = "yd-list --groups -D -n='' -t=''"

        cleanup(f"yd-remove -y {spec}")

        before = _ydids(ids_cmd)

        result = shell(f"yd-create -y {spec}")
        assert result.exit_code == 0, f"yd-create failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name in result.stdout, f"'{name}' not found in yd-list output"

        new_ydids = _ydids(ids_cmd) - before
        if new_ydids:
            _assert_show(next(iter(new_ydids)))

        result = shell(f"yd-remove -y {spec}")
        assert result.exit_code == 0, f"yd-remove failed:\n{result.stdout}"

        result = shell(list_cmd)
        assert result.exit_code == 0
        assert name not in result.stdout, f"'{name}' still present after removal"
