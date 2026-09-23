import cv2
import numpy as np
from typing import Tuple, Dict, Any

def preprocess_label_image(image_input: np.ndarray) -> np.ndarray:
    """
    Advanced OpenCV Preprocessing Pipeline for Tesseract OCR:
    1. Upscales to 300 DPI equivalent (width >= 1200px)
    2. Grayscale conversion
    3. CLAHE contrast enhancement (clipLimit=2.2, tileGridSize=(8,8))
    4. Bilateral filter noise reduction (d=7, sigmaColor=50, sigmaSpace=50)
    5. Otsu automatic thresholding
    """
    h, w = image_input.shape[:2]
    
    # 1. Scale width to >= 1200px for 300 DPI target resolution
    if w < 1200:
        scale_factor = 1200.0 / float(w)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        resized = cv2.resize(image_input, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    else:
        resized = image_input.copy()

    # 2. Grayscale
    if len(resized.shape) == 3 and resized.shape[2] == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized.copy()

    # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 4. Bilateral Filtering (preserves sharp text edges while removing sensor noise)
    filtered = cv2.bilateralFilter(enhanced, d=7, sigmaColor=50, sigmaSpace=50)

    # 5. Otsu Thresholding
    _, binary = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary

def preprocess_image(image_input: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Legacy helper wrapper returning (color_processed, ocr_binary)
    """
    binary = preprocess_label_image(image_input)
    return image_input, binary

def extract_cv_features(image_input: np.ndarray) -> Dict[str, Any]:
    """
    Extract classical Computer Vision features for Image Quality Classifier (Model 1):
    - laplacian_var (blur)
    - mean_brightness
    - std_brightness
    - glare_ratio
    - edge_density
    - symmetry_diff
    """
    if len(image_input.shape) == 3 and image_input.shape[2] == 3:
        gray = cv2.cvtColor(image_input, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_input.copy()

    # 1. Laplacian Variance (blur)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # 2. Mean & Std Brightness
    mean_brightness = float(np.mean(gray))
    std_brightness = float(np.std(gray))

    # 3. Glare Ratio (pixels > 240)
    glare_ratio = float(np.sum(gray > 240) / (gray.size + 1e-5))

    # 4. Edge Density & Symmetry Difference
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / (edges.size + 1e-5))

    half_h = gray.shape[0] // 2
    edges_top = edges[:half_h, :]
    edges_bottom = edges[half_h:, :]
    density_top = float(np.sum(edges_top > 0) / (edges_top.size + 1e-5))
    density_bottom = float(np.sum(edges_bottom > 0) / (edges_bottom.size + 1e-5))
    symmetry_diff = float(abs(density_top - density_bottom))

    return {
        "laplacian_var": laplacian_var,
        "mean_brightness": mean_brightness,
        "std_brightness": std_brightness,
        "glare_ratio": glare_ratio,
        "edge_density": edge_density,
        "symmetry_diff": symmetry_diff
    }
