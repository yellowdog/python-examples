"""
Tests that run the standard demo dry-runs.
"""

import subprocess
import time

import pytest
from cli_test_helpers import shell

DEMO_DIR = "../python-examples-demos"
CMD_SEQ = "yd-provision -D && yd-submit -D && yd-instantiate -D"

_DEMOS = [
    "bash",
    "bash/gce-instance-groups",
    "batch-allocation",
    "blender-2",
    "cmd.exe",
    "common-factors-csv",
    "image-montage",
    "montecarlo",
    "powershell",
    "primes",
    "video-demo",
]


@pytest.mark.dryruns
@pytest.mark.parametrize("demo", _DEMOS)
def test_dry_run_in_dir(demo):
    result = shell(f"cd {DEMO_DIR}/{demo} && {CMD_SEQ}")
    assert result.exit_code == 0


@pytest.mark.dryruns
def test_generic_gui():
    proc = subprocess.Popen(
        ["./yellow-gui.py"],
        cwd=f"{DEMO_DIR}/yellow-gui",
    )
    time.sleep(2.5)
    assert proc.poll() is None, "GUI exited unexpectedly on startup"
    proc.terminate()
    proc.wait()


@pytest.mark.dryruns
@pytest.mark.parametrize("demo", _DEMOS)
def test_dry_run_out_of_dir(demo):
    result = shell(
        f"cd {DEMO_DIR}"
        f" && yd-provision -D -c {demo}/config.toml"
        f" && yd-submit -D -c {demo}/config.toml"
        f" && yd-instantiate -D -c {demo}/config.toml"
    )
    assert result.exit_code == 0
