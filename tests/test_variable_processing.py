"""
Unit tests for variable processing
"""

import pytest

from yd_commands.utils import remove_outer_delimiters, split_delimited_string


class TestVariableProcessing:
    @pytest.mark.parametrize(
        "input_string, opening_delimiter, closing_delimiter, expected",
        [
            ("{{one}}", "{{", "}}", "one"),
            ("{{{one}}}", "{{", "}}", "{one}"),
            ("__{{{on}e}}}__", "__{{", "}}__", "{on}e}"),
        ],
    )
    def test_remove_outer_delimiters(
        self, input_string, opening_delimiter, closing_delimiter, expected
    ):
        assert (
            remove_outer_delimiters(
                input_string=input_string,
                opening_delimiter=opening_delimiter,
                closing_delimiter=closing_delimiter,
            )
            == expected
        )

    @pytest.mark.parametrize(
        "input_string, opening_delimiter, closing_delimiter, expected",
        [
            ("{{one}}", "{{", "}}", ["{{one}}"]),
            (
                "A {{one}}123{{xy}z}}hello",
                "{{",
                "}}",
                ["A ", "{{one}}", "123", "{{xy}z}}", "hello"],
            ),
            pytest.param(
                "{{one}}}}", "{{", "}}", ["{{one}}}"], marks=pytest.mark.xfail
            ),  # Mismatched delimiters
        ],
    )
    def test_split_delimited_string(
        self, input_string, opening_delimiter, closing_delimiter, expected
    ):
        assert (
            split_delimited_string(
                s=input_string,
                opening_delimiter=opening_delimiter,
                closing_delimiter=closing_delimiter,
            )
            == expected
        )
