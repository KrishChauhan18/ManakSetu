import cv2
import numpy as np
from typing import Dict, Any, List

class RxSymbolDetector:
    """
    Detects presence of 'Rx' / 'NRx' / 'XRx' prescription symbols on medicine labels
    using OCR keyword spatial proximity and OpenCV shape/contour heuristics.
    """
    def detect_rx_symbol(self, image_np: np.ndarray, ocr_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 1. OCR text detection for Rx / NRx / XRx
        for b in ocr_blocks:
            text = b.get("text", "").strip()
            # Standalone Rx or starting with Rx
            if any(text.upper() == tag or text.upper().startswith(f"{tag} ") for tag in ["RX", "NRX", "XRX", "℞"]):
                return {
                    "present": True,
                    "symbol_type": text.upper().split()[0],
                    "confidence": min(0.95, b.get("confidence", 0.90)),
                    "bbox": b.get("bbox", [0, 0, 0, 0]),
                    "source": "ocr_text"
                }

        # 2. Template / Contour matching in top-left region of image
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_np.copy()

        h, w = gray.shape
        top_left = gray[0:int(h * 0.4), 0:int(w * 0.4)]
        
        # Check high contrast contours in top-left
        _, thresh = cv2.threshold(top_left, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            aspect_ratio = float(ch) / (cw + 1e-5)
            # Rx symbol typical aspect ratio 1.0 - 2.2 and minimum size
            if 20 <= cw <= 150 and 20 <= ch <= 200 and 0.8 <= aspect_ratio <= 2.5:
                # Potential symbol detected
                return {
                    "present": True,
                    "symbol_type": "Rx",
                    "confidence": 0.75,
                    "bbox": [x, y, x + cw, y + ch],
                    "source": "cv_contour"
                }

        return {
            "present": False,
            "symbol_type": None,
            "confidence": 0.0,
            "bbox": None,
            "source": "none"
        }

rx_detector = RxSymbolDetector()
