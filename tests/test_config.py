"""Tests for strot_ai.config."""
import os
import stat
import pytest
import yaml
from pathlib import Path
from strot_ai.config import StrotConfig, _load_yaml, _save_yaml


class TestConfigPriorityChain:
    def test_constructor_args_highest_priority(self, credentials_file, mock_env):
        cfg = StrotConfig(
            url="https://arg.strot.ai",
            api_key="sk_arg_789",
            credentials_file=credentials_file,
        )
        assert cfg.url == "https://arg.strot.ai"
        assert cfg.api_key == "sk_arg_789"

    def test_env_vars_over_credentials(self, credentials_file, mock_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        assert cfg.url == "https://env.strot.ai"
        assert cfg.api_key == "sk_env_456"

    def test_credentials_file_fallback(self, credentials_file, clean_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        assert cfg.url == "https://test.strot.ai"
        assert cfg.api_key == "sk_test_123"

    def test_no_config_available(self, tmp_path, clean_env):
        empty_file = tmp_path / "empty"
        cfg = StrotConfig(credentials_file=empty_file)
        assert cfg.url is None
        assert cfg.api_key is None


class TestConfigValidate:
    def test_validate_passes_when_configured(self, credentials_file, clean_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        cfg.validate()  # Should not raise

    def test_validate_raises_no_url(self, tmp_path, clean_env):
        cfg = StrotConfig(api_key="sk_test", credentials_file=tmp_path / "none")
        with pytest.raises(RuntimeError, match="URL"):
            cfg.validate()

    def test_validate_raises_no_key(self, tmp_path, clean_env):
        cfg = StrotConfig(url="https://test.ai", credentials_file=tmp_path / "none")
        with pytest.raises(RuntimeError, match="API key"):
            cfg.validate()


class TestConfigProperties:
    def test_org_from_credentials(self, credentials_file, clean_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        assert cfg.org == "test-org-uuid"

    def test_user_email_from_credentials(self, credentials_file, clean_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        assert cfg.user_email == "test@example.com"

    def test_is_configured(self, credentials_file, clean_env):
        cfg = StrotConfig(credentials_file=credentials_file)
        assert cfg.is_configured is True

    def test_not_configured(self, tmp_path, clean_env):
        cfg = StrotConfig(credentials_file=tmp_path / "none")
        assert cfg.is_configured is False


class TestProfileManagement:
    def test_save_and_load_profile(self, tmp_path, monkeypatch):
        creds_file = tmp_path / ".strot" / "credentials"
        # Patch the default path
        import strot_ai.config as config_mod
        monkeypatch.setattr(config_mod, "DEFAULT_CREDENTIALS_FILE", creds_file)

        StrotConfig.save_profile(
            profile="test",
            url="https://test.ai",
            api_key="sk_test",
            org="org-123",
            user_email="user@test.com",
        )

        profiles = StrotConfig.list_profiles()
        assert "test" in profiles
        assert profiles["test"]["url"] == "https://test.ai"
        assert profiles["test"]["api_key"] == "sk_test"
        assert profiles["test"]["org"] == "org-123"

    def test_delete_profile(self, tmp_path, monkeypatch):
        creds_file = tmp_path / ".strot" / "credentials"
        import strot_ai.config as config_mod
        monkeypatch.setattr(config_mod, "DEFAULT_CREDENTIALS_FILE", creds_file)

        StrotConfig.save_profile(profile="todelete", url="https://x.ai", api_key="sk_x")
        assert StrotConfig.delete_profile("todelete") is True
        assert "todelete" not in StrotConfig.list_profiles()

    def test_delete_nonexistent_profile(self, tmp_path, monkeypatch):
        creds_file = tmp_path / ".strot" / "credentials"
        import strot_ai.config as config_mod
        monkeypatch.setattr(config_mod, "DEFAULT_CREDENTIALS_FILE", creds_file)
        assert StrotConfig.delete_profile("nope") is False

    def test_current_profile_tracking(self, tmp_path, monkeypatch):
        creds_file = tmp_path / ".strot" / "credentials"
        import strot_ai.config as config_mod
        monkeypatch.setattr(config_mod, "DEFAULT_CREDENTIALS_FILE", creds_file)

        StrotConfig.save_profile(profile="prod", url="https://prod.ai", api_key="sk_prod")
        assert StrotConfig.get_current_profile_name() == "prod"

        StrotConfig.save_profile(profile="staging", url="https://staging.ai", api_key="sk_stag")
        assert StrotConfig.get_current_profile_name() == "staging"


class TestYAMLHelpers:
    def test_load_missing_file(self, tmp_path):
        result = _load_yaml(tmp_path / "nonexistent")
        assert result == {}

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "file.yaml"
        _save_yaml(path, {"key": "value"})
        assert path.exists()
        loaded = _load_yaml(path)
        assert loaded["key"] == "value"
