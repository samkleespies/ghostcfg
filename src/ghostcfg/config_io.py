"""Read, write, and backup the Ghostty config file.

Preserves comments, blank lines, and key ordering on round-trip.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConfigEntry:
    """A single line/entry in the config file."""

    kind: str  # "option", "comment", "blank"
    key: str = ""
    value: str = ""
    raw: str = ""  # original line text for comments/blanks


@dataclass
class GhosttyConfig:
    """Parsed Ghostty config preserving structure."""

    entries: list[ConfigEntry] = field(default_factory=list)
    path: Path | None = None
    _backed_up: bool = False

    def get(self, key: str) -> str | None:
        """Get the value of an option (last occurrence wins for non-repeatable)."""
        for entry in reversed(self.entries):
            if entry.kind == "option" and entry.key == key:
                return entry.value
        return None

    def get_all(self, key: str) -> list[str]:
        """Get all values for a repeatable option."""
        return [e.value for e in self.entries if e.kind == "option" and e.key == key]

    def set(self, key: str, value: str) -> None:
        """Set an option value. Updates existing entry or appends new one."""
        for entry in self.entries:
            if entry.kind == "option" and entry.key == key:
                entry.value = value
                return
        # Not found — append
        self.entries.append(ConfigEntry(kind="option", key=key, value=value))

    def remove(self, key: str) -> None:
        """Remove all entries for a given key."""
        self.entries = [
            e for e in self.entries if not (e.kind == "option" and e.key == key)
        ]

    def set_repeatable(self, key: str, values: list[str]) -> None:
        """Replace all entries for a repeatable option with new values."""
        self.remove(key)
        for v in values:
            self.entries.append(ConfigEntry(kind="option", key=key, value=v))

    def to_text(self) -> str:
        """Serialize config back to text, preserving structure."""
        lines = []
        for entry in self.entries:
            if entry.kind == "comment" or entry.kind == "blank":
                lines.append(entry.raw)
            elif entry.kind == "option":
                # Quote values that are empty-looking or have leading/trailing spaces
                value = entry.value
                if value != value.strip() or value == "":
                    value = f'"{value}"'
                lines.append(f"{entry.key} = {value}")
        # Ensure trailing newline
        text = "\n".join(lines)
        if text and not text.endswith("\n"):
            text += "\n"
        return text

    def modified_keys(self, original: "GhosttyConfig") -> set[str]:
        """Return set of keys whose values differ from original."""
        changed = set()
        all_keys = {e.key for e in self.entries if e.kind == "option"}
        all_keys |= {e.key for e in original.entries if e.kind == "option"}
        for key in all_keys:
            if self.get_all(key) != original.get_all(key):
                changed.add(key)
        return changed


def parse_config(text: str) -> GhosttyConfig:
    """Parse a Ghostty config file string into a GhosttyConfig."""
    config = GhosttyConfig()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            config.entries.append(ConfigEntry(kind="blank", raw=line))
        elif stripped.startswith("#"):
            config.entries.append(ConfigEntry(kind="comment", raw=line))
        elif "=" in stripped:
            key, _, value = stripped.partition("=")
            # Preserve quoted values (including spaces)
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                # Keep the inner content, preserving spaces
                value = value[1:-1]
            config.entries.append(
                ConfigEntry(kind="option", key=key.strip(), value=value)
            )
        else:
            # Unknown line — preserve as comment
            config.entries.append(ConfigEntry(kind="comment", raw=line))
    return config


def read_config(path: Path) -> GhosttyConfig:
    """Read and parse a Ghostty config file."""
    if not path.exists():
        config = GhosttyConfig()
        config.path = path
        return config
    text = path.read_text()
    config = parse_config(text)
    config.path = path
    return config


def write_config(config: GhosttyConfig, path: Path | None = None) -> None:
    """Write config to file, creating parent dirs if needed."""
    p = path or config.path
    if p is None:
        raise ValueError("No path specified")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(config.to_text())


def backup_config(config: GhosttyConfig) -> Path | None:
    """Create a backup of the config file. Returns backup path or None."""
    if config._backed_up or config.path is None or not config.path.exists():
        return None
    backup_path = config.path.with_suffix(".bak")
    shutil.copy2(config.path, backup_path)
    config._backed_up = True
    return backup_path
