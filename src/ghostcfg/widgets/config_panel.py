"""Category-based config editor panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Label, Rule

from ghostcfg.schema import get_options_for_category, is_repeatable
from ghostcfg.widgets.option_row import OptionRow


class ConfigPanel(Widget):
    """Renders all options for a single category with a description pane."""

    def __init__(
        self,
        category: str,
        config_values: dict[str, str],
        docs: dict[str, str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.category = category
        self.config_values = config_values
        self.docs = docs
        self._option_rows: dict[str, OptionRow] = {}

    def compose(self) -> ComposeResult:
        options = get_options_for_category(self.category)
        with Vertical(classes="config-panel"):
            with VerticalScroll(classes="options-scroll"):
                for name, meta in options:
                    # Skip repeatable options like palette/keybind (too complex for simple rows)
                    if is_repeatable(name) and name in (
                        "palette",
                        "keybind",
                        "command-palette-entry",
                    ):
                        continue
                    current = str(self.config_values.get(name, meta.get("default", "")))
                    doc = self.docs.get(name, "")
                    row = OptionRow(
                        key=name,
                        meta=meta,
                        current_value=current,
                        config_values=self.config_values,
                        doc=doc,
                        id=f"row-{name}",
                    )
                    self._option_rows[name] = row
                    yield row
            yield Rule()
            yield Label(
                "Select an option to see its description.",
                id="doc-pane",
                classes="doc-pane",
            )

    def on_option_row_option_focused(self, event: OptionRow.OptionFocused) -> None:
        doc_pane = self.query_one("#doc-pane", Label)
        text = (
            f"[bold]{event.key}[/bold]\n\n{event.doc}"
            if event.doc
            else f"[bold]{event.key}[/bold]"
        )
        doc_pane.update(text)

    def get_modified_values(self) -> dict[str, str]:
        """Return dict of {key: new_value} for all modified options."""
        modified = {}
        for name, row in self._option_rows.items():
            if row.is_modified:
                modified[name] = row.current_value
        return modified

    def reset_option(self, key: str) -> None:
        """Reset a specific option to its default."""
        if key in self._option_rows:
            self._option_rows[key].reset_to_default()
