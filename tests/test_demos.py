"""
Tests that run the standard demos.
Use 'pytest --run-demos', otherwise these will be skipped.
"""

import pytest
from cli_test_helpers import shell

DEMO_DIR = "../python-examples-demos"
CMD_SEQ = "yd-provision && yd-submit -f && yd-terminate -y && yd-delete -Ry '{{tag}}*'"
NEXTFLOW = "/Users/pwt/nextflow/nextflow"

_STANDARD_DEMOS = [
    "bash",
    "batch-allocation",
    "bash/gce-instance-groups",
    "primes",
    "image-montage",
    "common-factors-csv",
    "powershell",
    "cmd.exe",
    "blender-2",
    "montecarlo",
]


@pytest.mark.demos
class TestDemos:
    @pytest.mark.parametrize("demo", _STANDARD_DEMOS)
    def test_demo(self, demo: str):
        result = shell(f"cd {DEMO_DIR}/{demo} && {CMD_SEQ}")
        assert result.exit_code == 0

    def test_cmd_modelled_on_premise(self):
        result = shell(
            f"cd {DEMO_DIR}/modelled-on-premise && yd-instantiate "
            "&& sleep 120 && yd-terminate -y"
        )
        assert result.exit_code == 0

    def test_video_demo(self):
        result = shell(
            f"cd {DEMO_DIR}/video-demo && yd-provision -v instances=1 -v max_nodes=1 "
            f"&& yd-submit -C 1 -f && yd-terminate -y && yd-delete -Ry '{{{{tag}}}}*'"
        )
        assert result.exit_code == 0

    # def test_nextflow_image_montage(self):
    #     result = shell(
    #         f"cd {DEMO_DIR}/nextflow/image-montage && {NEXTFLOW} main.nf "
    #         "&& cd .. && ./cleanup.sh"
    #     )
    #     assert result.exit_code == 0

    # def test_nextflow_salmon_rna(self):
    #     result = shell(
    #         f"cd {DEMO_DIR}/nextflow/salmon-rna && {NEXTFLOW} main.nf "
    #         "&& cd .. && ./cleanup.sh"
    #     )
    #     assert result.exit_code == 0
