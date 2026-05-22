"""
2D Convolution engine — manual implementation using NumPy.
Demonstrates: (f * g)(x,y) = ΣΣ f(m,n) g(x-m, y-n)
"""
import numpy as np
from scipy.ndimage import convolve


def make_gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    """G(x,y) = 1/(2πσ²) * e^(-(x²+y²)/(2σ²))"""
    half = size // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1]
    kernel = np.exp(-(x ** 2 + y ** 2) / (2 * sigma ** 2))
    return kernel / kernel.sum()


def make_average_kernel(size: int) -> np.ndarray:
    return np.ones((size, size), dtype=np.float32) / (size * size)


def make_sharpen_kernel() -> np.ndarray:
    return np.array([[0, -1, 0],
                     [-1, 5, -1],
                     [0, -1, 0]], dtype=np.float32)


def make_laplacian_kernel() -> np.ndarray:
    return np.array([[0,  1, 0],
                     [1, -4, 1],
                     [0,  1, 0]], dtype=np.float32)


def make_sobel_kernels():
    Kx = np.array([[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]], dtype=np.float32)
    Ky = np.array([[-1, -2, -1],
                   [0,  0,  0],
                   [1,  2,  1]], dtype=np.float32)
    return Kx, Ky


def apply_kernel_2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Apply a 2D kernel to each channel of an image via convolution."""
    if image.ndim == 2:
        result = convolve(image.astype(np.float32), kernel, mode='reflect')
        return np.clip(result, 0, 255).astype(np.uint8)
    channels = [convolve(image[:, :, c].astype(np.float32), kernel, mode='reflect')
                for c in range(image.shape[2])]
    return np.clip(np.stack(channels, axis=2), 0, 255).astype(np.uint8)
