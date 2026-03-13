"""
Unit tests for yellowdog_cli.utils.type_check
"""

import pytest

from yellowdog_cli.utils.type_check import (
    check_bool,
    check_dict,
    check_float,
    check_float_or_int,
    check_int,
    check_list,
    check_str,
)


class TestCheckInt:
    def test_valid(self):
        assert check_int(42) == 42

    def test_zero(self):
        assert check_int(0) == 0

    def test_negative(self):
        assert check_int(-7) == -7

    def test_none_returns_none(self):
        assert check_int(None) is None

    def test_float_raises(self):
        with pytest.raises(Exception, match="Integer"):
            check_int(1.5)

    def test_string_raises(self):
        with pytest.raises(Exception, match="Integer"):
            check_int("5")

    def test_bool_accepted(self):
        # bool is a subtype of int; isinstance(True, int) is True
        assert check_int(True) is True


class TestCheckFloat:
    def test_valid(self):
        assert check_float(3.14) == 3.14

    def test_none_returns_none(self):
        assert check_float(None) is None

    def test_int_raises(self):
        # int is not a float in Python's type system
        with pytest.raises(Exception, match="Float"):
            check_float(1)

    def test_string_raises(self):
        with pytest.raises(Exception, match="Float"):
            check_float("1.5")


class TestCheckFloatOrInt:
    def test_float(self):
        assert check_float_or_int(3.14) == 3.14

    def test_int(self):
        assert check_float_or_int(5) == 5

    def test_none_returns_none(self):
        assert check_float_or_int(None) is None

    def test_string_raises(self):
        with pytest.raises(Exception, match="Float.*Integer"):
            check_float_or_int("abc")

    def test_list_raises(self):
        with pytest.raises(Exception):
            check_float_or_int([1.0])


class TestCheckBool:
    def test_true(self):
        assert check_bool(True) is True

    def test_false(self):
        assert check_bool(False) is False

    def test_none_returns_none(self):
        assert check_bool(None) is None

    def test_int_one_raises(self):
        # type(1) != bool, even though isinstance(1, int) is True
        with pytest.raises(Exception, match="Boolean"):
            check_bool(1)

    def test_int_zero_raises(self):
        with pytest.raises(Exception, match="Boolean"):
            check_bool(0)

    def test_string_raises(self):
        with pytest.raises(Exception, match="Boolean"):
            check_bool("True")


class TestCheckStr:
    def test_valid(self):
        assert check_str("hello") == "hello"

    def test_empty_string(self):
        assert check_str("") == ""

    def test_none_returns_none(self):
        assert check_str(None) is None

    def test_int_raises(self):
        with pytest.raises(Exception, match="String"):
            check_str(42)

    def test_list_raises(self):
        with pytest.raises(Exception, match="String"):
            check_str(["a"])


class TestCheckList:
    def test_valid(self):
        assert check_list([1, 2, 3]) == [1, 2, 3]

    def test_empty(self):
        assert check_list([]) == []

    def test_none_returns_none(self):
        assert check_list(None) is None

    def test_tuple_raises(self):
        with pytest.raises(Exception, match="List"):
            check_list((1, 2))

    def test_dict_raises(self):
        with pytest.raises(Exception, match="List"):
            check_list({"a": 1})


class TestCheckDict:
    def test_valid(self):
        assert check_dict({"a": 1}) == {"a": 1}

    def test_empty(self):
        assert check_dict({}) == {}

    def test_none_returns_none(self):
        assert check_dict(None) is None

    def test_list_raises(self):
        with pytest.raises(Exception, match="Dict"):
            check_dict([1, 2])

    def test_string_raises(self):
        with pytest.raises(Exception, match="Dict"):
            check_dict("{'a': 1}")
