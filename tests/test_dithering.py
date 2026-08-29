"""Tests for dithering module."""
import pytest
import numpy as np
from PIL import Image
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.engine.dithering import DitheringStep


class TestDithering:
    """Test suite for DitheringStep."""

    def test_none_dithering(self):
        """Test that 'none' returns image unchanged."""
        img = Image.new("L", (10, 10), color=128)
        step = DitheringStep(algorithm="none")
        result = step.process(img)
        assert np.array_equal(np.array(img), np.array(result))

    def test_floyd_steinberg_runs(self):
        """Test Floyd-Steinberg dithering executes."""
        img = Image.new("L", (20, 20), color=128)
        step = DitheringStep(algorithm="floyd-steinberg")
        result = step.process(img)
        assert result.size == (20, 20)

    def test_atkinson_runs(self):
        """Test Atkinson dithering executes."""
        img = Image.new("L", (20, 20), color=128)
        step = DitheringStep(algorithm="atkinson")
        result = step.process(img)
        assert result.size == (20, 20)

    def test_ordered_runs(self):
        """Test ordered dithering executes."""
        img = Image.new("L", (20, 20), color=128)
        step = DitheringStep(algorithm="ordered")
        result = step.process(img)
        assert result.size == (20, 20)

    def test_dithering_adds_variation(self):
        """Test that dithering adds variation to flat image."""
        img = Image.new("L", (50, 50), color=128)

        step = DitheringStep(algorithm="floyd-steinberg")
        result = step.process(img)

        result_array = np.array(result)
        unique_values = len(np.unique(result_array))
        assert unique_values > 1, "Dithering should create variation"

    def test_invalid_algorithm_raises(self):
        """Test invalid algorithm raises ValueError."""
        with pytest.raises(ValueError):
            DitheringStep(algorithm="invalid")

    def test_grayscale_output(self):
        """Test output is grayscale."""
        img = Image.new("L", (10, 10), color=128)
        step = DitheringStep(algorithm="floyd-steinberg")
        result = step.process(img)
        assert result.mode == "L"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])