"""
Unit tests for yellowdog_cli.utils.submit_utils.assemble_arguments

Tests the combination of argumentsPrefix + arguments + argumentsPostfix.
"""

import pytest

from yellowdog_cli.utils.submit_utils import assemble_arguments


class TestAssembleArguments:
    """
    assemble_arguments(prefix, args, postfix) combines three lists.
    When prefix and postfix are both empty/None, args is returned unchanged.
    """

    # ------------------------------------------------------------------
    # No prefix or postfix — pass-through
    # ------------------------------------------------------------------

    def test_no_prefix_no_postfix_returns_args_unchanged(self):
        assert assemble_arguments(None, ["a", "b"], None) == ["a", "b"]

    def test_no_prefix_no_postfix_empty_args_unchanged(self):
        assert assemble_arguments(None, [], None) == []

    def test_no_prefix_no_postfix_none_args_unchanged(self):
        assert assemble_arguments(None, None, None) is None

    def test_empty_prefix_and_postfix_returns_args_unchanged(self):
        assert assemble_arguments([], ["a"], []) == ["a"]

    # ------------------------------------------------------------------
    # Prefix only
    # ------------------------------------------------------------------

    def test_prefix_prepended_to_args(self):
        assert assemble_arguments(["--input"], ["file.txt"], None) == [
            "--input",
            "file.txt",
        ]

    def test_prefix_with_none_args(self):
        assert assemble_arguments(["--flag"], None, None) == ["--flag"]

    def test_prefix_with_empty_args(self):
        assert assemble_arguments(["--flag"], [], None) == ["--flag"]

    def test_multi_item_prefix(self):
        assert assemble_arguments(["--input", "data/"], ["file.txt"], None) == [
            "--input",
            "data/",
            "file.txt",
        ]

    # ------------------------------------------------------------------
    # Postfix only
    # ------------------------------------------------------------------

    def test_postfix_appended_to_args(self):
        assert assemble_arguments(None, ["file.txt"], ["--output"]) == [
            "file.txt",
            "--output",
        ]

    def test_postfix_with_none_args(self):
        assert assemble_arguments(None, None, ["--output"]) == ["--output"]

    def test_postfix_with_empty_args(self):
        assert assemble_arguments(None, [], ["--output"]) == ["--output"]

    def test_multi_item_postfix(self):
        assert assemble_arguments(None, ["file.txt"], ["--output", "results/"]) == [
            "file.txt",
            "--output",
            "results/",
        ]

    # ------------------------------------------------------------------
    # Both prefix and postfix
    # ------------------------------------------------------------------

    def test_prefix_args_postfix_combined(self):
        assert assemble_arguments(["--in"], ["file.txt"], ["--out"]) == [
            "--in",
            "file.txt",
            "--out",
        ]

    def test_prefix_args_postfix_realistic(self):
        assert assemble_arguments(
            ["--input", "data/"],
            ["{{filename}}"],
            ["--output", "results/"],
        ) == ["--input", "data/", "{{filename}}", "--output", "results/"]

    def test_prefix_and_postfix_no_args(self):
        assert assemble_arguments(["--start"], None, ["--end"]) == ["--start", "--end"]

    def test_prefix_and_postfix_empty_args(self):
        assert assemble_arguments(["--start"], [], ["--end"]) == ["--start", "--end"]

    # ------------------------------------------------------------------
    # Order is preserved
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "prefix, args, postfix, expected",
        [
            (
                ["p1", "p2"],
                ["a1", "a2"],
                ["s1", "s2"],
                ["p1", "p2", "a1", "a2", "s1", "s2"],
            ),
            (["p1"], ["a1", "a2", "a3"], ["s1"], ["p1", "a1", "a2", "a3", "s1"]),
            (
                ["p1", "p2", "p3"],
                ["a1"],
                ["s1", "s2", "s3"],
                ["p1", "p2", "p3", "a1", "s1", "s2", "s3"],
            ),
        ],
    )
    def test_order_preserved(self, prefix, args, postfix, expected):
        assert assemble_arguments(prefix, args, postfix) == expected
