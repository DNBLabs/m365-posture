"""Environment-backed configuration for Microsoft Graph app-only authentication.

Reads tenant, application, credential, and chapter toggle settings from ``os.environ``
so secrets are never loaded from source files. Boolean chapter flags are parsed from
string values (``true`` / ``false``) because process and Task Scheduler environments
only expose string values on Windows.
"""

import os
from dataclasses import dataclass
from typing import Optional


class ConfigError(ValueError):
    """Raised when required environment variables are missing or contradictory."""


@dataclass
class AppConfig:
    """Validated settings for a single-tenant Graph run.

    Attributes:
        tenant_id: Entra directory (tenant) ID.
        client_id: App registration client ID.
        cert_path: Path to PFX for certificate auth, or ``None`` if using a secret.
        cert_password: Optional PFX password.
        client_secret: Optional client secret when not using a certificate.
        output_dir: Default output directory from env (CLI ``--out`` overrides for reports).
        chapters: Map of chapter id to enabled flag.
    """

    tenant_id: str
    client_id: str
    cert_path: Optional[str]
    cert_password: Optional[str]
    client_secret: Optional[str]
    output_dir: str
    chapters: dict[str, bool]


def load_config() -> AppConfig:
    """Read configuration from the current process environment.

    Returns:
        :class:`AppConfig` populated from ``TENANT_ID``, ``CLIENT_ID``, optional
        ``GRAPH_CERT_PATH`` / ``GRAPH_CERT_PASSWORD``, optional ``CLIENT_SECRET``,
        optional ``OUTPUT_DIR``, and ``CHAPTER_*`` toggles.

    Raises:
        ConfigError: If ``TENANT_ID`` or ``CLIENT_ID`` is missing, or if neither
            certificate path nor client secret is provided.
    """
    tenant_id = os.environ.get("TENANT_ID")
    client_id = os.environ.get("CLIENT_ID")
    if not tenant_id or not client_id:
        raise ConfigError("TENANT_ID and CLIENT_ID are required")
    cert_path = os.environ.get("GRAPH_CERT_PATH")
    cert_password = os.environ.get("GRAPH_CERT_PASSWORD")
    client_secret = os.environ.get("CLIENT_SECRET")
    if not cert_path and not client_secret:
        raise ConfigError("Either GRAPH_CERT_PATH or CLIENT_SECRET must be set for app-only auth")
    output_dir = os.environ.get("OUTPUT_DIR", "./dist")
    chapters = {
        "guests": os.environ.get("CHAPTER_GUESTS", "true").lower() == "true",
        "privileged": os.environ.get("CHAPTER_PRIVILEGED", "true").lower() == "true",
        "applications": os.environ.get("CHAPTER_APPLICATIONS", "true").lower() == "true",
        "devices": os.environ.get("CHAPTER_DEVICES", "true").lower() == "true",
        "signin_risk": os.environ.get("CHAPTER_SIGNIN_RISK", "false").lower() == "true",
    }
    return AppConfig(
        tenant_id=tenant_id,
        client_id=client_id,
        cert_path=cert_path,
        cert_password=cert_password,
        client_secret=client_secret,
        output_dir=output_dir,
        chapters=chapters,
    )
