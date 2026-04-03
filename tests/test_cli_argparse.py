"""CLI argparse and wiring tests (no live Graph calls)."""

from __future__ import annotations

from pathlib import Path

import pytest

from m365_posture.cli import main, run_pipeline
from m365_posture.config import load_config


def test_main_run_invokes_run_pipeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TENANT_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("CLIENT_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("CLIENT_SECRET", "dummy-secret-for-test")
    monkeypatch.delenv("GRAPH_CERT_PATH", raising=False)

    captured: list[dict] = []

    def fake_run_pipeline(cfg, out_dir, redact, **kwargs):
        captured.append(
            {"tenant": cfg.tenant_id, "out": out_dir, "redact": redact, "kwargs": kwargs}
        )
        return 0

    monkeypatch.setattr("m365_posture.cli.run_pipeline", fake_run_pipeline)

    code = main(["run", "--out", str(tmp_path)])
    assert code == 0
    assert len(captured) == 1
    assert captured[0]["tenant"] == "11111111-1111-1111-1111-111111111111"
    assert captured[0]["out"] == Path(tmp_path).resolve()
    assert captured[0]["redact"] is False


def test_main_run_passes_redact(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TENANT_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("CLIENT_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("CLIENT_SECRET", "dummy-secret-for-test")

    captured: list[bool] = []

    def fake_run_pipeline(cfg, out_dir, redact, **kwargs):
        captured.append(redact)
        return 0

    monkeypatch.setattr("m365_posture.cli.run_pipeline", fake_run_pipeline)
    assert main(["run", "--out", str(tmp_path), "--redact"]) == 0
    assert captured == [True]


def test_main_config_error_exits_before_pipeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TENANT_ID", raising=False)
    monkeypatch.delenv("CLIENT_ID", raising=False)

    called: list[bool] = []

    def fake_run_pipeline(*_a, **_k):
        called.append(True)
        return 0

    monkeypatch.setattr("m365_posture.cli.run_pipeline", fake_run_pipeline)
    assert main(["run", "--out", str(tmp_path)]) == 1
    assert called == []


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_run_pipeline_writes_reports_with_stub_credential(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TENANT_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("CLIENT_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("CLIENT_SECRET", "dummy-secret-for-test")
    monkeypatch.setenv("CHAPTER_GUESTS", "true")
    monkeypatch.setenv("CHAPTER_PRIVILEGED", "false")
    monkeypatch.setenv("CHAPTER_APPLICATIONS", "false")
    monkeypatch.setenv("CHAPTER_DEVICES", "false")
    monkeypatch.setenv("CHAPTER_SIGNIN_RISK", "false")

    class _Cred:
        def get_token(self, *_scope, **_kwargs):
            return type("T", (), {"token": "stub"})()

    monkeypatch.setattr(
        "m365_posture.cli.execute_graph_get",
        lambda url, _getter: {"value": []},
    )

    cfg = load_config()
    code = run_pipeline(
        cfg, tmp_path, False, credential_factory=lambda _c: _Cred()
    )
    assert code == 0
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "report.html").is_file()
    logs = list((tmp_path / "runs").glob("*.log"))
    assert len(logs) == 1
