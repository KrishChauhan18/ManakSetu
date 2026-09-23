import re
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class CustomFieldFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Decoupled Feature Extractor for text block field classification.
    Extracts regex boolean flags and length metrics.
    Imported directly by training and API runtime scripts to ensure clean joblib serialization.
    """
    def fit(self, x, y=None):
        return self

    def transform(self, posts):
        features = []
        for text in posts:
            text_str = str(text)
            has_currency = 1.0 if re.search(r'(₹|rs\.?|inr|mrp|\$)', text_str, re.I) else 0.0
            has_digit = 1.0 if re.search(r'\d', text_str) else 0.0
            has_date = 1.0 if re.search(r'\d{1,2}[/\.-]\d{2,4}', text_str) else 0.0
            has_unit = 1.0 if re.search(r'\b(g|kg|ml|l|ltr|gm|gms|n|units|pcs)\b', text_str, re.I) else 0.0
            has_care = 1.0 if re.search(r'(care|customer|toll|complaint|email|tel|phone|contact|1800)', text_str, re.I) else 0.0
            has_mfr = 1.0 if re.search(r'(mfd|manufactured|packed|marketed|imported|pvt|ltd|co\.)', text_str, re.I) else 0.0
            length = float(len(text_str)) / 100.0

            features.append([
                has_currency, has_digit, has_date, has_unit, has_care, has_mfr, length
            ])
        return np.array(features)
