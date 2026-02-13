"""Tests for config_io module."""

from ghostcfg.config_io import GhosttyConfig, parse_config


def test_parse_empty():
    config = parse_config("")
    assert config.entries == []


def test_parse_simple_option():
    config = parse_config("font-size = 14")
    assert len(config.entries) == 1
    assert config.entries[0].kind == "option"
    assert config.entries[0].key == "font-size"
    assert config.entries[0].value == "14"


def test_parse_preserves_comments():
    text = """# This is a comment
font-size = 14

# Another comment
theme = Catppuccin Mocha
"""
    config = parse_config(text)
    assert len(config.entries) == 5  # comment, option, blank, comment, option
    assert config.entries[0].kind == "comment"
    assert config.entries[1].kind == "option"
    assert config.entries[2].kind == "blank"
    assert config.entries[3].kind == "comment"
    assert config.entries[4].kind == "option"


def test_get_value():
    config = parse_config("font-size = 14\ntheme = Dracula")
    assert config.get("font-size") == "14"
    assert config.get("theme") == "Dracula"
    assert config.get("nonexistent") is None


def test_set_existing_value():
    config = parse_config("font-size = 14")
    config.set("font-size", "16")
    assert config.get("font-size") == "16"


def test_set_new_value():
    config = parse_config("font-size = 14")
    config.set("theme", "Dracula")
    assert config.get("theme") == "Dracula"
    assert len(config.entries) == 2


def test_remove_value():
    config = parse_config("font-size = 14\ntheme = Dracula")
    config.remove("theme")
    assert config.get("theme") is None
    assert len(config.entries) == 1


def test_roundtrip_preserves_structure():
    text = """# My Ghostty config
font-size = 14

# Theme
theme = Catppuccin Mocha
background-opacity = 0.95
"""
    config = parse_config(text)
    output = config.to_text()
    assert output == text


def test_modified_keys():
    original = parse_config("font-size = 14\ntheme = Dracula")
    modified = parse_config("font-size = 14\ntheme = Dracula")
    modified.set("theme", "Catppuccin Mocha")
    assert modified.modified_keys(original) == {"theme"}


def test_get_all_repeatable():
    config = parse_config("palette = 0=#000\npalette = 1=#111\nfont-size = 14")
    assert config.get_all("palette") == ["0=#000", "1=#111"]
    assert config.get_all("font-size") == ["14"]


def test_set_repeatable():
    config = parse_config("font-size = 14")
    config.set_repeatable("palette", ["0=#000", "1=#111"])
    assert config.get_all("palette") == ["0=#000", "1=#111"]
    text = config.to_text()
    assert "palette = 0=#000" in text
    assert "palette = 1=#111" in text
