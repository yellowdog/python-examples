"""
Tests that run the standard demos.
Use 'pytest --run-demos', otherwise these will be skipped.
"""

import pytest
from cli_test_helpers import shell

DEMO_DIR = "../python-examples-demos"
CMD_SEQ = "yd-provision && yd-submit -f && yd-terminate -y && yd-delete -y"
NEXTFLOW = "/Users/pwt/nextflow/nextflow"


@pytest.mark.demos
class TestDemos:
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

    def test_nextflow_image_montage(self):
        result = shell(
            f"cd {DEMO_DIR}/nextflow/image-montage && {NEXTFLOW} main.nf "
            "&& cd .. && ./cleanup.sh"
        )
        assert result.exit_code == 0

    def test_nextflow_salmon_rna(self):
        result = shell(
            f"cd {DEMO_DIR}/nextflow/salmon-rna && {NEXTFLOW} main.nf "
            "&& cd .. && ./cleanup.sh"
        )
        assert result.exit_code == 0

    def test_cmd_modelled_on_premise(self):
        result = shell(
            f"cd {DEMO_DIR}/modelled-on-premise && yd-instantiate "
            "&& sleep 120 && yd-terminate -y"
        )
        assert result.exit_code == 0
