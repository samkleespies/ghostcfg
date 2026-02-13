"""Tests for schema module."""

from ghostcfg.schema import (
    CATEGORIES,
    SCHEMA,
    get_options_for_category,
    is_hot_reloadable,
    is_repeatable,
)


def test_categories_not_empty():
    assert len(CATEGORIES) > 0


def test_schema_not_empty():
    assert len(SCHEMA) > 0


def test_all_options_have_category():
    for name, meta in SCHEMA.items():
        assert "category" in meta, f"{name} missing category"
        assert meta["category"] in CATEGORIES, f"{name} has unknown category: {meta['category']}"


def test_all_options_have_type():
    valid_types = {"string", "boolean", "enum", "integer", "float", "color", "path", "duration"}
    for name, meta in SCHEMA.items():
        assert "type" in meta, f"{name} missing type"
        assert meta["type"] in valid_types, f"{name} has unknown type: {meta['type']}"


def test_enum_options_have_values():
    for name, meta in SCHEMA.items():
        if meta["type"] == "enum":
            assert "values" in meta, f"Enum {name} missing values"
            assert len(meta["values"]) > 0, f"Enum {name} has empty values"


def test_get_options_for_category():
    font_opts = get_options_for_category("Font")
    assert len(font_opts) > 0
    assert all(meta["category"] == "Font" for _, meta in font_opts)


def test_platform_filtering():
    macos_opts = get_options_for_category("Advanced", plat="macos")
    linux_opts = get_options_for_category("Advanced", plat="linux")
    # macOS options should not appear in Linux filter
    macos_names = {name for name, _ in macos_opts}
    linux_names = {name for name, _ in linux_opts}
    assert "macos-titlebar-style" in macos_names
    assert "macos-titlebar-style" not in linux_names
    assert "gtk-titlebar" in linux_names
    assert "gtk-titlebar" not in macos_names


def test_is_hot_reloadable():
    assert is_hot_reloadable("foreground") is True
    assert is_hot_reloadable("background") is True
    assert is_hot_reloadable("font-size") is False


def test_is_repeatable():
    assert is_repeatable("font-family") is True
    assert is_repeatable("palette") is True
    assert is_repeatable("font-size") is False
