"""
Spatial domain and frequency domain image filters.
All filters operate on NumPy arrays (H x W x 3 BGR or H x W grayscale).
"""
import numpy as np
import cv2
from scipy.ndimage import median_filter as scipy_median

from processing.convolution import (
    make_gaussian_kernel, make_average_kernel, make_sharpen_kernel,
    make_laplacian_kernel, make_sobel_kernels, apply_kernel_2d
)


# ─── PREPROCESSING ────────────────────────────────────────────────────────────

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Y = 0.299R + 0.587G + 0.114B  (convert to 3-ch gray for display)"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def adjust_brightness(img: np.ndarray, value: int) -> np.ndarray:
    """f(x,y) + k"""
    arr = img.astype(np.int16) + value
    return np.clip(arr, 0, 255).astype(np.uint8)


def adjust_contrast(img: np.ndarray, factor: float) -> np.ndarray:
    """α(f(x,y) − 128) + 128"""
    arr = factor * (img.astype(np.float32) - 128) + 128
    return np.clip(arr, 0, 255).astype(np.uint8)


def normalize_intensity(img: np.ndarray) -> np.ndarray:
    """Stretch intensity to [0, 255]"""
    mn, mx = img.min(), img.max()
    if mx == mn:
        return img
    return ((img.astype(np.float32) - mn) / (mx - mn) * 255).astype(np.uint8)


def resize_image(img: np.ndarray, scale: float) -> np.ndarray:
    h, w = img.shape[:2]
    return cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))),
                      interpolation=cv2.INTER_LINEAR)


# ─── BLUR FILTERS ─────────────────────────────────────────────────────────────

def average_blur(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Box filter — uniform kernel convolution"""
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    kernel = make_average_kernel(ksize)
    return apply_kernel_2d(img, kernel)


def gaussian_blur(img: np.ndarray, ksize: int = 7, sigma: float = 1.5) -> np.ndarray:
    """G(x,y) = 1/(2πσ²) e^(-(x²+y²)/2σ²)"""
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    kernel = make_gaussian_kernel(ksize, sigma)
    return apply_kernel_2d(img, kernel)


def median_blur(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """Nonlinear: replace pixel with median of neighbourhood"""
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    if img.ndim == 3:
        channels = [scipy_median(img[:, :, c], size=ksize) for c in range(img.shape[2])]
        return np.clip(np.stack(channels, axis=2), 0, 255).astype(np.uint8)
    return np.clip(scipy_median(img, size=ksize), 0, 255).astype(np.uint8)


# ─── SHARPENING ───────────────────────────────────────────────────────────────

def sharpen(img: np.ndarray) -> np.ndarray:
    """Laplacian-based: [0,-1,0 | -1,5,-1 | 0,-1,0]"""
    return apply_kernel_2d(img, make_sharpen_kernel())


def high_pass_sharpen(img: np.ndarray, strength: float = 1.5) -> np.ndarray:
    """Unsharp masking: g = f + α(f − blur(f))"""
    blurred = gaussian_blur(img, ksize=9, sigma=2.0)
    detail = img.astype(np.float32) - blurred.astype(np.float32)
    result = img.astype(np.float32) + strength * detail
    return np.clip(result, 0, 255).astype(np.uint8)


# ─── EDGE DETECTION ──────────────────────────────────────────────────────────

def sobel_edge(img: np.ndarray) -> np.ndarray:
    """M = sqrt(Gx² + Gy²) using Sobel operators"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    Kx, Ky = make_sobel_kernels()
    from scipy.ndimage import convolve
    gx = convolve(gray, Kx, mode='reflect')
    gy = convolve(gray, Ky, mode='reflect')
    mag = np.sqrt(gx ** 2 + gy ** 2)
    mag = np.clip(mag, 0, 255).astype(np.uint8)
    return cv2.cvtColor(mag, cv2.COLOR_GRAY2BGR)


def canny_edge(img: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
    """Canny multi-stage edge detector"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, low, high)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def laplacian_edge(img: np.ndarray) -> np.ndarray:
    """∇²f = ∂²f/∂x² + ∂²f/∂y²"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    from scipy.ndimage import convolve
    lap = convolve(gray, make_laplacian_kernel(), mode='reflect')
    lap = np.abs(lap)
    lap = np.clip(lap / lap.max() * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lap, cv2.COLOR_GRAY2BGR)


# ─── NOISE ────────────────────────────────────────────────────────────────────

def add_salt_pepper_noise(img: np.ndarray, amount: float = 0.05) -> np.ndarray:
    """P(0) = P(255) = amount/2"""
    out = img.copy()
    total = img.size // img.shape[2] if img.ndim == 3 else img.size
    n_salt = int(total * amount / 2)
    n_pepper = int(total * amount / 2)
    h, w = img.shape[:2]
    coords = np.random.randint(0, h, n_salt), np.random.randint(0, w, n_salt)
    out[coords[0], coords[1]] = 255
    coords = np.random.randint(0, h, n_pepper), np.random.randint(0, w, n_pepper)
    out[coords[0], coords[1]] = 0
    return out


def gaussian_noise_reduction(img: np.ndarray, sigma: float = 1.2) -> np.ndarray:
    """Gaussian smoothing to reduce noise"""
    return gaussian_blur(img, ksize=5, sigma=sigma)


# ─── FREQUENCY DOMAIN ────────────────────────────────────────────────────────

def _freq_filter(img: np.ndarray, mask_fn) -> np.ndarray:
    """Apply a frequency-domain mask via 2D FFT → filter → IFFT"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    rows, cols = gray.shape
    crow, ccol = rows // 2, cols // 2
    mask = mask_fn(rows, cols, crow, ccol)
    filtered = fshift * mask
    f_ishift = np.fft.ifftshift(filtered)
    img_back = np.fft.ifft2(f_ishift)
    img_back = np.abs(img_back)
    img_back = np.clip(img_back, 0, 255).astype(np.uint8)
    return cv2.cvtColor(img_back, cv2.COLOR_GRAY2BGR)


def low_pass_filter(img: np.ndarray, cutoff: float = 0.3) -> np.ndarray:
    """H(u,v) = 1 if D(u,v) ≤ D₀"""
    def mask_fn(rows, cols, crow, ccol):
        radius = int(min(rows, cols) * cutoff / 2)
        mask = np.zeros((rows, cols), np.float32)
        Y, X = np.ogrid[:rows, :cols]
        dist = np.sqrt((X - ccol) ** 2 + (Y - crow) ** 2)
        mask[dist <= radius] = 1
        return mask
    return _freq_filter(img, mask_fn)


def high_pass_filter(img: np.ndarray, cutoff: float = 0.1) -> np.ndarray:
    """H(u,v) = 1 if D(u,v) > D₀"""
    def mask_fn(rows, cols, crow, ccol):
        radius = int(min(rows, cols) * cutoff / 2)
        mask = np.ones((rows, cols), np.float32)
        Y, X = np.ogrid[:rows, :cols]
        dist = np.sqrt((X - ccol) ** 2 + (Y - crow) ** 2)
        mask[dist <= radius] = 0
        return mask
    result = _freq_filter(img, mask_fn)
    # Normalize for visibility
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY).astype(np.float32)
    if gray.max() > 0:
        gray = gray / gray.max() * 255
    return cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR)


def band_pass_filter(img: np.ndarray, low: float = 0.1, high: float = 0.4) -> np.ndarray:
    """H(u,v) = 1 if D₁ < D(u,v) < D₂"""
    def mask_fn(rows, cols, crow, ccol):
        r_lo = int(min(rows, cols) * low / 2)
        r_hi = int(min(rows, cols) * high / 2)
        mask = np.zeros((rows, cols), np.float32)
        Y, X = np.ogrid[:rows, :cols]
        dist = np.sqrt((X - ccol) ** 2 + (Y - crow) ** 2)
        mask[(dist >= r_lo) & (dist <= r_hi)] = 1
        return mask
    return _freq_filter(img, mask_fn)


def compute_fft_spectrum(img: np.ndarray) -> np.ndarray:
    """
    F(u,v) = ΣΣ f(x,y)·e^(-j2π(ux/M + vy/N))
    Returns a displayable log-magnitude spectrum image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)
    magnitude = np.clip(magnitude / magnitude.max() * 255, 0, 255).astype(np.uint8)
    spectrum_color = cv2.applyColorMap(magnitude, cv2.COLORMAP_INFERNO)
    return spectrum_color
