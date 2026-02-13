# ghostcfg

An interactive TUI for editing [Ghostty](https://ghostty.org) terminal configuration.

Browse all 200+ config options by category, preview themes in real time, and save changes that hot-reload into your running Ghostty instance — no manual file editing or restarts needed.

## Features

- **Tabbed category browser** — Font, Colors, Cursor, Window, Background, Input, Shell, Advanced
- **Live theme preview** — browse themes with instant preview as you navigate; Enter to confirm, Escape to revert
- **Theme filtering** — filter by dark, light, or show all themes
- **Type-aware inputs** — toggles for booleans, dropdowns for enums, color swatches with a picker, validated text fields for numbers/strings
- **Hot-reload** — saves trigger SIGUSR2 to your running Ghostty process so changes take effect immediately
- **Roundtrip-safe** — preserves your comments, blank lines, and ordering when writing config
- **Platform-aware** — only shows options relevant to your OS (macOS / Linux)

## Requirements

- Python 3.10+
- [Ghostty](https://ghostty.org) installed and on PATH

## Install

```bash
pip install ghostcfg
```

Or install from source:

```bash
git clone https://github.com/YOUR_USERNAME/ghostcfg.git
cd ghostcfg
pip install -e .
```

## Usage

```bash
ghostcfg   # or: gcfg
```

### Keybindings

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Cycle between tabs |
| `Up` / `Down` | Navigate options |
| `Enter` | Edit / toggle option |
| `Ctrl+S` | Save all changes + reload Ghostty |
| `Ctrl+D` | Reset focused option to default |
| `?` | Toggle help overlay |
| `q` | Quit (prompts if unsaved) |

**Theme browser:**

| Key | Action |
|-----|--------|
| `Up` / `Down` | Browse themes (live preview) |
| `Enter` | Confirm theme |
| `Escape` | Revert to original theme |
| `d` / `l` / `a` | Filter: dark only / light only / all |

## How It Works

ghostcfg reads your Ghostty config file, presents it through a tabbed Textual interface, and writes changes back while preserving your existing formatting. When you save, it sends SIGUSR2 to your running Ghostty process to trigger a hot-reload.

Config file locations:
- **macOS:** `~/Library/Application Support/com.mitchellh.ghostty/config`
- **Linux:** `~/.config/ghostty/config`

## License

MIT
