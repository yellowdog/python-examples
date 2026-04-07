"""
Unit tests for yellowdog_cli.utils.rclone_utils.parse_rclone_config
"""

from yellowdog_cli.utils.rclone_utils import parse_rclone_config


class TestParseRcloneConfig:
    """
    parse_rclone_config accepts either:
      - A plain remote name  ("myremote")          → (name, None)
      - An inline config     ("NAME,type=s3,...")   → (name, ini_section_str)
    An optional leading "rclone:" prefix is stripped in both cases.
    """

    def setup_method(self):
        parse_rclone_config.cache_clear()

    # ------------------------------------------------------------------
    # Plain remote names (defined in system rclone.conf)
    # ------------------------------------------------------------------

    def test_plain_remote_name(self):
        name, config = parse_rclone_config("myremote")
        assert name == "myremote"
        assert config is None

    def test_plain_remote_strips_rclone_prefix(self):
        name, config = parse_rclone_config("rclone:myremote")
        assert name == "myremote"
        assert config is None

    def test_empty_string_defaults_to_remote(self):
        name, config = parse_rclone_config("")
        assert name == "remote"
        assert config is None

    def test_whitespace_only_defaults_to_remote(self):
        name, config = parse_rclone_config("  ")
        assert name == "remote"
        assert config is None

    # ------------------------------------------------------------------
    # Inline config strings (all parameters embedded in the string)
    # ------------------------------------------------------------------

    def test_inline_config_remote_name(self):
        name, config = parse_rclone_config("S3,type=s3,provider=AWS")
        assert name == "S3"
        assert config is not None

    def test_inline_config_section_header(self):
        name, config = parse_rclone_config("S3,type=s3,provider=AWS")
        assert config is not None
        assert "[S3]" in config

    def test_inline_config_params_present(self):
        name, config = parse_rclone_config("S3,type=s3,provider=AWS,env_auth=true")
        assert config is not None
        assert "type = s3" in config
        assert "provider = AWS" in config
        assert "env_auth = true" in config

    def test_inline_config_strips_rclone_prefix(self):
        name, config = parse_rclone_config("rclone:myS3,type=s3,provider=AWS")
        assert name == "myS3"
        assert config is not None
        assert "[myS3]" in config

    def test_inline_config_region_param(self):
        name, config = parse_rclone_config(
            "S3,type=s3,provider=AWS,env_auth=true,region=eu-west-2"
        )
        assert config is not None
        assert "region = eu-west-2" in config

    def test_inline_config_empty_remote_name_defaults(self):
        # Leading comma → empty remote_name → defaults to "remote"
        name, config = parse_rclone_config(",type=s3")
        assert name == "remote"
        assert config is not None
        assert "[remote]" in config

    # ------------------------------------------------------------------
    # Caching: clearing and re-querying produces the same result
    # ------------------------------------------------------------------

    def test_repeated_call_after_clear_returns_same_result(self):
        r1 = parse_rclone_config("cached_remote")
        parse_rclone_config.cache_clear()
        r2 = parse_rclone_config("cached_remote")
        assert r1 == r2

    # ------------------------------------------------------------------
    # Quoted / stripped values
    # ------------------------------------------------------------------

    def test_single_quoted_value_stripped(self):
        name, config = parse_rclone_config("R,type='s3'")
        assert config is not None
        assert "type = s3" in config

    def test_double_quoted_value_stripped(self):
        name, config = parse_rclone_config('R2,type="s3"')
        assert config is not None
        assert "type = s3" in config
