"""Image rendering endpoints."""
import io
import time
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from ..engine.renderer import ASCIIRenderer
from ..config import settings

router = APIRouter()


SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file."""
    if file.size and file.size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail={"error": "FILE_TOO_LARGE", "message": f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"}
        )
    
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_IMAGE_TYPES:
        filename = file.filename or ""
        if not any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            raise HTTPException(
                status_code=415,
                detail={"error": "UNSUPPORTED_MEDIA_TYPE", "message": "Only JPG, PNG, WebP images are supported"}
            )


@router.post("/render/image", tags=["render"])
async def render_image(
    file: UploadFile = File(...),
    width: int = Form(80),
    mode: str = Form("density"),
    charset: str = Form("STANDARD"),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
    gamma: float = Form(1.0),
    invert: bool = Form(False),
    dither: str = Form("none"),
    color: str = Form("monochrome"),
):
    """Render an uploaded image to ASCII art."""
    start_time = time.time()
    
    validate_image(file)
    
    if width < 1 or width > 500:
        raise HTTPException(
            status_code=422,
            detail={"error": "INVALID_WIDTH", "message": "Width must be between 1 and 500"}
        )
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        img_width, img_height = image.size
        if img_width > settings.MAX_IMAGE_WIDTH or img_height > settings.MAX_IMAGE_WIDTH:
            raise HTTPException(
                status_code=422,
                detail={"error": "IMAGE_TOO_LARGE", "message": f"Image dimensions exceed {settings.MAX_IMAGE_WIDTH}px"}
            )
        
        renderer = ASCIIRenderer(
            width=width,
            charset=charset,
            mode=mode,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma,
            invert=invert,
            dither=dither,
            color=color,
        )
        
        result = renderer.render(image)
        processing_ms = int((time.time() - start_time) * 1000)
        
        response = {
            "ascii": result.ascii_text,
            "width": result.width,
            "height": result.height,
            "mode": result.mode,
            "charset": result.charset,
            "processing_ms": processing_ms,
            "metadata": result.metadata,
        }
        
        if result.color_data is not None:
            response["color_data"] = result.color_data.tolist()
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "INVALID_PARAMETER", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "PROCESSING_ERROR", "message": str(e)}
        )
    finally:
        await file.close()


@router.get("/render/modes", tags=["render"])
async def get_modes():
    """Get available rendering modes."""
    return {
        "modes": [
            {"id": "density", "name": "Density", "description": "Character density represents brightness"},
            {"id": "blocks", "name": "Blocks", "description": "Unicode block characters"},
            {"id": "binary", "name": "Binary", "description": "Two-character binary representation"},
            {"id": "edge", "name": "Edge", "description": "Edge detection mapping"},
            {"id": "custom", "name": "Custom", "description": "User-defined character set"},
        ]
    }


@router.get("/charsets", tags=["render"])
async def get_charsets():
    """Get predefined character sets."""
    charsets = ASCIIRenderer.get_available_charsets()
    return {
        "charsets": [
            {"id": k, "name": k.title(), "chars": v}
            for k, v in charsets.items()
        ]
    }