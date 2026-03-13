import atexit
import sys
import time

import pytest
from cli_test_helpers import shell

# Strip pytest's own arguments before any yellowdog_cli modules are imported.
# CLIParser calls parse_args() at module level; without this, pytest's argv
# (e.g. file paths, -v) would be misinterpreted or cause parse errors.
sys.argv = sys.argv[:1]


def pytest_addoption(parser):
    parser.addoption(
        "--run-demos",
        action="store_true",
        default=False,
        help="Run demos",
    )
    parser.addoption(
        "--run-system",
        action="store_true",
        default=False,
        help="Run system tests against the live platform",
    )
    parser.addoption(
        "--run-system-compute",
        action="store_true",
        default=False,
        help="Run system tests that provision real cloud compute (implies --run-system)",
    )


def pytest_collection_modifyitems(config, items):
    run_system = config.getoption("--run-system") or config.getoption(
        "--run-system-compute"
    )

    if not config.getoption("--run-demos"):
        skipper = pytest.mark.skip(reason="Only run when '--run-demos' is given")
        for item in items:
            if "demos" in item.keywords:
                item.add_marker(skipper)

    if not run_system:
        skipper = pytest.mark.skip(reason="Only run when '--run-system' is given")
        for item in items:
            if "system" in item.keywords:
                item.add_marker(skipper)

    if not config.getoption("--run-system-compute"):
        skipper = pytest.mark.skip(
            reason="Only run when '--run-system-compute' is given"
        )
        for item in items:
            if "system_compute" in item.keywords:
                item.add_marker(skipper)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def system_tag() -> str:
    """
    Session-unique tag for compute tests (e.g. 'pytest-1741880400').

    Belt-and-braces: registers an atexit handler that cancels any outstanding
    Work Requirements and terminates any Worker Pools carrying the tag, so
    cloud resources are cleaned up even if a test crashes without teardown.
    """
    tag = f"pytest-{int(time.time())}"

    def _cleanup() -> None:
        shell(f"yd-cancel -y -t={tag} -n=pytest-system")
        shell(f"yd-terminate -y -t={tag} -n=pytest-system")

    atexit.register(_cleanup)
    return tag


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def yd_list_row_matches(stdout: str, name: str, status: str) -> bool:
    """
    Return True if any line of ``yd-list`` tabular output contains both
    ``name`` and ``status`` on the same row.

    Useful for asserting that a named resource is in a particular state,
    e.g. ``yd_list_row_matches(result.stdout, "my-pool", "RUNNING")``.
    """
    return any(name in line and status in line for line in stdout.splitlines())


# ---------------------------------------------------------------------------
# pytest configuration
# ---------------------------------------------------------------------------


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "demos: mark test to run only when '--run-demos' is specified"
    )
    config.addinivalue_line(
        "markers",
        "system: mark test to run only when '--run-system' is specified",
    )
    config.addinivalue_line(
        "markers",
        "system_compute: mark test to run only when '--run-system-compute' is specified",
    )
