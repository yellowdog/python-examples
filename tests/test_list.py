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
        result = shell("yd-list -o -t=''")
        assert result.exit_code == 0

    def test_objects_all(self):
        result = shell("yd-list -oa -t=''")
        assert result.exit_code == 0

    def test_work_reqs(self):
        result = shell("yd-list -w -n='' -t=''")
        assert result.exit_code == 0

    def test_worker_pools(self):
        result = shell("yd-list -p -n='' -t=''")
        assert result.exit_code == 0

    def test_compute_reqs(self):
        result = shell("yd-list -r -n='' -t=''")
        assert result.exit_code == 0

    def test_compute_templates(self):
        result = shell("yd-list -C -n='' -t=''")
        assert result.exit_code == 0

    def test_source_templates(self):
        result = shell("yd-list -S -n='' -t=''")
        assert result.exit_code == 0

    def test_keyrings(self):
        result = shell("yd-list -K -n='' -t=''")
        assert result.exit_code == 0

    def test_image_families(self):
        result = shell("yd-list -I -n='' -t=''")
        assert result.exit_code == 0

    def test_namespaces(self):
        result = shell("yd-list -N -n='' -t=''")
        assert result.exit_code == 0

    def test_allowances(self):
        result = shell("yd-list -A -n='' -t=''")
        assert result.exit_code == 0
