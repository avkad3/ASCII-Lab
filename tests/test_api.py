"""API integration tests for ASCII Lab."""
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app


client = TestClient(app)


class TestHealth:
    """Health check endpoint tests."""

    def test_health_check(self):
        """Test health endpoint returns ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRenderImage:
    """Image rendering endpoint tests."""

    def _create_image_bytes(self, mode="L", size=(100, 100), color=128):
        """Helper to create test image bytes."""
        img = Image.new(mode, size, color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    def test_render_image_basic(self):
        """Test basic image upload and rendering."""
        img_bytes = self._create_image_bytes()
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 40, "mode": "density"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ascii" in data
        assert data["width"] == 40
        assert data["mode"] == "density"
        assert "processing_ms" in data
        assert "metadata" in data

    def test_render_image_with_params(self):
        """Test rendering with all parameters."""
        img_bytes = self._create_image_bytes(mode="RGB", color=(255, 128, 64))
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={
                "width": 60,
                "mode": "blocks",
                "charset": "BLOCKS",
                "brightness": 1.2,
                "contrast": 0.8,
                "gamma": 1.1,
                "invert": True,
                "dither": "floyd-steinberg",
                "color": "monochrome",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["width"] == 60
        assert data["mode"] == "blocks"
        assert data["metadata"]["brightness"] == 1.2
        assert data["metadata"]["invert"] is True
        assert data["metadata"]["dither"] == "floyd-steinberg"

    def test_render_image_color_mode(self):
        """Test color mode returns color data."""
        img_bytes = self._create_image_bytes(mode="RGB", color=(255, 0, 0))
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 20, "color": "original"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "color_data" in data
        assert isinstance(data["color_data"], list)

    def test_invalid_file_type(self):
        """Test unsupported file type returns 415."""
        response = client.post(
            "/api/render/image",
            files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert response.status_code == 415
        assert "error" in response.json()["detail"]

    def test_missing_file(self):
        """Test missing file returns 422."""
        response = client.post("/api/render/image")
        assert response.status_code == 422

    def test_invalid_width(self):
        """Test invalid width returns 422."""
        img_bytes = self._create_image_bytes()
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 0}
        )
        assert response.status_code == 422
        assert "INVALID_WIDTH" in response.json()["detail"]["error"]

    def test_width_too_large(self):
        """Test width > 500 returns 422."""
        img_bytes = self._create_image_bytes()
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 1000}
        )
        assert response.status_code == 422

    def test_custom_charset(self):
        """Test custom character set."""
        img_bytes = self._create_image_bytes()
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 20, "charset": "XO "}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(c in "XO " for row in data["ascii"].split("\n") for c in row)

    def test_binary_mode(self):
        """Test binary mode returns only 0 and 1."""
        img_bytes = self._create_image_bytes()
        response = client.post(
            "/api/render/image",
            files={"file": ("test.png", img_bytes, "image/png")},
            data={"width": 20, "mode": "binary"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(c in "01" for row in data["ascii"].split("\n") for c in row)

    def test_dithering_modes(self):
        """Test all dithering modes work."""
        img_bytes = self._create_image_bytes()
        for dither in ["none", "floyd-steinberg", "atkinson", "ordered"]:
            img_bytes.seek(0)
            response = client.post(
                "/api/render/image",
                files={"file": ("test.png", img_bytes, "image/png")},
                data={"width": 20, "dither": dither}
            )
            assert response.status_code == 200, f"Dither {dither} failed"


class TestModesEndpoint:
    """Rendering modes endpoint tests."""

    def test_get_modes(self):
        """Test modes endpoint returns available modes."""
        response = client.get("/api/render/modes")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        mode_ids = [m["id"] for m in data["modes"]]
        assert "density" in mode_ids
        assert "blocks" in mode_ids
        assert "binary" in mode_ids


class TestCharsetsEndpoint:
    """Charsets endpoint tests."""

    def test_get_charsets(self):
        """Test charsets endpoint returns presets."""
        response = client.get("/api/charsets")
        assert response.status_code == 200
        data = response.json()
        assert "charsets" in data
        charset_ids = [c["id"] for c in data["charsets"]]
        assert "STANDARD" in charset_ids
        assert "BLOCKS" in charset_ids

if __name__ == "__main__":
    pytest.main([__file__, "-v"])