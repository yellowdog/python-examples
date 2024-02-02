"""
Template for using 'expect' scripts to drive tests that require
interactive input.
"""

from cli_test_helpers import shell


class TestObjects:
    def test_object_details(self, tmp_path):
        # The Expect script
        script_exp = """
        set timeout 10
        spawn yd-list -oad -n=pytest -t=
        expect "press <Return> to cancel: "
        send "1\r"
        expect eof
        """
        p = tmp_path / "script.exp"
        p.write_text(script_exp)

        # Ensure there's an object in the Object Store
        result = shell(f"yd-upload -n=pytest -t='' {p}")
        assert result.exit_code == 0

        # Run the Expect script
        result = shell(f"expect {p}")
        assert result.exit_code == 0

        # Delete the object
        result = shell(f"yd-delete -y -n=pytest -t='' {p}")
        assert result.exit_code == 0
