"""
Filter registry: maps filter IDs to callables, metadata, and parameter specs.
"""
from processing import filters as F
from processing.histogram import histogram_equalization, clahe_enhancement

# Each entry: (callable, label, group, params)
# params: list of (name, min, max, default, step, label)

FILTER_REGISTRY = {
    # ── BASIC ──
    "none": {
        "fn": lambda img, **kw: img.copy(),
        "label": "Original",
        "group": "Basic",
        "params": [],
        "formula": "g(x,y) = f(x,y)",
        "desc": "Identity — no transformation.",
    },
    "grayscale": {
        "fn": lambda img, **kw: F.to_grayscale(img),
        "label": "Grayscale",
        "group": "Basic",
        "params": [],
        "formula": "Y = 0.299R + 0.587G + 0.114B",
        "desc": "Luminance-weighted color conversion.",
    },
    "brightness": {
        "fn": lambda img, value=30, **kw: F.adjust_brightness(img, int(value)),
        "label": "Brightness",
        "group": "Basic",
        "params": [("value", -100, 100, 30, 1, "Offset")],
        "formula": "g = f + k",
        "desc": "Additive intensity shift.",
    },
    "contrast": {
        "fn": lambda img, factor=1.5, **kw: F.adjust_contrast(img, factor),
        "label": "Contrast",
        "group": "Basic",
        "params": [("factor", 0.1, 3.0, 1.5, 0.05, "Factor α")],
        "formula": "g = α(f − 128) + 128",
        "desc": "Linear contrast scaling around mid-gray.",
    },
    "normalize": {
        "fn": lambda img, **kw: F.normalize_intensity(img),
        "label": "Normalize",
        "group": "Basic",
        "params": [],
        "formula": "g = (f − min) / (max − min) × 255",
        "desc": "Stretch intensity to full [0,255] range.",
    },

    # ── BLUR ──
    "average_blur": {
        "fn": lambda img, ksize=5, **kw: F.average_blur(img, int(ksize)),
        "label": "Average Blur",
        "group": "Blur",
        "params": [("ksize", 3, 21, 5, 2, "Kernel Size")],
        "formula": "g = (1/n²) Σ f(x+i, y+j)",
        "desc": "Box filter — uniform 2D convolution.",
    },
    "gaussian_blur": {
        "fn": lambda img, sigma=1.5, **kw: F.gaussian_blur(img, sigma=sigma),
        "label": "Gaussian Blur",
        "group": "Blur",
        "params": [("sigma", 0.3, 8.0, 1.5, 0.1, "σ (sigma)")],
        "formula": "G(x,y) = e^(−(x²+y²)/2σ²)",
        "desc": "Gaussian-weighted low-pass spatial filter.",
    },
    "median_blur": {
        "fn": lambda img, ksize=3, **kw: F.median_blur(img, int(ksize)),
        "label": "Median Filter",
        "group": "Blur",
        "params": [("ksize", 3, 11, 3, 2, "Kernel Size")],
        "formula": "g = median{f(x+i, y+j)}",
        "desc": "Nonlinear rank filter — excellent for salt & pepper.",
    },

    # ── SHARPEN ──
    "sharpen": {
        "fn": lambda img, **kw: F.sharpen(img),
        "label": "Sharpen",
        "group": "Sharpen",
        "params": [],
        "formula": "k = [0,-1,0 | -1,5,-1 | 0,-1,0]",
        "desc": "Laplacian-based sharpening kernel.",
    },
    "highpass_sharpen": {
        "fn": lambda img, strength=1.5, **kw: F.high_pass_sharpen(img, strength),
        "label": "Unsharp Masking",
        "group": "Sharpen",
        "params": [("strength", 0.5, 4.0, 1.5, 0.1, "Strength α")],
        "formula": "g = f + α(f − blur(f))",
        "desc": "High-frequency detail boosting via residual.",
    },

    # ── EDGE DETECTION ──
    "sobel": {
        "fn": lambda img, **kw: F.sobel_edge(img),
        "label": "Sobel Edge",
        "group": "Edge",
        "params": [],
        "formula": "M = √(Gx² + Gy²)",
        "desc": "Gradient magnitude via Sobel X/Y operators.",
    },
    "canny": {
        "fn": lambda img, low=50, high=150, **kw: F.canny_edge(img, int(low), int(high)),
        "label": "Canny Edge",
        "group": "Edge",
        "params": [("low", 10, 200, 50, 5, "Low Threshold"),
                   ("high", 50, 400, 150, 5, "High Threshold")],
        "formula": "Gradient → NMS → Hysteresis",
        "desc": "Multi-stage optimal edge detector.",
    },
    "laplacian": {
        "fn": lambda img, **kw: F.laplacian_edge(img),
        "label": "Laplacian",
        "group": "Edge",
        "params": [],
        "formula": "∇²f = ∂²f/∂x² + ∂²f/∂y²",
        "desc": "Second-derivative isotropic edge detector.",
    },

    # ── NOISE ──
    "salt_pepper": {
        "fn": lambda img, amount=0.05, **kw: F.add_salt_pepper_noise(img, amount),
        "label": "Add Salt & Pepper",
        "group": "Noise",
        "params": [("amount", 0.01, 0.3, 0.05, 0.01, "Noise Amount")],
        "formula": "P(0) = P(255) = a/2",
        "desc": "Random impulse noise injection.",
    },
    "denoise": {
        "fn": lambda img, sigma=1.2, **kw: F.gaussian_noise_reduction(img, sigma),
        "label": "Gaussian Denoise",
        "group": "Noise",
        "params": [("sigma", 0.3, 5.0, 1.2, 0.1, "σ (sigma)")],
        "formula": "g = G_σ * f",
        "desc": "Gaussian smoothing for noise suppression.",
    },

    # ── HISTOGRAM ──
    "hist_eq": {
        "fn": lambda img, **kw: histogram_equalization(img),
        "label": "Histogram EQ",
        "group": "Histogram",
        "params": [],
        "formula": "s = (L−1) · CDF(r) / N",
        "desc": "Global contrast enhancement via CDF mapping.",
    },
    "clahe": {
        "fn": lambda img, clip=2.0, tile=8, **kw: clahe_enhancement(img, clip, int(tile)),
        "label": "CLAHE",
        "group": "Histogram",
        "params": [("clip", 1.0, 8.0, 2.0, 0.5, "Clip Limit"),
                   ("tile", 4, 16, 8, 2, "Tile Size")],
        "formula": "Local CDF with clip limit C",
        "desc": "Adaptive histogram equalization — no over-amplification.",
    },

    # ── FREQUENCY ──
    "fft_spectrum": {
        "fn": lambda img, **kw: F.compute_fft_spectrum(img),
        "label": "FFT Spectrum",
        "group": "Frequency",
        "params": [],
        "formula": "F(u,v) = ΣΣ f(x,y)·e^{-j2π(ux/M+vy/N)}",
        "desc": "Log-magnitude 2D Fourier spectrum (shifted).",
    },
    "lowpass": {
        "fn": lambda img, cutoff=0.3, **kw: F.low_pass_filter(img, cutoff),
        "label": "Low-Pass Filter",
        "group": "Frequency",
        "params": [("cutoff", 0.05, 0.9, 0.3, 0.05, "Cutoff D₀")],
        "formula": "H(u,v) = 1 if D(u,v) ≤ D₀",
        "desc": "Ideal circular LPF — removes high-freq detail.",
    },
    "highpass_freq": {
        "fn": lambda img, cutoff=0.1, **kw: F.high_pass_filter(img, cutoff),
        "label": "High-Pass Filter",
        "group": "Frequency",
        "params": [("cutoff", 0.02, 0.5, 0.1, 0.02, "Cutoff D₀")],
        "formula": "H(u,v) = 1 if D(u,v) > D₀",
        "desc": "Ideal circular HPF — retains edges/textures.",
    },
    "bandpass": {
        "fn": lambda img, low=0.1, high=0.4, **kw: F.band_pass_filter(img, low, high),
        "label": "Band-Pass Filter",
        "group": "Frequency",
        "params": [("low", 0.02, 0.5, 0.1, 0.02, "Inner D₁"),
                   ("high", 0.1, 0.9, 0.4, 0.05, "Outer D₂")],
        "formula": "H(u,v) = 1 if D₁ < D < D₂",
        "desc": "Passes a ring of frequencies in the spectrum.",
    },
}

GROUPS = ["Basic", "Blur", "Sharpen", "Edge", "Noise", "Histogram", "Frequency"]
