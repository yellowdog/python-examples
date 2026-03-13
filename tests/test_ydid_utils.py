"""
Unit tests for yellowdog_cli.utils.ydid_utils
"""

import pytest

from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type


class TestGetYdidType:
    @pytest.mark.parametrize(
        "ydid, expected",
        [
            ("ydid:workreq:abc123", YDIDType.WORK_REQUIREMENT),
            ("ydid:taskgrp:abc123", YDIDType.TASK_GROUP),
            ("ydid:task:abc123", YDIDType.TASK),
            ("ydid:wrkrpool:abc123", YDIDType.WORKER_POOL),
            ("ydid:wrkr:abc123", YDIDType.WORKER),
            ("ydid:compreq:abc123", YDIDType.COMPUTE_REQUIREMENT),
            ("ydid:compsrc:abc123", YDIDType.COMPUTE_SOURCE),
            ("ydid:node:abc123", YDIDType.NODE),
            ("ydid:crt:abc123", YDIDType.COMPUTE_REQUIREMENT_TEMPLATE),
            ("ydid:cst:abc123", YDIDType.COMPUTE_SOURCE_TEMPLATE),
            ("ydid:imgfam:abc123", YDIDType.IMAGE_FAMILY),
            ("ydid:imggrp:abc123", YDIDType.IMAGE_GROUP),
            ("ydid:image:abc123", YDIDType.IMAGE),
            ("ydid:keyring:abc123", YDIDType.KEYRING),
            ("ydid:allow:abc123", YDIDType.ALLOWANCE),
            ("ydid:app:abc123", YDIDType.APPLICATION),
            ("ydid:user:abc123", YDIDType.USER),
            ("ydid:group:abc123", YDIDType.GROUP),
            ("ydid:role:abc123", YDIDType.ROLE),
        ],
    )
    def test_known_prefix_returns_correct_type(self, ydid, expected):
        assert get_ydid_type(ydid) == expected

    def test_none_returns_none(self):
        assert get_ydid_type(None) is None

    def test_empty_string_returns_none(self):
        assert get_ydid_type("") is None

    def test_no_ydid_prefix_returns_none(self):
        assert get_ydid_type("not-a-ydid") is None

    def test_ydid_prefix_only_unknown_type_returns_none(self):
        assert get_ydid_type("ydid:unknown:abc123") is None

    def test_ydid_prefix_with_no_type_returns_none(self):
        assert get_ydid_type("ydid:") is None

    def test_partial_prefix_not_matching_returns_none(self):
        # "ydid:task" is a prefix of "ydid:taskgrp" — ensure no false match
        assert get_ydid_type("ydid:taskgrp:xyz") == YDIDType.TASK_GROUP
        assert get_ydid_type("ydid:task:xyz") == YDIDType.TASK

    def test_enum_values_are_human_readable_strings(self):
        assert YDIDType.WORK_REQUIREMENT.value == "Work Requirement"
        assert YDIDType.TASK_GROUP.value == "Task Group"
        assert (
            YDIDType.COMPUTE_REQUIREMENT_TEMPLATE.value
            == "Compute Requirement Template"
        )
