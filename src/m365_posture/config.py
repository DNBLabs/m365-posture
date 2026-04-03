import os
from dataclasses import dataclass
from typing import Optional


class ConfigError(ValueError):
    pass


@dataclass
class AppConfig:
    tenant_id: str
    client_id: str
    cert_path: Optional[str]
    cert_password: Optional[str]
    client_secret: Optional[str]
    output_dir: str
    chapters: dict[str, bool]


def load_config() -> AppConfig:
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
