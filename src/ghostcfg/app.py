"""Main Textual App for ghostcfg."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Input, TabbedContent, TabPane

from ghostcfg.config_io import GhosttyConfig, backup_config, read_config, write_config
from ghostcfg.ghostty import (
    get_config_path,
    get_config_with_docs,
    list_themes,
    reload_config,
)
from ghostcfg.schema import CATEGORIES
from ghostcfg.screens.color_picker import ColorPickerScreen
from ghostcfg.screens.help_screen import HelpScreen
from ghostcfg.widgets.config_panel import ConfigPanel
from ghostcfg.widgets.option_row import OptionRow
from ghostcfg.widgets.theme_browser import ThemeBrowser

# Color keys that themes control — remove these when applying a theme
# so the theme's colors take effect instead of being overridden.
THEME_COLOR_KEYS = {
    "background",
    "foreground",
    "bold-color",
    "cursor-color",
    "cursor-text",
    "selection-foreground",
    "selection-background",
    "split-divider-color",
    "unfocused-split-fill",
    "window-titlebar-background",
    "window-titlebar-foreground",
}


class GhostCfg(App):
    """Interactive TUI for Ghostty configuration."""

    TITLE = "ghostcfg"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", show=True, priority=True),
        Binding("question_mark", "help", "Help", show=True),
        Binding("q", "quit_app", "Quit", show=True),
        Binding("ctrl+d", "reset_default", "Default", show=True),
    ]

    has_unsaved: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self._config_path: Path = get_config_path()
        self._config: GhosttyConfig = GhosttyConfig()
        self._themes: list[str] = []
        self._docs: dict[str, str] = {}
        self._config_values: dict[str, str] = {}
        self._original_theme: str = ""
        self._theme_ready = False

    def compose(self) -> ComposeResult:
        self._load_data()
        with TabbedContent(id="tabs"):
            with TabPane("Themes", id="tab-themes"):
                # Pass empty list; ThemeBrowser is populated in on_mount
                # to avoid reentrancy in its reactive watchers.
                yield ThemeBrowser([], id="theme-browser")
            for category in CATEGORIES:
                tab_id = f"tab-{category.lower()}"
                with TabPane(category, id=tab_id):
                    yield ConfigPanel(
                        category=category,
                        config_values=self._config_values,
                        docs=self._docs,
                        id=f"panel-{category.lower()}",
                    )
        yield Footer()

    def on_mount(self) -> None:
        try:
            browser = self.query_one("#theme-browser", ThemeBrowser)
            browser.all_themes = self._themes
            browser.set_original_theme(self._original_theme)
            browser._refresh_list()
        except Exception:
            pass
        self.call_after_refresh(self._enable_theme_preview)

    def _enable_theme_preview(self) -> None:
        """Allow theme live-preview after initial UI settlement."""
        self._theme_ready = True

    def _load_data(self) -> None:
        """Load themes, config, and docs from Ghostty."""
        self._themes = list_themes()
        self._config = read_config(self._config_path)
        cli_data = get_config_with_docs()

        for name, data in cli_data.items():
            self._docs[name] = data.get("doc", "")
            file_val = self._config.get(name)
            if file_val is not None:
                self._config_values[name] = file_val
            else:
                val = data.get("value", "")
                if isinstance(val, list):
                    self._config_values[name] = ", ".join(val)
                else:
                    self._config_values[name] = val

        self._original_theme = self._config_values.get("theme", "")

    # ── Theme browser handlers ────────────────────────────

    def on_theme_browser_theme_highlighted(
        self, event: ThemeBrowser.ThemeHighlighted
    ) -> None:
        """Live preview: instantly apply theme on cursor movement."""
        if not self._theme_ready:
            return
        self._apply_theme(event.theme)

    def on_theme_browser_theme_selected(
        self, event: ThemeBrowser.ThemeSelected
    ) -> None:
        """Confirm theme selection."""
        self._original_theme = event.theme
        self.notify(f"Theme: {event.theme}")

    def on_theme_browser_theme_reverted(
        self, event: ThemeBrowser.ThemeReverted
    ) -> None:
        """Revert to original theme on Escape."""
        self._apply_theme(self._original_theme)

    def _apply_theme(self, theme: str) -> None:
        """Apply a theme: set it in config, remove conflicting color overrides, save + reload."""
        backup_config(self._config)
        self._config.set("theme", theme)
        # Remove explicit color keys that would override the theme
        for key in THEME_COLOR_KEYS:
            self._config.remove(key)
        # Also remove palette overrides
        self._config.remove("palette")
        try:
            write_config(self._config)
            reload_config()
        except Exception as e:
            self.notify(f"Theme apply failed: {e}", severity="error")

    # ── Config editor handlers ────────────────────────────

    def on_option_row_value_changed(self, event: OptionRow.ValueChanged) -> None:
        """Update unsaved indicator when any option changes."""
        self.has_unsaved = bool(self._collect_changes())

    def on_option_row_color_picker_requested(
        self, event: OptionRow.ColorPickerRequested
    ) -> None:
        """Open the color picker modal for a color option."""
        # Extract values immediately - event may not persist properly
        key = event.key
        current_color = event.current_value

        def on_color_selected(color: str) -> None:
            if color:
                try:
                    input_widget = self.query_one(f"#opt-{key}", Input)
                    input_widget.value = color
                except Exception:
                    pass
        self.push_screen(ColorPickerScreen(current_color), callback=on_color_selected)

    # ── Persistence ───────────────────────────────────────

    def _collect_changes(self) -> dict[str, str]:
        """Collect all modified values directly from widgets."""
        changes: dict[str, str] = {}
        for panel in self.query(ConfigPanel):
            changes.update(panel.get_modified_values())
        return changes

    def action_save(self) -> None:
        """Save all pending changes to config file and reload."""
        changes = self._collect_changes()
        if not changes:
            self.notify("No changes to save.")
            return

        backup_config(self._config)

        for key, value in changes.items():
            if value:
                self._config.set(key, value)
            else:
                self._config.remove(key)

        try:
            write_config(self._config)
            reloaded = reload_config()

            for key, value in changes.items():
                self._config_values[key] = value
                try:
                    row = self.query_one(f"#row-{key}", OptionRow)
                    row.update_original_value(value)
                except Exception:
                    pass

            self.has_unsaved = False

            if reloaded:
                self.notify("Config saved and reloaded!")
            else:
                self.notify(
                    "Saved, but Ghostty reload failed (PID not found).",
                    severity="warning",
                )

        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    # ── Actions ───────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit_app(self) -> None:
        if self.has_unsaved:
            self.notify(
                "Unsaved changes! Press Ctrl+S to save, or q again to force quit."
            )
            self._force_quit_pending = getattr(self, "_force_quit_pending", False)
            if self._force_quit_pending:
                self.exit()
            else:
                self._force_quit_pending = True
        else:
            self.exit()

    def action_reset_default(self) -> None:
        """Reset the currently focused option to its default value."""
        focused = self.focused
        if focused is None:
            return
        widget = focused
        while widget is not None and not isinstance(widget, OptionRow):
            widget = widget.parent
        if isinstance(widget, OptionRow):
            widget.reset_to_default()
            self.notify(f"Reset {widget.key} to default")

    def watch_has_unsaved(self, value: bool) -> None:
        """Update header to show modified indicator."""
        self.sub_title = "[modified]" if value else ""


def main() -> None:
    app = GhostCfg()
    app.run()


if __name__ == "__main__":
    main()
