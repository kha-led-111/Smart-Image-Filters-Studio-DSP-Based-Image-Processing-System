# Smart Image Filters Studio
### DSP-Based Image Processing & Enhancement System

A desktop image processing application demonstrating Digital Signal Processing
concepts including 2D convolution, Fourier analysis, edge detection, histogram
processing, and spatial/frequency domain filtering.

---

## Setup

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

---

## Project Structure

```
sfilt_studio/
│
├── main.py                     # Entry point
│
├── gui/
│   ├── dashboard.py            # Main window, drop zone, right info panel
│   ├── controls.py             # Filter sidebar with group tabs & sliders
│   └── viewer.py               # Image viewer + histogram canvas
│
├── processing/
│   ├── convolution.py          # Manual 2D convolution, kernel generators
│   ├── filters.py              # All spatial + frequency domain filters
│   ├── histogram.py            # Histogram equalization, CLAHE
│   └── filter_registry.py      # Filter ID → function + metadata map
│
├── utils/
│   └── image_loader.py         # Load/save, resize, BGR↔QImage conversion
│
├── outputs/                    # Exported images saved here
├── requirements.txt
└── README.md
```

---

## Features

### Filters (20 total)

| Group      | Filter                  | DSP Concept                    |
|------------|-------------------------|--------------------------------|
| Basic      | Grayscale               | Luminance conversion           |
| Basic      | Brightness / Contrast   | Intensity scaling              |
| Basic      | Normalize               | Range stretching               |
| Blur       | Average Blur            | Box filter convolution         |
| Blur       | Gaussian Blur           | Gaussian kernel convolution    |
| Blur       | Median Filter           | Nonlinear rank filtering       |
| Sharpen    | Sharpen                 | Laplacian-based kernel         |
| Sharpen    | Unsharp Masking         | High-pass residual boost       |
| Edge       | Sobel Edge              | Gradient magnitude             |
| Edge       | Canny Edge              | Multi-stage optimal detector   |
| Edge       | Laplacian               | 2nd derivative edge map        |
| Noise      | Salt & Pepper           | Impulse noise injection        |
| Noise      | Gaussian Denoise        | Low-pass smoothing             |
| Histogram  | Histogram EQ            | CDF-based contrast stretch     |
| Histogram  | CLAHE                   | Adaptive local equalization    |
| Frequency  | FFT Spectrum            | 2D Fourier magnitude           |
| Frequency  | Low-Pass Filter         | Ideal circular LPF in freq dom |
| Frequency  | High-Pass Filter        | Ideal circular HPF in freq dom |
| Frequency  | Band-Pass Filter        | Annular mask in freq domain    |

### UI Features
- Drag & drop image loading (JPG, PNG, BMP, WebP, TIFF)
- Live parameter sliders with debounced real-time preview
- Before/After comparison mode (side-by-side)
- RGB histogram panel (rendered in Qt, no Matplotlib popup)
- DSP formula display for every active filter
- Multi-threaded processing (QThread — UI never freezes)
- Export processed image (PNG, JPG, BMP)

---

## DSP Concepts Demonstrated

- **2D Convolution**: `(f * g)(x,y) = ΣΣ f(m,n) g(x-m, y-n)`
- **Fourier Transform**: `F(u,v) = ΣΣ f(x,y)·e^{-j2π(ux/M + vy/N)}`
- **Gaussian Kernel**: `G(x,y) = (1/2πσ²)·e^{-(x²+y²)/2σ²}`
- **Histogram Equalization**: `s = T(r) = (L-1)·CDF(r)/N`
- **Sobel Gradient**: `M = √(Gx² + Gy²)`
- **Unsharp Masking**: `g = f + α(f - blur(f))`
- **Laplacian**: `∇²f = ∂²f/∂x² + ∂²f/∂y²`

---

## Requirements

- Python 3.9+
- PyQt5 ≥ 5.15
- OpenCV ≥ 4.8
- NumPy ≥ 1.24
- SciPy ≥ 1.10
