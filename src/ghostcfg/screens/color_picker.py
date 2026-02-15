"""Color picker modal screen — HSB hue bar + saturation/brightness grid."""

from __future__ import annotations

import colorsys

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

SB_COLS = 24
SB_ROWS = 12
HUE_CELLS = 24


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _rgb_to_hsv(hex_color: str) -> tuple[float, float, float]:
    c = Color.parse(hex_color)
    return colorsys.rgb_to_hsv(c.r / 255, c.g / 255, c.b / 255)


def _cell_text(hex_color: str, selected: bool = False) -> Text:
    if selected:
        return Text("▏▕", style=f"white on {hex_color}")
    return Text("  ", style=f"on {hex_color}")


class SBCell(Static):
    def __init__(self, col: int, row: int) -> None:
        super().__init__("", classes="sb-cell")
        self.col = col
        self.row = row
        self.hex_color = "#000000"

    def on_mount(self) -> None:
        screen = self.screen
        if isinstance(screen, ColorPickerScreen):
            s = (self.col + 0.5) / SB_COLS
            v = 1.0 - (self.row + 0.5) / SB_ROWS
            self.hex_color = _hsv_to_hex(screen._hue, s, v)
            self.update(_cell_text(self.hex_color))

    def on_click(self) -> None:
        screen = self.screen
        if isinstance(screen, ColorPickerScreen):
            screen.select_color(self.hex_color)


class HueCell(Static):
    def __init__(self, index: int) -> None:
        super().__init__("", classes="hue-cell")
        self.hue_index = index
        self.hue_value = index / HUE_CELLS
        self.hex_color = _hsv_to_hex(self.hue_value, 1.0, 1.0)

    def on_mount(self) -> None:
        self.update(_cell_text(self.hex_color))

    def on_click(self) -> None:
        screen = self.screen
        if isinstance(screen, ColorPickerScreen):
            screen.set_hue(self.hue_value)


class ColorPickerScreen(ModalScreen[str]):
    """Modal color picker with HSB hue bar and saturation/brightness grid."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Select", show=True, priority=True),
    ]

    def __init__(self, current_color: str = "") -> None:
        super().__init__()
        self._current_color = current_color.strip() or "#ffffff"
        try:
            h, s, v = _rgb_to_hsv(self._current_color)
        except Exception:
            h, s, v = 0.0, 0.0, 1.0
        self._hue = h
        self._sat = s
        self._val = v
        self._last_set_hex: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="color-picker-dialog"):
            yield Label("Pick a color", id="picker-title")
            yield Static("", id="color-preview")
            yield Label(self._current_color, id="color-preview-hex")
            with Vertical(id="sb-grid"):
                for row in range(SB_ROWS):
                    with Horizontal(classes="sb-row"):
                        for col in range(SB_COLS):
                            yield SBCell(col, row)
            with Horizontal(id="hue-bar"):
                for i in range(HUE_CELLS):
                    yield HueCell(i)
            with Horizontal(id="picker-hex-row"):
                yield Label("Hex: ", id="picker-hex-label")
                yield Input(
                    value=self._current_color,
                    placeholder="#rrggbb",
                    id="picker-hex-input",
                )
            with Horizontal(id="picker-footer"):
                yield Button("Select", id="picker-select-btn", variant="primary")
                yield Button("Cancel", id="picker-cancel-btn")
            yield Label("Enter to select, Escape to cancel", id="picker-hint")

    def on_mount(self) -> None:
        self._update_preview(self._current_color)
        self._highlight_hue_cell()
        self._highlight_sb_cell()

    def set_hue(self, hue: float) -> None:
        self._hue = hue
        self._rebuild_sb_grid()
        self._highlight_hue_cell()
        hex_color = _hsv_to_hex(self._hue, self._sat, self._val)
        self._select_and_update(hex_color)

    def select_color(self, hex_color: str) -> None:
        try:
            _h, s, v = _rgb_to_hsv(hex_color)
            self._sat = s
            self._val = v
        except Exception:
            pass
        self._select_and_update(hex_color)
        self._highlight_sb_cell()

    def _select_and_update(self, hex_color: str) -> None:
        self._current_color = hex_color
        self._update_preview(hex_color)
        self._last_set_hex = hex_color
        try:
            self.query_one("#picker-hex-input", Input).value = hex_color
        except Exception:
            pass

    def _rebuild_sb_grid(self) -> None:
        """Rebuild all cell colors for current hue, including selection."""
        best_col = max(0, min(SB_COLS - 1, round(self._sat * SB_COLS - 0.5)))
        best_row = max(0, min(SB_ROWS - 1, round((1.0 - self._val) * SB_ROWS - 0.5)))
        for cell in self.query(SBCell):
            s = (cell.col + 0.5) / SB_COLS
            v = 1.0 - (cell.row + 0.5) / SB_ROWS
            hex_color = _hsv_to_hex(self._hue, s, v)
            cell.hex_color = hex_color
            selected = cell.col == best_col and cell.row == best_row
            cell.update(_cell_text(hex_color, selected))

    def _highlight_hue_cell(self) -> None:
        best_idx = round(self._hue * HUE_CELLS) % HUE_CELLS
        for cell in self.query(HueCell):
            cell.update(_cell_text(cell.hex_color, cell.hue_index == best_idx))

    def _highlight_sb_cell(self) -> None:
        best_col = max(0, min(SB_COLS - 1, round(self._sat * SB_COLS - 0.5)))
        best_row = max(0, min(SB_ROWS - 1, round((1.0 - self._val) * SB_ROWS - 0.5)))
        for cell in self.query(SBCell):
            selected = cell.col == best_col and cell.row == best_row
            cell.update(_cell_text(cell.hex_color, selected))

    def _update_preview(self, color: str) -> None:
        self._current_color = color
        try:
            self.query_one("#color-preview", Static).styles.background = color
        except Exception:
            pass
        try:
            self.query_one("#color-preview-hex", Label).update(color)
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "picker-hex-input":
            val = event.value.strip()
            if val == self._last_set_hex:
                self._last_set_hex = None
                return
            try:
                Color.parse(val)
                self._update_preview(val)
                h, s, v = _rgb_to_hsv(val)
                self._hue = h
                self._sat = s
                self._val = v
                self._rebuild_sb_grid()
                self._highlight_hue_cell()
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "picker-select-btn":
            self.dismiss(self._current_color)
        elif event.button.id == "picker-cancel-btn":
            self.dismiss("")

    def action_confirm(self) -> None:
        self.dismiss(self._current_color)

    def action_cancel(self) -> None:
        self.dismiss("")
