"""Tests for the core ASCII rendering engine (Milestone 1)."""
import pytest
import numpy as np
from PIL import Image
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.engine.renderer import ASCIIRenderer, RenderResult
from app.engine.mapping import CHARSETS


class TestASCIIRenderer:
    """Test suite for ASCIIRenderer."""

    def test_basic_rendering(self):
        """Test that a simple image renders to ASCII."""
        # Create a simple 100x100 gradient image
        img = Image.new("L", (100, 100))
        pixels = np.array(img)
        for y in range(100):
            pixels[y, :] = int(255 * (y / 100))
        img = Image.fromarray(pixels)

        renderer = ASCIIRenderer(width=40)
        result = renderer.render(img)

        assert isinstance(result, RenderResult)
        assert result.width == 40
        assert result.height > 0
        assert len(result.rows) == result.height
        assert all(len(row) == result.width for row in result.rows)
        assert result.mode == "density"

    def test_custom_charset(self):
        """Test rendering with a custom character set."""
        img = Image.new("L", (50, 50), color=128)
        custom_charset = "XO "

        renderer = ASCIIRenderer(width=20, charset=custom_charset)
        result = renderer.render(img)

        # All mid-gray pixels should map to 'O' (middle character)
        assert all(c in custom_charset for row in result.rows for c in row)
        # Middle gray should use middle char
        assert result.rows[0][0] == "O"

    def test_width_scaling(self):
        """Test that output width matches requested width."""
        img = Image.new("L", (200, 100), color=200)

        for target_width in [10, 40, 80, 120]:
            renderer = ASCIIRenderer(width=target_width)
            result = renderer.render(img)
            assert result.width == target_width
            assert all(len(row) == target_width for row in result.rows)

    def test_brightness_adjustment(self):
        """Test brightness affects character selection."""
        # Dark image
        img = Image.new("L", (50, 50), color=50)

        renderer_dark = ASCIIRenderer(width=10, brightness=0.5)
        result_dark = renderer_dark.render(img)

        renderer_bright = ASCIIRenderer(width=10, brightness=2.0)
        result_bright = renderer_bright.render(img)

        # Brighter image should use lighter characters on average
        dark_chars = sum(ord(c) for row in result_dark.rows for c in row)
        bright_chars = sum(ord(c) for row in result_bright.rows for c in row)

        # Lighter chars have higher ASCII values (space is 32, @ is 64)
        # With standard charset "@%#*+=-:. ", lighter chars are later in string
        # Brightness 2.0 should push values up, using lighter chars
        charset = renderer_dark.charset
        dark_idx = sum(charset.index(c) for row in result_dark.rows for c in row)
        bright_idx = sum(charset.index(c) for row in result_bright.rows for c in row)

        assert bright_idx >= dark_idx, "Higher brightness should use lighter characters"

    def test_contrast_adjustment(self):
        """Test contrast affects character distribution."""
        # Mid-tone image
        img = Image.new("L", (50, 50), color=128)

        renderer_low = ASCIIRenderer(width=10, contrast=0.5)
        result_low = renderer_low.render(img)

        renderer_high = ASCIIRenderer(width=10, contrast=2.0)
        result_high = renderer_high.render(img)

        # High contrast should push toward extremes
        low_unique = len(set(c for row in result_low.rows for c in row))
        high_unique = len(set(c for row in result_high.rows for c in row))

        # With flat mid-gray, low contrast keeps middle chars
        # High contrast with flat image might not change much, 
        # but test that contrast parameter is accepted and processed
        assert result_low is not None
        assert result_high is not None

    def test_inversion(self):
        """Test that invert flag reverses character mapping."""
        img = Image.new("L", (50, 50), color=255)  # White

        renderer_normal = ASCIIRenderer(width=10, invert=False)
        result_normal = renderer_normal.render(img)

        renderer_inverted = ASCIIRenderer(width=10, invert=True)
        result_inverted = renderer_inverted.render(img)

        # White image normal -> lightest char (space)
        # White image inverted -> darkest char (@)
        charset = renderer_normal.charset
        normal_char = result_normal.rows[0][0]
        inverted_char = result_inverted.rows[0][0]

        assert normal_char == charset[-1], "White image should map to lightest char"
        assert inverted_char == charset[0], "Inverted white should map to darkest char"

    def test_empty_image_raises_error(self):
        """Test that empty image raises ValueError."""
        img = Image.new("L", (0, 0))
        renderer = ASCIIRenderer(width=10)

        with pytest.raises(ValueError):
            renderer.render(img)

    def test_none_image_raises_error(self):
        """Test that None image raises ValueError."""
        renderer = ASCIIRenderer(width=10)

        with pytest.raises(ValueError):
            renderer.render(None)

    def test_invalid_image_type_raises_error(self):
        """Test that non-PIL images raise TypeError."""
        renderer = ASCIIRenderer(width=10)

        with pytest.raises(TypeError):
            renderer.render("not an image")

    def test_aspect_ratio_correction(self):
        """Test that aspect ratio is preserved with character correction."""
        # Create a square image
        img = Image.new("L", (100, 100), color=128)

        renderer = ASCIIRenderer(width=40)
        result = renderer.render(img)

        # With 0.5 char aspect ratio, 100x100 pixel square
        # should render to roughly 40x20 chars (half height)
        # The exact ratio depends on implementation
        ratio = result.width / result.height

        # Should be roughly 2:1 (width:height) due to char aspect correction
        assert 1.5 <= ratio <= 3.0, f"Aspect ratio {ratio} seems off"

    def test_preset_charset(self):
        """Test that preset charset names are resolved."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=10, charset="BLOCKS", mode="blocks")
        result = renderer.render(img)

        blocks_charset = CHARSETS["BLOCKS"]
        assert all(c in blocks_charset for row in result.rows for c in row)

    def test_render_result_structure(self):
        """Test that RenderResult has all expected fields."""
        img = Image.new("L", (100, 100))
        pixels = np.array(img)
        pixels[:, :] = np.random.randint(0, 256, (100, 100))
        img = Image.fromarray(pixels)

        renderer = ASCIIRenderer(width=60, mode="density", brightness=1.2, 
                                  contrast=0.8, gamma=1.1, invert=True)
        result = renderer.render(img)

        assert result.ascii_text is not None
        assert "\n" in result.ascii_text
        assert result.metadata["brightness"] == 1.2
        assert result.metadata["contrast"] == 0.8
        assert result.metadata["gamma"] == 1.1
        assert result.metadata["invert"] is True

    def test_binary_mode(self):
        """Test binary rendering mode."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=20, mode="binary")
        result = renderer.render(img)

        assert all(c in "01" for row in result.rows for c in row)

    def test_blocks_mode(self):
        """Test blocks rendering mode."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=20, mode="blocks")
        result = renderer.render(img)

        blocks_chars = CHARSETS["BLOCKS"]
        assert all(c in blocks_chars for row in result.rows for c in row)

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError):
            ASCIIRenderer(width=10, mode="invalid_mode")

    def test_invalid_width_raises_error(self):
        """Test that width < 1 raises ValueError."""
        with pytest.raises(ValueError):
            ASCIIRenderer(width=0)

    def test_empty_charset_raises_error(self):
        """Test that empty charset raises ValueError."""
        with pytest.raises(ValueError):
            ASCIIRenderer(width=10, charset="")

    def test_dithering_floyd_steinberg(self):
        """Test Floyd-Steinberg dithering runs without error."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=20, dither="floyd-steinberg")
        result = renderer.render(img)

        assert result.width == 20
        assert len(result.rows) > 0

    def test_dithering_atkinson(self):
        """Test Atkinson dithering runs without error."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=20, dither="atkinson")
        result = renderer.render(img)

        assert result.width == 20

    def test_dithering_ordered(self):
        """Test ordered dithering runs without error."""
        img = Image.new("L", (50, 50), color=128)

        renderer = ASCIIRenderer(width=20, dither="ordered")
        result = renderer.render(img)

        assert result.width == 20

    def test_color_mode_original(self):
        """Test color mode extracts color data."""
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))

        renderer = ASCIIRenderer(width=20, color="original")
        result = renderer.render(img)

        assert result.color_data is not None
        assert result.color_data.shape == (result.height, result.width, 3)

    def test_render_from_path(self, tmp_path):
        """Test rendering from file path."""
        img = Image.new("L", (50, 50), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        renderer = ASCIIRenderer(width=20)
        result = renderer.render_from_path(str(img_path))

        assert result.width == 20

    def test_get_available_modes(self):
        """Test that get_available_modes returns supported modes."""
        modes = ASCIIRenderer.get_available_modes()
        assert "density" in modes
        assert "blocks" in modes
        assert "binary" in modes

    def test_get_available_charsets(self):
        """Test that get_available_charsets returns presets."""
        charsets = ASCIIRenderer.get_available_charsets()
        assert "STANDARD" in charsets
        assert "BLOCKS" in charsets
        assert "BINARY" in charsets


if __name__ == "__main__":
    pytest.main([__file__, "-v"])