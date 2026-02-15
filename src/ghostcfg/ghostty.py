"""Interface to the ghostty CLI and process management."""

from __future__ import annotations

import os
import platform
import signal
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


@dataclass
class ThemePalette:
    """Parsed color palette from a Ghostty theme file."""

    background: str = "#000000"
    foreground: str = "#ffffff"
    cursor_color: str = ""
    selection_background: str = ""
    ansi: list[str] = field(default_factory=lambda: [""] * 16)


def get_theme_dirs() -> list[Path]:
    """Return theme search directories in priority order."""
    dirs: list[Path] = []
    if platform.system() == "Darwin":
        dirs.append(
            Path.home()
            / "Library"
            / "Application Support"
            / "com.mitchellh.ghostty"
            / "themes"
        )
        dirs.append(
            Path("/Applications/Ghostty.app/Contents/Resources/ghostty/themes")
        )
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        dirs.append(Path(xdg) / "ghostty" / "themes")
        dirs.append(Path("/usr/share/ghostty/themes"))
        dirs.append(Path("/usr/local/share/ghostty/themes"))
    return dirs


def get_theme_file(name: str) -> Path | None:
    """Search theme directories for a file matching the given theme name."""
    for d in get_theme_dirs():
        candidate = d / name
        if candidate.is_file():
            return candidate
    return None


@lru_cache(maxsize=128)
def parse_theme_file(name: str) -> ThemePalette | None:
    """Parse a Ghostty theme file and return its palette, or None if not found."""
    path = get_theme_file(name)
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    palette = ThemePalette()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "background":
            palette.background = value
        elif key == "foreground":
            palette.foreground = value
        elif key == "cursor-color":
            palette.cursor_color = value
        elif key == "selection-background":
            palette.selection_background = value
        elif key == "palette":
            # Format: "index=color" e.g. "0=#1d1f21"
            if "=" in value:
                idx_str, _, color = value.partition("=")
                try:
                    idx = int(idx_str)
                    if 0 <= idx <= 15:
                        palette.ansi[idx] = color
                except ValueError:
                    pass
    return palette


def get_config_path() -> Path:
    """Detect the Ghostty config file path based on platform."""
    if platform.system() == "Darwin":
        p = Path.home() / "Library" / "Application Support" / "com.mitchellh.ghostty" / "config"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        p = Path(xdg) / "ghostty" / "config"
    return p


def list_themes() -> list[str]:
    """Run ghostty +list-themes --plain and return sorted list of theme names."""
    try:
        result = subprocess.run(
            ["ghostty", "+list-themes", "--plain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        themes = []
        for line in result.stdout.strip().splitlines():
            # Format: "Theme Name (resources)" or "Theme Name (user)"
            name = line.strip()
            for suffix in ("(resources)", "(user)"):
                if name.endswith(suffix):
                    name = name[: -len(suffix)].strip()
                    break
            if name:
                themes.append(name)
        return themes
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def get_config_with_docs() -> dict[str, dict]:
    """Run ghostty +show-config --docs and parse into structured dict.

    Returns dict of {option_name: {"value": str, "doc": str}}.
    Repeatable options (like palette, keybind) collect all values into a list.
    """
    try:
        result = subprocess.run(
            ["ghostty", "+show-config", "--docs"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}

    options: dict[str, dict] = {}
    current_doc_lines: list[str] = []

    for line in result.stdout.splitlines():
        if line.startswith("# "):
            current_doc_lines.append(line[2:])
        elif line == "#":
            current_doc_lines.append("")
        elif "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            doc = "\n".join(current_doc_lines).strip()
            current_doc_lines = []

            if key in options:
                # Repeatable option — collect values into a list
                existing = options[key]
                if isinstance(existing["value"], list):
                    existing["value"].append(value)
                else:
                    existing["value"] = [existing["value"], value]
            else:
                options[key] = {"value": value, "doc": doc}
        else:
            current_doc_lines = []

    return options


def get_ghostty_pids() -> list[int]:
    """Find running Ghostty process IDs.

    Uses -a flag because ghostcfg typically runs inside Ghostty, making
    Ghostty an ancestor process — pgrep excludes ancestors by default.
    """
    for pgrep_args in (
        ["pgrep", "-a", "-x", "ghostty"],
        ["pgrep", "-a", "ghostty"],
    ):
        try:
            result = subprocess.run(
                pgrep_args,
                capture_output=True,
                text=True,
                timeout=5,
            )
            pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
            if pids:
                return pids
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            continue
    return []


def reload_config() -> bool:
    """Send SIGUSR2 to Ghostty to trigger config reload. Returns True on success."""
    pids = get_ghostty_pids()
    if not pids:
        return False
    for pid in pids:
        try:
            os.kill(pid, signal.SIGUSR2)
        except (ProcessLookupError, PermissionError):
            continue
    return True


def list_fonts() -> list[str]:
    """List installed monospace fonts available for use in Ghostty."""
    fonts: set[str] = set()

    if platform.system() == "Darwin":
        # macOS: use system_profiler or fc-list
        try:
            # Try fc-list first (if fontconfig is installed via Homebrew)
            result = subprocess.run(
                ["fc-list", ":spacing=mono", "family"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    # fc-list returns "Family Name" or "Family,AltName"
                    name = line.split(",")[0].strip()
                    if name:
                        fonts.add(name)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Also try atsutil for macOS native fonts
        if not fonts:
            try:
                result = subprocess.run(
                    ["atsutil", "fonts", "-list"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                # Filter for common monospace font names
                mono_hints = ["mono", "code", "consol", "courier", "menlo", "sf mono",
                             "hack", "fira", "source", "jetbrains", "iosevka", "input"]
                for line in result.stdout.strip().splitlines():
                    name = line.strip()
                    if any(hint in name.lower() for hint in mono_hints):
                        fonts.add(name)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    else:
        # Linux: use fc-list
        try:
            result = subprocess.run(
                ["fc-list", ":spacing=mono", "family"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.strip().splitlines():
                name = line.split(",")[0].strip()
                if name:
                    fonts.add(name)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Add common fallbacks that are likely available
    common = ["SF Mono", "Menlo", "Monaco", "Courier New", "JetBrains Mono",
              "Fira Code", "Source Code Pro", "Hack", "Inconsolata"]
    for f in common:
        fonts.add(f)

    return sorted(fonts, key=str.lower)
