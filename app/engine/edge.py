"""Edge detection for ASCII rendering using OpenCV."""
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class EdgeDetectionStep:
    """Detect edges using Sobel gradient magnitude + Canny refinement.
    
    Output is a grayscale image where pixel intensity = edge strength,
    suitable for character-density mapping to edge characters.
    """

    def __init__(self, blur_radius: int = 5, sobel_ksize: int = 3):
        self.blur_radius = blur_radius
        self.sobel_ksize = sobel_ksize

    def process(self, image: Image.Image) -> Image.Image:
        if not HAS_OPENCV:
            raise ImportError(
                "OpenCV is required for edge detection. "
                "Install with: pip install opencv-python"
            )
        
        # PIL → numpy (RGB or L)
        img_array = np.array(image)
        
        # Ensure grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Gaussian blur to reduce noise
        ksize = (self.blur_radius, self.blur_radius)
        blurred = cv2.GaussianBlur(gray, ksize, 0)
        
        # Sobel gradients
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=self.sobel_ksize)
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=self.sobel_ksize)
        
        # Gradient magnitude
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Normalize to 0-255
        if magnitude.max() > 0:
            magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
        else:
            magnitude = np.zeros_like(gray, dtype=np.uint8)
        
        return Image.fromarray(magnitude, mode="L")