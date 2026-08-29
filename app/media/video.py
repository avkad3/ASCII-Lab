"""Video frame extraction and processing for ASCII Lab."""

import os
from typing import Iterator, Tuple, Optional

from PIL import Image

try:
    import cv2

    HAS_OPENCV = True

except ImportError:
    HAS_OPENCV = False


class VideoProcessor:
    """Extract frames from video files using OpenCV."""

    SUPPORTED_FORMATS = {
        ".mp4",
        ".webm",
        ".mov",
        ".avi",
        ".mkv",
    }

    def __init__(
        self,
        max_duration: int = 60,
        target_fps: Optional[int] = None,
    ):
        self.max_duration = max_duration
        self.target_fps = target_fps

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        filename: str,
        file_size: int,
    ) -> None:
        """Validate video file."""

        if not filename:
            raise ValueError(
                "Video filename is missing."
            )

        ext = os.path.splitext(
            filename.lower()
        )[1]

        if ext not in self.SUPPORTED_FORMATS:
            supported = ", ".join(
                sorted(self.SUPPORTED_FORMATS)
            )

            raise ValueError(
                f"Unsupported video format: {ext}. "
                f"Supported: {supported}"
            )

        if file_size <= 0:
            raise ValueError(
                "Video file is empty."
            )

    # ========================================================
    # FRAME EXTRACTION
    # ========================================================

    def extract_frames(
        self,
        file_path: str,
    ) -> Iterator[
        Tuple[Image.Image, int, float]
    ]:
        """
        Extract frames from a video.

        Yields:
            PIL Image
            frame number
            timestamp in seconds
        """

        if not HAS_OPENCV:
            raise ImportError(
                "OpenCV is required for video processing. "
                "Install it with: pip install opencv-python"
            )

        cap = cv2.VideoCapture(
            file_path
        )

        if not cap.isOpened():
            cap.release()

            raise ValueError(
                "Could not open video file. "
                "The codec may not be supported."
            )

        try:
            fps = cap.get(
                cv2.CAP_PROP_FPS
            )

            if not fps or fps <= 0:
                fps = 30.0

            total_frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            duration = (
                total_frames / fps
                if fps > 0
                else 0
            )

            if (
                self.max_duration
                and duration > self.max_duration
            ):
                raise ValueError(
                    f"Video exceeds "
                    f"{self.max_duration}s limit "
                    f"({duration:.1f}s)"
                )

            # Determine how many source frames
            # should be skipped.
            frame_interval = 1

            if (
                self.target_fps
                and self.target_fps > 0
                and fps > self.target_fps
            ):
                frame_interval = max(
                    1,
                    int(
                        round(
                            fps
                            / self.target_fps
                        )
                    ),
                )

            frame_num = 0
            yielded = 0

            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                if (
                    frame_num
                    % frame_interval
                    == 0
                ):
                    frame_rgb = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB,
                    )

                    pil_image = Image.fromarray(
                        frame_rgb
                    )

                    timestamp = (
                        frame_num / fps
                    )

                    yield (
                        pil_image,
                        yielded,
                        timestamp,
                    )

                    yielded += 1

                frame_num += 1

        finally:
            cap.release()

    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    def get_video_info(
        self,
        file_path: str,
    ) -> dict:
        """Return video metadata."""

        if not HAS_OPENCV:
            raise ImportError(
                "OpenCV is required for video processing."
            )

        cap = cv2.VideoCapture(
            file_path
        )

        if not cap.isOpened():
            cap.release()

            raise ValueError(
                "Could not open video file."
            )

        try:
            fps = cap.get(
                cv2.CAP_PROP_FPS
            )

            if not fps or fps <= 0:
                fps = 30.0

            total_frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            width = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            height = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            duration = (
                total_frames / fps
                if fps > 0
                else 0
            )

            return {
                "fps": fps,
                "total_frames": total_frames,
                "width": width,
                "height": height,
                "duration": duration,
            }

        finally:
            cap.release()