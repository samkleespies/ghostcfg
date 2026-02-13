"""Searchable theme browser with live preview."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option


class ThemeBrowser(Widget):
    """Theme browser with search and live preview."""

    BINDINGS = [
        Binding("escape", "revert", "Revert", show=True),
        Binding("d", "filter_dark", "Dark only", show=False),
        Binding("l", "filter_light", "Light only", show=False),
        Binding("a", "filter_all", "All themes", show=False),
    ]

    filter_text: reactive[str] = reactive("", layout=False)
    filter_mode: reactive[str] = reactive("all")  # "all", "dark", "light"

    class ThemeHighlighted(Message):
        """Sent when a theme is highlighted (for live preview)."""

        def __init__(self, theme: str) -> None:
            self.theme = theme
            super().__init__()

    class ThemeSelected(Message):
        """Sent when a theme is confirmed with Enter."""

        def __init__(self, theme: str) -> None:
            self.theme = theme
            super().__init__()

    class ThemeReverted(Message):
        """Sent when user presses Escape to revert."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, themes: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.all_themes = themes
        self._original_theme: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-container"):
            yield Input(placeholder="Search themes...", id="theme-search")
            yield OptionList(id="theme-list")
            yield Label("", id="theme-count")

    def set_original_theme(self, theme: str) -> None:
        """Set the theme to revert to on Escape."""
        self._original_theme = theme

    def _filtered_themes(self) -> list[str]:
        """Get themes filtered by search text and dark/light mode."""
        themes = self.all_themes
        if self.filter_text:
            query = self.filter_text.lower()
            themes = [t for t in themes if query in t.lower()]
        if self.filter_mode == "dark":
            themes = [t for t in themes if self._is_dark_theme(t)]
        elif self.filter_mode == "light":
            themes = [t for t in themes if self._is_light_theme(t)]
        return themes

    @staticmethod
    def _is_dark_theme(name: str) -> bool:
        """Heuristic: theme is likely dark if name doesn't suggest light."""
        lower = name.lower()
        light_keywords = ["light", "latte", "day", "dawn", "morning", "white", "paper"]
        return not any(kw in lower for kw in light_keywords)

    @staticmethod
    def _is_light_theme(name: str) -> bool:
        """Heuristic: theme is likely light."""
        lower = name.lower()
        light_keywords = ["light", "latte", "day", "dawn", "morning", "white", "paper"]
        return any(kw in lower for kw in light_keywords)

    def _refresh_list(self) -> None:
        """Rebuild the option list based on current filters."""
        option_list = self.query_one("#theme-list", OptionList)
        option_list.clear_options()
        filtered = self._filtered_themes()
        for theme in filtered:
            option_list.add_option(Option(theme, id=theme))
        count_label = self.query_one("#theme-count", Label)
        total = len(self.all_themes)
        shown = len(filtered)
        mode_label = ""
        if self.filter_mode == "dark":
            mode_label = " dark"
        elif self.filter_mode == "light":
            mode_label = " light"
        count_label.update(f"{shown} of {total}{mode_label} themes")

        # Restore selection to original theme if visible
        if self._original_theme and self._original_theme in filtered:
            index = filtered.index(self._original_theme)
            option_list.highlighted = index

    def watch_filter_text(self) -> None:
        self._refresh_list()

    def watch_filter_mode(self) -> None:
        self._refresh_list()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "theme-search":
            self.filter_text = event.value

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        if event.option is not None:
            theme = str(event.option.prompt)
            self.post_message(self.ThemeHighlighted(theme))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option is not None:
            theme = str(event.option.prompt)
            self.post_message(self.ThemeSelected(theme))

    def action_revert(self) -> None:
        self.post_message(self.ThemeReverted())

    def action_filter_dark(self) -> None:
        self.filter_mode = "dark" if self.filter_mode != "dark" else "all"

    def action_filter_light(self) -> None:
        self.filter_mode = "light" if self.filter_mode != "light" else "all"

    def action_filter_all(self) -> None:
        self.filter_mode = "all"

    def focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#theme-search", Input).focus()
