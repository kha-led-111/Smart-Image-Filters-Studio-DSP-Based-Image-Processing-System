"""
Histogram processing: equalization, analysis, and contrast enhancement.
"""
import numpy as np
import cv2


def compute_histogram(img: np.ndarray):
    """Return per-channel histograms as dict {b, g, r, bins}."""
    bins = np.arange(256)
    if img.ndim == 2:
        hist, _ = np.histogram(img.ravel(), bins=256, range=(0, 256))
        return {"gray": hist, "bins": bins}
    b_hist = cv2.calcHist([img], [0], None, [256], [0, 256]).ravel()
    g_hist = cv2.calcHist([img], [1], None, [256], [0, 256]).ravel()
    r_hist = cv2.calcHist([img], [2], None, [256], [0, 256]).ravel()
    return {"b": b_hist, "g": g_hist, "r": r_hist, "bins": bins}


def histogram_equalization(img: np.ndarray) -> np.ndarray:
    """
    s = T(r) = (L-1) * CDF(r) / N
    Applied per-channel for color images (CLAHE for better results).
    """
    if img.ndim == 2:
        return cv2.equalizeHist(img)
    # Convert to YCrCb and equalize Y channel only (preserves color)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def clahe_enhancement(img: np.ndarray, clip_limit: float = 2.0,
                       tile_size: int = 8) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalization."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit,
                             tileGridSize=(tile_size, tile_size))
    if img.ndim == 2:
        return clahe.apply(img)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = clahe.apply(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
