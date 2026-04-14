"""
Unit tests for provision_utils.py.

Covers:
  - get_user_data_property: mutex validation, all-None, user_data string,
    user_data_file, user_data_files concatenation, content_path chdir,
    chdir failure, finally restores original directory
  - get_template_id: YDID passthrough, name lookup, name not found
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

import yellowdog_cli.utils.provision_utils as pu_module
from yellowdog_cli.utils.provision_utils import get_template_id, get_user_data_property
from yellowdog_cli.utils.ydid_utils import YDIDType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    user_data: str | None = None,
    user_data_file: str | None = None,
    user_data_files: list[str] | None = None,
) -> MagicMock:
    config = MagicMock()
    config.user_data = user_data
    config.user_data_file = user_data_file
    config.user_data_files = user_data_files
    return config


def _identity_subs(text, **kwargs):
    """Variable substitution stub that returns the text unchanged."""
    return text


# ---------------------------------------------------------------------------
# get_user_data_property
# ---------------------------------------------------------------------------


class TestGetUserDataProperty:
    """
    Tests for get_user_data_property.
    """

    def _call(
        self,
        config,
        content_path: str | None = None,
        subs_result: str | None = None,
    ):
        """
        Helper: call get_user_data_property with chdir/getcwd/subs mocked.
        subs_result: fixed return value from variable substitution; if None
        the stub passes text through unchanged.
        """
        sub_fn = (lambda text, **kw: subs_result) if subs_result else _identity_subs

        with (
            patch.object(pu_module, "chdir"),
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch.object(
                pu_module,
                "process_variable_substitutions_in_file_contents",
                side_effect=sub_fn,
            ),
        ):
            return get_user_data_property(config, content_path)

    def test_two_options_set_raises_value_error(self):
        config = _make_config(user_data="inline data", user_data_file="file.sh")
        with pytest.raises(ValueError, match="Only one of"):
            get_user_data_property(config)

    def test_all_three_options_set_raises_value_error(self):
        config = _make_config(
            user_data="data", user_data_file="file.sh", user_data_files=["a.sh"]
        )
        with pytest.raises(ValueError, match="Only one of"):
            get_user_data_property(config)

    def test_all_none_returns_none(self):
        config = _make_config()
        result = self._call(config)
        assert result is None

    def test_user_data_string_returned_after_subs(self):
        config = _make_config(user_data="#!/bin/bash\necho hello")
        result = self._call(config, subs_result="substituted-content")
        assert result == "substituted-content"

    def test_user_data_string_passed_through_when_no_vars(self):
        config = _make_config(user_data="plain text")
        result = self._call(config)
        assert result == "plain text"

    def test_user_data_file_content_read_and_returned(self):
        config = _make_config(user_data_file="startup.sh")
        with (
            patch.object(pu_module, "chdir"),
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch.object(
                pu_module,
                "process_variable_substitutions_in_file_contents",
                side_effect=_identity_subs,
            ),
            patch("builtins.open", mock_open(read_data="#!/bin/bash\necho hi")),
        ):
            result = get_user_data_property(config)
        assert result == "#!/bin/bash\necho hi"

    def test_user_data_files_concatenated_with_newlines(self):
        config = _make_config(user_data_files=["a.sh", "b.sh"])

        read_mock = mock_open()
        read_mock.return_value.__enter__.return_value.read.side_effect = [
            "content-a",
            "content-b",
        ]

        with (
            patch.object(pu_module, "chdir"),
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch.object(
                pu_module,
                "process_variable_substitutions_in_file_contents",
                side_effect=_identity_subs,
            ),
            patch("builtins.open", read_mock),
        ):
            result = get_user_data_property(config)
        assert result == "content-a\ncontent-b\n"

    def test_content_path_used_for_chdir_when_provided(self):
        config = _make_config(user_data="data")

        with (
            patch.object(pu_module, "chdir") as mock_chdir,
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch.object(
                pu_module,
                "process_variable_substitutions_in_file_contents",
                side_effect=_identity_subs,
            ),
        ):
            get_user_data_property(config, content_path="/custom/path")

        chdir_dirs = [call.args[0] for call in mock_chdir.call_args_list]
        assert "/custom/path" in chdir_dirs

    def test_config_file_dir_used_when_no_content_path(self):
        config = _make_config(user_data="data")

        with (
            patch.object(pu_module, "chdir") as mock_chdir,
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch.object(
                pu_module,
                "process_variable_substitutions_in_file_contents",
                side_effect=_identity_subs,
            ),
        ):
            get_user_data_property(config)

        chdir_dirs = [call.args[0] for call in mock_chdir.call_args_list]
        assert "/config/dir" in chdir_dirs

    def test_restores_original_directory_on_file_error(self):
        config = _make_config(user_data_file="missing.sh")

        with (
            patch.object(pu_module, "chdir") as mock_chdir,
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
            patch("builtins.open", side_effect=OSError("File not found")),
        ):
            with pytest.raises(OSError):
                get_user_data_property(config)

        chdir_dirs = [call.args[0] for call in mock_chdir.call_args_list]
        assert "/original" in chdir_dirs

    def test_chdir_failure_raises_runtime_error(self):
        config = _make_config(user_data="data")

        def chdir_effect(path):
            if path == "/config/dir":
                raise OSError("No such directory")

        with (
            patch.object(pu_module, "chdir", side_effect=chdir_effect),
            patch.object(pu_module, "getcwd", return_value="/original"),
            patch.object(pu_module, "CONFIG_FILE_DIR", "/config/dir"),
        ):
            with pytest.raises(
                RuntimeError, match="Unable to switch to content directory"
            ):
                get_user_data_property(config)


# ---------------------------------------------------------------------------
# get_template_id
# ---------------------------------------------------------------------------


class TestGetTemplateId:
    """
    Tests for get_template_id.
    """

    def test_ydid_passthrough_no_lookup(self):
        ydid = "ydid:crt:test:abc123"
        client = MagicMock()

        with (
            patch.object(
                pu_module,
                "get_ydid_type",
                return_value=YDIDType.COMPUTE_REQUIREMENT_TEMPLATE,
            ),
            patch.object(
                pu_module, "get_compute_requirement_template_id_by_name"
            ) as mock_lookup,
        ):
            result = get_template_id(client, ydid)

        assert result == ydid
        mock_lookup.assert_not_called()

    def test_name_triggers_lookup_and_returns_id(self):
        client = MagicMock()

        with (
            patch.object(pu_module, "get_ydid_type", return_value=None),
            patch.object(
                pu_module,
                "get_compute_requirement_template_id_by_name",
                return_value="ydid:crt:test:resolved",
            ),
            patch.object(pu_module, "print_info"),
        ):
            result = get_template_id(client, "my-template")

        assert result == "ydid:crt:test:resolved"

    def test_name_not_found_raises_key_error(self):
        client = MagicMock()

        with (
            patch.object(pu_module, "get_ydid_type", return_value=None),
            patch.object(
                pu_module,
                "get_compute_requirement_template_id_by_name",
                return_value=None,
            ),
        ):
            with pytest.raises(KeyError, match="not found"):
                get_template_id(client, "nonexistent-template")
