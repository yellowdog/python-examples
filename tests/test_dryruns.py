"""
Tests that run the standard demo dry-runs.
"""

from cli_test_helpers import shell

DEMO_DIR = "../python-examples-demos"
CMD_SEQ = "yd-provision -D && yd-submit -D && yd-instantiate -D"


class TestDemoDryRuns:
    def test_bash(self):
        result = shell(f"cd {DEMO_DIR}/bash && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_primes(self):
        result = shell(f"cd {DEMO_DIR}/primes && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_image_montage(self):
        result = shell(f"cd {DEMO_DIR}/image-montage && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_openfoam(self):
        result = shell(f"cd {DEMO_DIR}/openfoam && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_slurm_cluster(self):
        result = shell(f"cd {DEMO_DIR}/slurm-cluster && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_common_factors(self):
        result = shell(f"cd {DEMO_DIR}/common-factors-csv && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_virtual_screening(self):
        result = shell(f"cd {DEMO_DIR}/virtual-screening && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_benchmark(self):
        result = shell(f"cd {DEMO_DIR}/benchmark && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_benchmark_jsonnet(self):
        result = shell(
            f"cd {DEMO_DIR}/benchmark &&"
            " yd-submit -D -r wr_benchmark.jsonnet -v crt_file=crt.json"
        )
        assert result.exit_code == 0

    def test_powershell(self):
        result = shell(f"cd {DEMO_DIR}/powershell && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_cmd_exe(self):
        result = shell(f"cd {DEMO_DIR}/cmd.exe && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_blender(self):
        result = shell(f"cd {DEMO_DIR}/blender && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_montecarlo(self):
        result = shell(f"cd {DEMO_DIR}/montecarlo && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_ansys(self):
        result = shell(f"cd {DEMO_DIR}/ansys && {CMD_SEQ}")
        assert result.exit_code == 0

    # Tests run from outside the demo directories
    def test_bash_out(self):
        demo_name = "bash"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_primes_out(self):
        demo_name = "primes"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_image_montage_out(self):
        demo_name = "image-montage"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_openfoam_out(self):
        demo_name = "openfoam"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_slurm_cluster_out(self):
        demo_name = "slurm-cluster"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_common_factors_out(self):
        demo_name = "common-factors-csv"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_virtual_screening_out(self):
        demo_name = "virtual-screening"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_benchmark_out(self):
        demo_name = "benchmark"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_benchmark_jsonnet_out(self):
        demo_name = "benchmark"
        result = shell(
            f"cd {DEMO_DIR} &&"
            f" yd-submit -D -c {demo_name}/config.toml"
            f" -r {demo_name}/wr_benchmark.jsonnet"
            f" -v crt_file={demo_name}/crt.json"
        )
        assert result.exit_code == 0

    def test_powershell_out(self):
        demo_name = "powershell"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_cmd_exe_out(self):
        demo_name = "cmd.exe"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_blender_out(self):
        demo_name = "blender"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_montecarlo_out(self):
        demo_name = "montecarlo"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0

    def test_ansys_out(self):
        demo_name = "ansys"
        result = shell(
            f"cd {DEMO_DIR} && yd-provision -D -c {demo_name}/config.toml && yd-submit"
            f" -D -c {demo_name}/config.toml && yd-instantiate -D -c"
            f" {demo_name}/config.toml"
        )
        assert result.exit_code == 0
