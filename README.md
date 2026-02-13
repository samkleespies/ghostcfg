# ghostcfg

A TUI for editing your [Ghostty](https://ghostty.org) config without touching the file by hand.

Browse 200+ options by category, preview themes live with color swatches, and save — ghostcfg hot-reloads your running Ghostty instance automatically.

## Install

```bash
pip install ghostcfg
```

Or from source:

```bash
git clone https://github.com/samkleespies/ghostcfg.git
cd ghostcfg
pip install -e .
```

Requires Python 3.10+ and [Ghostty](https://ghostty.org) on PATH.

## Usage

```bash
ghostcfg   # or: gcfg
```

### Keybindings

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Switch tabs |
| `Up` / `Down` | Navigate options |
| `Enter` | Edit / toggle |
| `Ctrl+S` | Save and reload Ghostty |
| `Ctrl+D` | Reset option to default |
| `?` | Help |
| `q` | Quit |

In the theme browser:

| Key | Action |
|-----|--------|
| `Up` / `Down` | Browse (previews live) |
| `Enter` | Confirm theme |
| `Escape` | Revert to original |
| `d` / `l` / `a` | Dark only / light only / all |

## What it does

- Tabbed categories: Font, Colors, Cursor, Window, Background, Input, Shell, Advanced
- Theme browser with inline color swatch preview, search, and dark/light filtering
- Type-aware widgets: toggles for booleans, dropdowns for enums, color pickers, validated number fields
- Saves trigger SIGUSR2 so Ghostty reloads instantly
- Roundtrip-safe: your comments, blank lines, and ordering are preserved
- Platform-aware: only shows options for your OS

ghostcfg finds your config at:
- **macOS:** `~/Library/Application Support/com.mitchellh.ghostty/config`
- **Linux:** `~/.config/ghostty/config`

## License

MIT
