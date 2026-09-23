import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any
from app.pipeline.preprocess import extract_cv_features

MODEL_PATH = os.path.join(os.getcwd(), "ml", "saved_models", "quality_model.joblib")

class QualityChecker:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception:
                self.model = None

    def assess_quality(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Assesses image quality using trained RandomForest model or CV heuristics.
        Returns:
        {
          "is_usable": bool,
          "issues": [list of issue strings],
          "scores": {cv features & predictions}
        }
        """
        feats = extract_cv_features(image_np)
        issues = []
        
        # Threshold heuristics for explicit feedback
        if feats["laplacian_var"] < 70.0:
            issues.append("Image is too blurry for reliable OCR extraction. Please retake with steady focus.")
            
        if feats["glare_ratio"] > 0.12 or feats["mean_brightness"] > 215.0:
            issues.append("High glare / over-exposure detected. Please avoid direct light reflection on the package.")
            
        if feats["mean_brightness"] < 40.0:
            issues.append("Image is too dark. Please use better lighting or camera flash.")

        if feats["symmetry_diff"] > 0.18:
            issues.append("Excessive angle skew detected. Please align camera parallel to the product label.")

        # ML Model prediction
        predicted_class = "good"
        if self.model is not None:
            try:
                df = pd.DataFrame([feats])
                pred = self.model.predict(df)[0]
                class_names = ["good", "blurry", "glare", "skewed"]
                predicted_class = class_names[pred] if pred < len(class_names) else "good"
            except Exception:
                pass

        is_usable = len(issues) == 0 and (predicted_class == "good")

        return {
            "is_usable": is_usable,
            "predicted_class": predicted_class,
            "issues": issues,
            "scores": {
                "laplacian_var": round(feats["laplacian_var"], 2),
                "mean_brightness": round(feats["mean_brightness"], 2),
                "glare_ratio": round(feats["glare_ratio"], 4),
                "symmetry_diff": round(feats["symmetry_diff"], 4)
            }
        }

quality_checker = QualityChecker()
