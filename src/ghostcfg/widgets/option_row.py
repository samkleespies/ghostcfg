"""Single config option row — adapts widget to option type."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Switch

from ghostcfg.ghostty import list_fonts

# Cache fonts list (expensive to compute)
_FONTS_CACHE: list[str] | None = None

def get_fonts() -> list[str]:
    """Get cached list of installed fonts."""
    global _FONTS_CACHE
    if _FONTS_CACHE is None:
        _FONTS_CACHE = list_fonts()
    return _FONTS_CACHE

# Keys that should use font dropdown
FONT_KEYS = {
    "font-family",
    "font-family-bold",
    "font-family-italic",
    "font-family-bold-italic",
    "window-title-font-family",
}


class OptionRow(Widget):
    """Renders a single config option with the appropriate input widget."""

    class ValueChanged(Message):
        """Sent when the user changes a value."""

        def __init__(self, key: str, value: str) -> None:
            self.key = key
            self.value = value
            super().__init__()

    class OptionFocused(Message):
        """Sent when this option row receives focus."""

        def __init__(self, key: str, doc: str) -> None:
            self.key = key
            self.doc = doc
            super().__init__()

    class ColorPickerRequested(Message):
        """Sent when the user clicks a color swatch."""

        def __init__(self, option_row: "OptionRow") -> None:
            self.option_row = option_row
            super().__init__()

        @property
        def key(self) -> str:
            return self.option_row.key

        @property
        def current_value(self) -> str:
            return self.option_row.current_value

    def __init__(
        self,
        key: str,
        meta: dict,
        current_value: str,
        doc: str,
        config_values: dict[str, str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.key = key
        self.meta = meta
        self.doc = doc
        self.config_values = config_values
        self.current_value = self._normalize_value(current_value, meta.get("type"))
        self._original_value = self.current_value

    def _normalize_value(self, value: str, opt_type: str | None) -> str:
        if opt_type == "boolean":
            return value.lower()
        return value

    @property
    def is_modified(self) -> bool:
        return self.current_value != self._original_value

    def update_original_value(self, new_value: str) -> None:
        """Update original value after a save, clearing modified state."""
        self._original_value = new_value
        self._update_modified_label()

    def compose(self) -> ComposeResult:
        opt_type = self.meta.get("type", "string")
        with Horizontal(classes="option-row"):
            modified = " *" if self.is_modified else ""
            yield Label(f"{self.key}{modified}", classes="option-label")
            if opt_type == "boolean":
                val = self.current_value.lower() in ("true", "1", "yes")
                yield Switch(value=val, id=f"opt-{self.key}", classes="option-widget")
            elif opt_type == "enum":
                values = self.meta.get("values", [])
                options = [(v, v) for v in values]
                yield Select(
                    options,
                    value=self.current_value
                    if self.current_value in values
                    else Select.BLANK,
                    id=f"opt-{self.key}",
                    classes="option-widget",
                    allow_blank=True,
                )
            elif opt_type == "color":
                with Horizontal(classes="color-input-row"):
                    yield Input(
                        value=self.current_value,
                        placeholder="#rrggbb",
                        id=f"opt-{self.key}",
                        classes="option-widget color-input",
                    )
                    yield Button("", id=f"swatch-{self.key}", classes="color-swatch")
            elif opt_type == "integer":
                yield Input(
                    value=self.current_value,
                    type="integer",
                    id=f"opt-{self.key}",
                    classes="option-widget",
                )
            elif opt_type == "float":
                yield Input(
                    value=self.current_value,
                    type="number",
                    id=f"opt-{self.key}",
                    classes="option-widget",
                )
            elif self.key in FONT_KEYS:
                # Font family dropdown
                fonts = get_fonts()
                options = [(f, f) for f in fonts]
                yield Select(
                    options,
                    value=self.current_value if self.current_value in fonts else Select.BLANK,
                    id=f"opt-{self.key}",
                    classes="option-widget",
                    allow_blank=True,
                )
            else:
                # string, path, duration, etc.
                yield Input(
                    value=self.current_value,
                    id=f"opt-{self.key}",
                    classes="option-widget",
                )

    def on_mount(self) -> None:
        self._update_color_swatch()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        new_val = "true" if event.value else "false"
        self.current_value = new_val
        self._notify_change()

    def on_select_changed(self, event: Select.Changed) -> None:
        new_val = str(event.value) if event.value != Select.BLANK else ""
        self.current_value = new_val
        self._notify_change()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.current_value = event.value
        self._update_color_swatch()
        self._notify_change()

    def on_focus(self) -> None:
        self.post_message(self.OptionFocused(self.key, self.doc))

    def on_descendant_focus(self, _event) -> None:
        self.post_message(self.OptionFocused(self.key, self.doc))

    def _notify_change(self) -> None:
        self._update_modified_label()
        self.post_message(self.ValueChanged(self.key, self.current_value))

    def _update_modified_label(self) -> None:
        try:
            label = self.query_one(".option-label", Label)
            modified = " *" if self.is_modified else ""
            label.update(f"{self.key}{modified}")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("swatch-"):
            event.stop()
            self.post_message(self.ColorPickerRequested(self))

    def _update_color_swatch(self) -> None:
        if self.meta.get("type") != "color":
            return
        try:
            swatch = self.query_one(f"#swatch-{self.key}", Button)
            val = self.current_value.strip()
            if val and (val.startswith("#") or val.startswith("rgb")):
                swatch.styles.background = val
            else:
                swatch.styles.background = "white"
        except Exception:
            pass

    def reset_to_default(self) -> None:
        """Reset this option to its default value."""
        default = self.meta.get("default", "")
        self.current_value = default
        opt_type = self.meta.get("type", "string")
        try:
            if opt_type == "boolean":
                widget = self.query_one(f"#opt-{self.key}", Switch)
                widget.value = default.lower() in ("true", "1", "yes")
            elif opt_type == "enum":
                widget = self.query_one(f"#opt-{self.key}", Select)
                values = self.meta.get("values", [])
                widget.value = default if default in values else Select.BLANK
            elif self.key in FONT_KEYS:
                widget = self.query_one(f"#opt-{self.key}", Select)
                fonts = get_fonts()
                widget.value = default if default in fonts else Select.BLANK
            else:
                widget = self.query_one(f"#opt-{self.key}", Input)
                widget.value = default
        except Exception:
            pass
        self._notify_change()
