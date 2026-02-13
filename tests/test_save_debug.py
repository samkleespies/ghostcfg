"""Tests for the save flow — verifies config changes persist to file."""

from pathlib import Path
from unittest.mock import patch

import pytest
from textual.widgets import Select

from ghostcfg.app import GhostCfg
from ghostcfg.config_io import read_config
from ghostcfg.widgets.option_row import OptionRow


SAMPLE_CONFIG = """\
# Font
font-size = 13

# Theme
theme = Catppuccin Mocha

# Cursor
cursor-style = underline
"""

MOCK_CLI_DATA = {
    "cursor-style": {"value": "bar", "doc": "The cursor style."},
    "font-size": {"value": "12", "doc": "Font size in points."},
    "theme": {"value": "Catppuccin Mocha", "doc": "Theme name."},
}


@pytest.fixture
def tmp_config(tmp_path):
    config_file = tmp_path / "config"
    config_file.write_text(SAMPLE_CONFIG)
    return config_file


def _make_app(tmp_config: Path) -> GhostCfg:
    """Create GhostCfg with config path pointing at temp file."""
    with patch("ghostcfg.app.get_config_path", return_value=tmp_config):
        return GhostCfg()


@pytest.mark.asyncio
async def test_save_changes_cursor_style(tmp_config):
    """Change cursor-style via Select widget, Ctrl+S, verify file is updated."""
    app = _make_app(tmp_config)

    with (
        patch("ghostcfg.app.list_themes", return_value=["Catppuccin Mocha", "Dracula"]),
        patch("ghostcfg.app.get_config_with_docs", return_value=MOCK_CLI_DATA),
        patch("ghostcfg.app.reload_config", return_value=True),
        patch("ghostcfg.app.backup_config"),
    ):
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            row = app.query_one("#row-cursor-style", OptionRow)
            assert row._original_value == "underline"
            assert row.current_value == "underline"
            assert not row.is_modified

            # Change via Select widget
            select_widget = row.query_one("#opt-cursor-style", Select)
            select_widget.value = "block"
            await pilot.pause()

            assert row.current_value == "block"
            assert row.is_modified

            changes = app._collect_changes()
            assert changes == {"cursor-style": "block"}

            # Save
            app.action_save()
            await pilot.pause()

            # Verify file
            saved_config = read_config(tmp_config)
            assert saved_config.get("cursor-style") == "block"
            assert not row.is_modified


@pytest.mark.asyncio
async def test_option_row_loads_file_value_not_default(tmp_config):
    """OptionRow should show the config file value, not the schema default."""
    app = _make_app(tmp_config)

    with (
        patch("ghostcfg.app.list_themes", return_value=[]),
        patch("ghostcfg.app.get_config_with_docs", return_value=MOCK_CLI_DATA),
        patch("ghostcfg.app.reload_config", return_value=True),
    ):
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # File has cursor-style=underline, schema default is "block"
            assert app._config_values["cursor-style"] == "underline"

            row = app.query_one("#row-cursor-style", OptionRow)
            assert row._original_value == "underline"
            assert row.current_value == "underline"

            # File has font-size=13, CLI default is "12"
            assert app._config_values["font-size"] == "13"


@pytest.mark.asyncio
async def test_select_mount_event_does_not_corrupt_state(tmp_config):
    """Select.Changed during mount should not make the row appear modified."""
    app = _make_app(tmp_config)

    with (
        patch("ghostcfg.app.list_themes", return_value=[]),
        patch("ghostcfg.app.get_config_with_docs", return_value=MOCK_CLI_DATA),
        patch("ghostcfg.app.reload_config", return_value=True),
    ):
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            row = app.query_one("#row-cursor-style", OptionRow)
            assert row._original_value == row.current_value
            assert not row.is_modified

            # No spurious changes should be detected
            assert app._collect_changes() == {}
