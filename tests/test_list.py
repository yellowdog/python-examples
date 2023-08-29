from cli_test_helpers import shell


class TestList:
    def test_help(self):
        result = shell("yd-list --help")
        assert result.exit_code == 0

    def test_workerpool(self):
        result = shell("yd-list -p -n='' -t=''")
        assert result.exit_code == 0

    def test_compute_requirements(self):
        result = shell("yd-list -r -n='' -t=''")
        assert result.exit_code == 0

    def test_objects(self):
        result = shell("yd-list -o -n='' -t=''")
        assert result.exit_code == 0
