"""Help overlay screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


HELP_TEXT = """\
[bold]ghostcfg[/bold] — Interactive Ghostty Configuration

[bold]Navigation[/bold]
  Tab / Shift+Tab    Cycle between tabs
  ↑ / ↓              Navigate options
  Enter              Edit / toggle option

[bold]Theme Browser[/bold]
  ↑ / ↓              Browse themes (live preview)
  Enter              Confirm theme
  Escape             Revert to original theme
  d                  Toggle dark-only filter
  l                  Toggle light-only filter
  a                  Show all themes

[bold]Config Editor[/bold]
  Ctrl+S             Save all changes + reload
  Ctrl+D             Reset focused option to default

[bold]General[/bold]
  ?                  Toggle this help
  q                  Quit (prompts if unsaved)

[dim]Press Escape or ? to close[/dim]
"""


class HelpScreen(ModalScreen):
    """Modal help overlay."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("question_mark", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="help-dialog"):
                yield Static(HELP_TEXT, id="help-text")
