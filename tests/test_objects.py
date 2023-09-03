"""
Template for using 'expect' scripts to drive tests that require
interactive input.
"""

from cli_test_helpers import shell


class TestObjects:
    def test_object_details(self, tmp_path):
        script_exp = """
        set timeout 10
        spawn yd-list -oad -t ""
        expect "press <Return> to cancel: "
        send "1\r"
        expect eof
        """
        p = tmp_path / "script.exp"
        p.write_text(script_exp)
        result = shell(f"expect {p}")
        assert result.exit_code == 0
