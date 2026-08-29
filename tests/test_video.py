"""Tests for video processing module."""
import pytest
import numpy as np
from PIL import Image

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.media.video import VideoProcessor


class TestVideoProcessor:
    """Test suite for VideoProcessor."""

    def test_validate_supported_format(self):
        """Test that supported formats pass validation."""
        vp = VideoProcessor()
        for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']:
            vp.validate(f"test{ext}", 1024)

    def test_validate_unsupported_format(self):
        """Test that unsupported formats raise error."""
        vp = VideoProcessor()
        with pytest.raises(ValueError):
            vp.validate("test.gif", 1024)

    def test_validate_size(self):
        """Test validation accepts any size for now."""
        vp = VideoProcessor()
        vp.validate("test.mp4", 100 * 1024 * 1024)

    def test_max_duration(self):
        """Test max duration setting."""
        vp = VideoProcessor(max_duration=30)
        assert vp.max_duration == 30