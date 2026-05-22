"""Image loading and saving utilities."""
import cv2
import numpy as np
from pathlib import Path


SUPPORTED_FORMATS = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp", "*.tiff")
SUPPORTED_FILTER = "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)"


def load_image(path: str) -> np.ndarray:
    """Load image as BGR NumPy array. Raises on failure."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img


def save_image(img: np.ndarray, path: str) -> bool:
    """Save BGR image to disk. Returns True on success."""
    return cv2.imwrite(str(path), img)


def resize_for_display(img: np.ndarray, max_w: int = 700, max_h: int = 550) -> np.ndarray:
    """Resize image proportionally to fit display constraints."""
    h, w = img.shape[:2]
    if w <= max_w and h <= max_h:
        return img
    scale = min(max_w / w, max_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def bgr_to_qimage(img: np.ndarray):
    """Convert BGR NumPy array to QImage for PyQt5 display."""
    from PyQt5.QtGui import QImage
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    return QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
