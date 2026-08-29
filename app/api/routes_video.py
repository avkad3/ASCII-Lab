"""Video and webcam rendering endpoints for ASCII Lab."""

import io
import os
import tempfile
import time
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from ..engine.renderer import ASCIIRenderer
from ..media.video import VideoProcessor
from ..config import settings


router = APIRouter()

video_processor = VideoProcessor(
    max_duration=settings.MAX_VIDEO_DURATION_SECONDS
)


def create_renderer(
    width: int,
    mode: str,
    charset: str,
    brightness: float,
    contrast: float,
    gamma: float,
    invert: bool,
    dither: str,
    color: str,
) -> ASCIIRenderer:
    """Create a renderer using the requested frontend settings."""

    return ASCIIRenderer(
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


def save_upload_to_temp(file: UploadFile) -> tuple[str, bytes]:
    """Save an uploaded file to a temporary file."""

    filename = file.filename or "video.mp4"

    suffix = os.path.splitext(filename)[1].lower()

    if not suffix:
        suffix = ".mp4"

    contents = file.file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    return tmp_path, contents


def remove_temp_file(path: str) -> None:
    """Safely remove a temporary file."""

    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass


# ============================================================
# VIDEO PREVIEW
# ============================================================

@router.post("/render/video", tags=["video"])
async def render_video(
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

    target_fps: Optional[int] = Form(10),
):
    """
    Render the first frame of a video.

    Used by the frontend to:
    1. Upload a video.
    2. Get video metadata.
    3. Generate an ASCII preview.
    """

    start_time = time.time()
    tmp_path = None

    try:
        filename = file.filename or "video.mp4"

        tmp_path, contents = save_upload_to_temp(file)

        video_processor.validate(
            filename,
            len(contents),
        )

        info = video_processor.get_video_info(
            tmp_path
        )

        # Use requested FPS for extraction.
        processor = VideoProcessor(
            max_duration=settings.MAX_VIDEO_DURATION_SECONDS,
            target_fps=target_fps,
        )

        frame_generator = processor.extract_frames(
            tmp_path
        )

        try:
            first_frame, frame_num, timestamp = next(
                frame_generator
            )
        except StopIteration:
            raise ValueError(
                "Video contains no readable frames."
            )

        renderer = create_renderer(
            width=width,
            mode=mode,
            charset=charset,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma,
            invert=invert,
            dither=dither,
            color=color,
        )

        result = renderer.render(first_frame)

        processing_ms = int(
            (time.time() - start_time) * 1000
        )

        response = {
            "status": "ok",

            "preview": {
                "ascii": result.ascii_text,
                "width": result.width,
                "height": result.height,
                "mode": result.mode,
            },

            "video_info": info,

            "first_frame": {
                "frame": frame_num,
                "timestamp": round(timestamp, 3),
            },

            "processing_ms": processing_ms,

            "target_fps": target_fps,

            "message": (
                "Video preview generated successfully."
            ),
        }

        if result.color_data is not None:
            response["preview"]["color_data"] = (
                result.color_data.tolist()
            )

        return JSONResponse(
            content=response
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_VIDEO",
                "message": str(exc),
            },
        )

    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MISSING_DEPENDENCY",
                "message": str(exc),
            },
        )

    except Exception as exc:
        print("Video rendering error:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_ERROR",
                "message": str(exc),
            },
        )

    finally:
        await file.close()

        if tmp_path:
            remove_temp_file(tmp_path)


# ============================================================
# VIDEO FRAMES
# ============================================================

@router.post("/render/video/frames", tags=["video"])
async def render_video_frames(
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

    target_fps: Optional[int] = Form(10),
):
    """
    Render all video frames to ASCII.

    Returns an array of ASCII frames that the
    frontend can animate.
    """

    start_time = time.time()
    tmp_path = None

    try:
        filename = file.filename or "video.mp4"

        tmp_path, contents = save_upload_to_temp(file)

        video_processor.validate(
            filename,
            len(contents),
        )

        processor = VideoProcessor(
            max_duration=settings.MAX_VIDEO_DURATION_SECONDS,
            target_fps=target_fps,
        )

        renderer = create_renderer(
            width=width,
            mode=mode,
            charset=charset,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma,
            invert=invert,
            dither=dither,
            color=color,
        )

        frames = []

        for pil_image, frame_num, timestamp in processor.extract_frames(
            tmp_path
        ):
            result = renderer.render(
                pil_image
            )

            frame_data = {
                "frame": frame_num,
                "timestamp": round(timestamp, 3),
                "ascii": result.ascii_text,
                "width": result.width,
                "height": result.height,
                "mode": result.mode,
            }

            if result.color_data is not None:
                frame_data["color_data"] = (
                    result.color_data.tolist()
                )

            frames.append(frame_data)

        processing_ms = int(
            (time.time() - start_time) * 1000
        )

        return JSONResponse(
            content={
                "status": "ok",
                "frames": frames,
                "total_frames": len(frames),
                "processing_ms": processing_ms,
                "target_fps": target_fps,
            }
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_VIDEO",
                "message": str(exc),
            },
        )

    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MISSING_DEPENDENCY",
                "message": str(exc),
            },
        )

    except Exception as exc:
        print(
            "Video frame rendering error:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_ERROR",
                "message": str(exc),
            },
        )

    finally:
        await file.close()

        if tmp_path:
            remove_temp_file(tmp_path)


# ============================================================
# WEBCAM
# ============================================================

@router.post("/render/webcam", tags=["webcam"])
async def render_webcam_frame(
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
    """
    Process one webcam frame.

    The browser captures the webcam using getUserMedia(),
    converts the frame to an image, and sends it here.
    """

    try:
        contents = await file.read()

        if not contents:
            raise ValueError(
                "Empty webcam frame received."
            )

        image = Image.open(
            io.BytesIO(contents)
        )

        # Force decoding so invalid/truncated images
        # fail here rather than later.
        image.load()

        renderer = create_renderer(
            width=width,
            mode=mode,
            charset=charset,
            brightness=brightness,
            contrast=contrast,
            gamma=gamma,
            invert=invert,
            dither=dither,
            color=color,
        )

        result = renderer.render(
            image
        )

        response = {
            "status": "ok",
            "ascii": result.ascii_text,
            "width": result.width,
            "height": result.height,
            "mode": result.mode,
        }

        if result.color_data is not None:
            response["color_data"] = (
                result.color_data.tolist()
            )

        return JSONResponse(
            content=response
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_WEBCAM_FRAME",
                "message": str(exc),
            },
        )

    except Exception as exc:
        print(
            "Webcam rendering error:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_ERROR",
                "message": str(exc),
            },
        )

    finally:
        await file.close()
