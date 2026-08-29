"""Core ASCII rendering engine for ASCII Lab.

This module is completely independent of FastAPI or any web framework.
It can be imported and used standalone:

    from ascii_lab import ASCIIRenderer
    renderer = ASCIIRenderer(width=120, mode="density")
    result = renderer.render(image)
"""
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image
import numpy as np

from .pipeline import RenderPipeline
from .resize import ResizeStep
from .grayscale import GrayscaleStep
from .contrast import ContrastStep
from .dithering import DitheringStep
from .edge import EdgeDetectionStep
from .mapping import CharacterMappingStep, CHARSETS
from .color import ColorStep


@dataclass
class RenderResult:
    """Result of ASCII rendering operation."""
    ascii_text: str
    rows: List[str]
    width: int
    height: int
    mode: str
    charset: str
    color_data: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None


class ASCIIRenderer:
    """Standalone ASCII rendering engine.
    
    Parameters:
        width: Target width in characters.
        charset: Character set string (darkest to lightest) or preset name.
        mode: Rendering mode ('density', 'blocks', 'binary', 'edge', 'custom').
        brightness: Brightness multiplier (0.0+).
        contrast: Contrast multiplier (0.0+).
        gamma: Gamma correction value (0.01+).
        invert: Whether to invert the image.
        dither: Dithering algorithm ('none', 'floyd-steinberg', 'atkinson', 'ordered').
        color: Color mode ('monochrome', 'original', 'terminal').
    """

    SUPPORTED_MODES = ["density", "blocks", "binary", "edge", "custom"]

    def __init__(
        self,
        width: int = 80,
        charset: str = "@%#*+=-:. ",
        mode: str = "density",
        brightness: float = 1.0,
        contrast: float = 1.0,
        gamma: float = 1.0,
        invert: bool = False,
        dither: str = "none",
        color: str = "monochrome",
    ):
        if width < 1:
            raise ValueError("Width must be at least 1")
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"Unsupported mode: {mode}. Supported: {self.SUPPORTED_MODES}")
        if charset == "":
            raise ValueError("Character set cannot be empty")

        self.width = width
        self.mode = mode
        self.brightness = brightness
        self.contrast = contrast
        self.gamma = gamma
        self.invert = invert
        self.dither = dither
        self.color_mode = color

        # Resolve charset
        self.charset = self._resolve_charset(charset, mode)
        
        # Build pipeline
        self.pipeline = self._build_pipeline()

    def _resolve_charset(self, charset: str, mode: str) -> str:
        """Resolve charset from preset name or custom string."""
        if charset.upper() in CHARSETS:
            charset = CHARSETS[charset.upper()]
        
        # Mode-specific defaults only when user didn't specify a custom charset
        standard = CHARSETS["STANDARD"]
        if mode == "blocks" and charset == standard:
            return CHARSETS["BLOCKS"]
        if mode == "binary" and charset == standard:
            return CHARSETS["BINARY"]
        if mode == "edge" and charset == standard:
            return CHARSETS["EDGE"]
        
        return charset

    def _build_pipeline(self) -> RenderPipeline:
        """Construct the rendering pipeline based on current settings."""
        pipeline = RenderPipeline()
        
        # 1. Resize
        pipeline.add_step(ResizeStep(width=self.width))
        
        if self.mode == "edge":
            # Edge detection pipeline: skip grayscale/contrast/dither
            pipeline.add_step(EdgeDetectionStep())
            # Edge mode still respects invert
            if self.invert:
                pipeline.add_step(ContrastStep(invert=True))
        else:
            # 2. Grayscale (for density mapping)
            if self.mode in ("density", "blocks", "binary", "custom"):
                pipeline.add_step(GrayscaleStep())
            
            # 3. Contrast/brightness/gamma
            pipeline.add_step(ContrastStep(
                brightness=self.brightness,
                contrast=self.contrast,
                gamma=self.gamma,
                invert=self.invert,
            ))
            
            # 4. Dithering
            if self.dither != "none":
                pipeline.add_step(DitheringStep(algorithm=self.dither))
        
        # 5. Character mapping
        pipeline.add_step(CharacterMappingStep(
            charset=self.charset,
            mode=self.mode,
        ))
        
        return pipeline

    def render(self, image: Image.Image) -> RenderResult:
        """Render a PIL Image to ASCII.
        
        Args:
            image: PIL Image object.
            
        Returns:
            RenderResult containing ASCII text and metadata.
        """
        if image is None:
            raise ValueError("Image cannot be None")
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image, got {type(image).__name__}")
        if image.size == (0, 0):
            raise ValueError("Image has zero dimensions")

        # Store original for color extraction if needed
        original_image = image.copy()
        
        # Run pipeline
        # For color mode, we need to extract color before grayscale
        color_data = None
        if self.color_mode != "monochrome":
            # Resize color image to same dimensions
            resized_color = ResizeStep(width=self.width).process(original_image)
            color_data = ColorStep(mode=self.color_mode).process(resized_color)

        # Process through pipeline for ASCII
        result = self.pipeline.process(image)
        
        if isinstance(result, tuple) and len(result) == 3:
            rows, out_width, out_height = result
        else:
            raise RuntimeError("Pipeline did not return expected (rows, width, height) tuple")

        ascii_text = "\n".join(rows)

        return RenderResult(
            ascii_text=ascii_text,
            rows=rows,
            width=out_width,
            height=out_height,
            mode=self.mode,
            charset=self.charset,
            color_data=color_data,
            metadata={
                "brightness": self.brightness,
                "contrast": self.contrast,
                "gamma": self.gamma,
                "invert": self.invert,
                "dither": self.dither,
                "color_mode": self.color_mode,
            }
        )

    def render_from_path(self, path: str) -> RenderResult:
        """Convenience method to render from a file path."""
        image = Image.open(path)
        return self.render(image)

    @classmethod
    def get_available_modes(cls) -> List[str]:
        """Return list of supported rendering modes."""
        return cls.SUPPORTED_MODES.copy()

    @classmethod
    def get_available_charsets(cls) -> Dict[str, str]:
        """Return predefined character sets."""
        return CHARSETS.copy()