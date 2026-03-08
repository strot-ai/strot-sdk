"""Shared test fixtures for STROT SDK tests."""
import os
import pytest
import yaml


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear the decorator registry between tests."""
    from strot_sdk.decorators import _REGISTRY
    for key in _REGISTRY:
        _REGISTRY[key].clear()
    yield
    for key in _REGISTRY:
        _REGISTRY[key].clear()


@pytest.fixture(autouse=True)
def clean_data_client():
    """Reset the data module's cached client between tests."""
    import strot_sdk.data as data_mod
    data_mod._client = None
    yield
    data_mod._client = None


@pytest.fixture
def credentials_file(tmp_path):
    """Create a temporary credentials file and return its path."""
    creds_dir = tmp_path / ".strot"
    creds_dir.mkdir()
    creds_file = creds_dir / "credentials"
    data = {
        "version": 1,
        "current_profile": "default",
        "profiles": {
            "default": {
                "url": "https://test.strot.ai",
                "api_key": "sk_test_123",
                "org": "test-org-uuid",
                "user_email": "test@example.com",
            }
        },
    }
    with open(creds_file, "w") as f:
        yaml.dump(data, f)
    return creds_file


@pytest.fixture
def mock_env(monkeypatch):
    """Set STROT env vars for testing."""
    monkeypatch.setenv("STROT_URL", "https://env.strot.ai")
    monkeypatch.setenv("STROT_API_KEY", "sk_env_456")


@pytest.fixture
def clean_env(monkeypatch):
    """Remove STROT env vars."""
    monkeypatch.delenv("STROT_URL", raising=False)
    monkeypatch.delenv("STROT_API_KEY", raising=False)
    monkeypatch.delenv("STROT_PROFILE", raising=False)
