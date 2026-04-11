import pytest
from cli_test_helpers import shell


@pytest.mark.system
@pytest.mark.parametrize(
    "cmd",
    [
        "yd-list --help",
        "yd-list allowances -n='' -t=''",
        "yd-list compute-requirement-templates -n='' -t=''",
        "yd-list image-families -n='' -t=''",
        "yd-list keyrings -n='' -t=''",
        "yd-list compute-source-templates -n='' -t=''",
        "yd-list worker-pools -n='' -t=''",
        "yd-list compute-requirements -n='' -t=''",
        "yd-list work-requirements -n='' -t=''",
        "yd-list groups -n='' -t=''",
        "yd-list permissions -n='' -t=''",
        "yd-list roles -n='' -t=''",
    ],
)
def test_list(cmd):
    assert shell(cmd).exit_code == 0
