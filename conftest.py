import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-demos",
        action="store_true",
        default=False,
        help="Run demos",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-demos"):
        skipper = pytest.mark.skip(reason="Only run when '--run-demos' is given")
        for item in items:
            if "demos" in item.keywords:
                item.add_marker(skipper)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "demos: mark test to run only when '--run-demos' is specified"
    )
