"""Tests for character mapping module."""
import pytest
import numpy as np
from PIL import Image
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.engine.mapping import CharacterMappingStep, CHARSETS


class TestCharacterMapping:
    """Test suite for CharacterMappingStep."""

    def test_basic_mapping(self):
        """Test basic character mapping."""
        img = Image.new("L", (10, 10), color=128)
        step = CharacterMappingStep(charset="@%#*+=-:. ")
        rows, width, height = step.process(img)

        assert width == 10
        assert height == 10
        assert len(rows) == 10
        assert all(len(row) == 10 for row in rows)

    def test_black_pixel_maps_to_first_char(self):
        """Test that black (0) maps to first (darkest) character."""
        img = Image.new("L", (1, 1), color=0)
        step = CharacterMappingStep(charset="@# ")
        rows, _, _ = step.process(img)
        assert rows[0][0] == "@"

    def test_white_pixel_maps_to_last_char(self):
        """Test that white (255) maps to last (lightest) character."""
        img = Image.new("L", (1, 1), color=255)
        step = CharacterMappingStep(charset="@# ")
        rows, _, _ = step.process(img)
        assert rows[0][0] == " "

    def test_mid_gray_maps_to_middle(self):
        """Test that mid-gray maps to middle character."""
        img = Image.new("L", (1, 1), color=128)
        step = CharacterMappingStep(charset="@# ")
        rows, _, _ = step.process(img)
        assert rows[0][0] == "#"

    def test_custom_charset(self):
        """Test custom character set."""
        img = Image.new("L", (5, 5), color=128)
        step = CharacterMappingStep(charset="XO")
        rows, _, _ = step.process(img)
        assert all(c in "XO" for row in rows for c in row)

    def test_charset_deduplication(self):
        """Test that duplicate characters are removed."""
        step = CharacterMappingStep(charset="@@##**")
        assert step.charset == "@#*"

    def test_empty_charset_raises(self):
        """Test empty charset raises ValueError."""
        with pytest.raises(ValueError):
            CharacterMappingStep(charset="")

    def test_preset_charsets_exist(self):
        """Test that all expected presets exist."""
        expected = ["STANDARD", "DENSE", "MINIMAL", "BLOCKS", "BINARY", "TERMINAL", "EDGE"]
        for preset in expected:
            assert preset in CHARSETS
            assert len(CHARSETS[preset]) > 0

    def test_gradient_mapping(self):
        """Test that gradient produces varying characters."""
        img_array = np.zeros((10, 100), dtype=np.uint8)
        for x in range(100):
            img_array[:, x] = int(255 * (x / 100))
        img = Image.fromarray(img_array)

        step = CharacterMappingStep(charset="@%#*+=-:. ")
        rows, _, _ = step.process(img)

        # Should have multiple different characters
        unique_chars = set(c for row in rows for c in row)
        assert len(unique_chars) > 3, "Gradient should produce varied characters"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])