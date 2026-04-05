"""Tests for :func:`m365_posture.config.load_config` environment parsing."""

import pytest
from m365_posture.config import load_config, ConfigError


def test_load_config_requires_tenant_and_client(monkeypatch):
    """Raise ConfigError when TENANT_ID or CLIENT_ID is unset.

    Args:
        monkeypatch: Pytest fixture to clear environment variables.

    Returns:
        None.
    """
    monkeypatch.delenv("TENANT_ID", raising=False)
    monkeypatch.delenv("CLIENT_ID", raising=False)
    with pytest.raises(ConfigError):
        load_config()


def test_load_config_valid_env_tenant_matches(monkeypatch):
    """Return AppConfig with tenant_id matching TENANT_ID when secrets are present.

    Args:
        monkeypatch: Pytest fixture to set required environment variables.

    Returns:
        None.
    """
    tenant = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setenv("TENANT_ID", tenant)
    monkeypatch.setenv("CLIENT_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("CLIENT_SECRET", "dummy-secret-for-test")
    monkeypatch.delenv("GRAPH_CERT_PATH", raising=False)
    cfg = load_config()
    assert cfg.tenant_id == tenant
