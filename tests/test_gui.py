"""
Test that the GUI interfaces start.
"""

from cli_test_helpers import shell

DEMO_DIR = "../python-examples-demos"
CMD_SEQ = "yd-provision -D && yd-submit -D"


class TestGUIs:
    def test_generic_gui(self):
        result = shell(f"cd {DEMO_DIR}/yellow-gui && ./yellow-gui.py")
        assert result.exit_code == 0

    def test_primes_gui(self):
        result = shell(f"cd {DEMO_DIR}/primes/gui && ./primes-gui.py")
        assert result.exit_code == 0

    def test_blender_gui(self):
        result = shell(f"cd {DEMO_DIR}/blender/gui && ./blender-gui.py")
        assert result.exit_code == 0
