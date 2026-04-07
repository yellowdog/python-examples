"""
Test that the GUI interfaces start.
"""

import subprocess
import time

DEMO_DIR = "../python-examples-demos"


class TestGUIs:
    def test_generic_gui(self):
        proc = subprocess.Popen(
            ["./yellow-gui.py"],
            cwd=f"{DEMO_DIR}/yellow-gui",
        )
        time.sleep(2)
        assert proc.poll() is None, "GUI exited unexpectedly on startup"
        proc.terminate()
        proc.wait()
