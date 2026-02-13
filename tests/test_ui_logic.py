"""Tests for UI logic and widget behavior."""

import pytest
from textual.widgets import Input, Label
from ghostcfg.widgets.option_row import OptionRow


@pytest.fixture
def option_row():
    """Create a sample OptionRow."""
    return OptionRow(
        key="font-size",
        meta={"type": "integer", "default": 12},
        current_value="12",
        doc="Font size in points",
        config_values={},
        id="row-font-size",
    )


def test_option_row_modified_state(option_row):
    """Test that is_modified updates correctly."""
    assert not option_row.is_modified
    assert option_row._original_value == "12"

    option_row.current_value = "14"
    assert option_row.is_modified

    option_row.update_original_value("14")
    assert not option_row.is_modified
    assert option_row._original_value == "14"

    option_row.current_value = "16"
    assert option_row.is_modified

    option_row.current_value = "14"
    assert not option_row.is_modified


def test_option_row_initialization(option_row):
    """Test OptionRow initialization values."""
    assert option_row.key == "font-size"
    assert option_row.current_value == "12"
    assert option_row._original_value == "12"
    assert not option_row.is_modified


# Note: Testing App interactions with filesystem requires more mocking,
# but testing OptionRow logic covers the core of the "persistent *" bug fix.
