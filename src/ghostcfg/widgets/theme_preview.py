"""Theme color preview panel."""

from __future__ import annotations

from rich.text import Text

from textual.widgets import Static


# Unicode full-block character used for color swatches
_BLOCK = "\u2588"


class ThemePreview(Static):
    """Displays a color swatch preview for a Ghostty theme."""

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)

    def show_theme(self, name: str, palette) -> None:
        """Update the preview with colors from a ThemePalette."""
        bg = palette.background or "#000000"
        fg = palette.foreground or "#ffffff"

        content = Text()

        # Theme name header
        content.append(f"  {name}  \n", style=f"{fg} on {bg} bold")
        content.append("\n")

        # Sample text
        content.append(f"  The quick brown fox  \n", style=f"{fg} on {bg}")
        content.append(f"  jumps over the lazy dog  \n", style=f"{fg} on {bg}")
        content.append("\n")

        # Normal colors (0-7)
        content.append("  ")
        for i in range(8):
            color = palette.ansi[i] if palette.ansi[i] else f"#{i * 2:01x}{i * 2:01x}{i * 2:01x}"
            content.append(_BLOCK * 4, style=color)
        content.append("\n")

        # Bright colors (8-15)
        content.append("  ")
        for i in range(8, 16):
            color = palette.ansi[i] if palette.ansi[i] else f"#{(i - 8) * 2 + 8:02x}{(i - 8) * 2 + 8:02x}{(i - 8) * 2 + 8:02x}"
            content.append(_BLOCK * 4, style=color)
        content.append("\n")

        self.update(content)

    def clear_preview(self) -> None:
        """Clear the preview display."""
        self.update("")
