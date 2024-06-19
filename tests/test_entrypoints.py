"""
Basic check that all the entrypoints are present, and can be invoked.
"""

from cli_test_helpers import shell


def test_entrypoints():
    result = shell("yd-abort --help")
    assert result.exit_code == 0
    result = shell("yd-create --help")
    assert result.exit_code == 0
    result = shell("yd-delete --help")
    assert result.exit_code == 0
    result = shell("yd-download --help")
    assert result.exit_code == 0
    result = shell("yd-format-json")
    assert result.exit_code == 0
    result = shell("yd-follow --help")
    assert result.exit_code == 0
    result = shell("yd-instantiate --help")
    assert result.exit_code == 0
    result = shell("yd-jsonnet2json")
    assert result.exit_code == 1
    result = shell("yd-list --help")
    assert result.exit_code == 0
    result = shell("yd-provision --help")
    assert result.exit_code == 0
    result = shell("yd-remove --help")
    assert result.exit_code == 0
    result = shell("yd-resize --help")
    assert result.exit_code == 0
    result = shell("yd-shutdown --help")
    assert result.exit_code == 0
    result = shell("yd-submit --help")
    assert result.exit_code == 0
    result = shell("yd-terminate --help")
    assert result.exit_code == 0
    result = shell("yd-upload --help")
    assert result.exit_code == 0
    result = shell("yd-version")
    assert result.exit_code == 0
    result = shell("yd-cloudwizard --help")
    assert result.exit_code == 0
    result = shell("yd-start --help")
    assert result.exit_code == 0
    result = shell("yd-hold --help")
    assert result.exit_code == 0
    result = shell("yd-boost --help")
    assert result.exit_code == 0
    result = shell("yd-show --help")
    assert result.exit_code == 0
