"""功能：验证 CLI 默认窗口和显式窗口参数的优先级。"""

from __future__ import annotations

from pathlib import Path

from config.settings import Settings
from livescholar import cli
from livescholar.models import SearchWindow


def test_cli_uses_240_hour_window_by_default(monkeypatch) -> None:
    captured: dict[str, SearchWindow] = {}

    def fake_run_pipeline(settings, window, output_dir):
        captured["window"] = window
        return Path("report.md"), "body", [], []

    monkeypatch.setattr(cli, "load_settings", lambda path: Settings())
    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(cli, "write_run_log", lambda search_log, papers, window, log_dir: Path("run.log"))

    assert cli.main(["manual", "--dry-run"]) == 0
    window = captured["window"]
    assert (window.end - window.start).total_seconds() == 240 * 60 * 60


def test_cli_window_hours_overrides_default(monkeypatch) -> None:
    captured: dict[str, SearchWindow] = {}

    def fake_run_pipeline(settings, window, output_dir):
        captured["window"] = window
        return Path("report.md"), "body", [], []

    monkeypatch.setattr(cli, "load_settings", lambda path: Settings())
    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(cli, "write_run_log", lambda search_log, papers, window, log_dir: Path("run.log"))

    assert cli.main(["run", "--dry-run", "--window-hours", "12"]) == 0
    window = captured["window"]
    assert (window.end - window.start).total_seconds() == 12 * 60 * 60
