import os
import joblib
import pandas as pd
from typing import Dict, Any

MODEL_PATH = os.path.join(os.getcwd(), "ml", "saved_models", "risk_model.joblib")

class RiskScorer:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception:
                self.model = None

    def calculate_priority(self, hist_rate: float, crit_count: int, avg_conf: float, days_since: int) -> float:
        """
        Calculates priority risk score (0.0 to 1.0) for inspection prioritization.
        """
        if self.model is not None:
            try:
                df = pd.DataFrame([{
                    "hist_violation_rate": hist_rate,
                    "critical_violations_last_5": crit_count,
                    "avg_ocr_confidence": avg_conf,
                    "days_since_last_inspection": days_since
                }])
                prob = float(self.model.predict_proba(df)[0][1])
                return round(prob, 3)
            except Exception:
                pass

        # Heuristic fallback
        score = (hist_rate * 0.4) + (min(crit_count, 5) * 0.1) + ((1.0 - avg_conf) * 0.3) + (min(days_since, 180) / 180.0 * 0.2)
        return round(min(max(score, 0.0), 1.0), 3)

risk_scorer = RiskScorer()
