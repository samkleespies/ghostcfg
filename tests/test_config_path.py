"""Config discovery uses temporary directories, never the user's files."""
from pathlib import Path

import pytest

from ghostcfg.ghostty import get_config_path


@pytest.mark.parametrize("system", ["Linux", "Darwin"])
def test_xdg_modern_and_legacy(monkeypatch, tmp_path, system):
    monkeypatch.setattr("ghostcfg.ghostty.platform.system", lambda: system)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "custom"))
    directory = tmp_path / "custom" / "ghostty"
    directory.mkdir(parents=True)
    modern = directory / "config.ghostty"
    modern.touch()
    assert get_config_path() == modern
    legacy = directory / "config"
    legacy.touch()
    assert get_config_path() == legacy


def test_macos_precedence(monkeypatch, tmp_path):
    monkeypatch.setattr("ghostcfg.ghostty.platform.system", lambda: "Darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    xdg = tmp_path / ".config" / "ghostty" / "config"
    xdg.parent.mkdir(parents=True)
    xdg.touch()
    mac = tmp_path / "Library/Application Support/com.mitchellh.ghostty/config.ghostty"
    mac.parent.mkdir(parents=True)
    mac.touch()
    assert get_config_path() == mac
    legacy = mac.with_name("config")
    legacy.touch()
    assert get_config_path() == legacy


@pytest.mark.parametrize("system, suffix", [
    ("Linux", ".config/ghostty/config.ghostty"),
    ("Darwin", "Library/Application Support/com.mitchellh.ghostty/config.ghostty"),
])
def test_new_config_default(monkeypatch, tmp_path, system, suffix):
    monkeypatch.setattr("ghostcfg.ghostty.platform.system", lambda: system)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    assert get_config_path() == tmp_path / suffix
