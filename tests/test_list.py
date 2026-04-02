import pytest
from cli_test_helpers import shell


@pytest.mark.system
@pytest.mark.parametrize(
    "cmd",
    [
        "yd-list --help",
        "yd-list -A -n='' -t=''",
        "yd-list -C -n='' -t=''",
        "yd-list -I -n='' -t=''",
        "yd-list -K -n='' -t=''",
        "yd-list -S -n='' -t=''",
        "yd-list -p -n='' -t=''",
        "yd-list -r -n='' -t=''",
        "yd-list -w -n='' -t=''",
        "yd-list --groups -n='' -t=''",
        "yd-list --permissions -n='' -t=''",
        "yd-list --roles -n='' -t=''",
    ],
)
def test_list(cmd):
    assert shell(cmd).exit_code == 0
