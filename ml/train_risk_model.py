import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score

SAVED_MODEL_DIR = os.path.join(os.getcwd(), "ml", "saved_models")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "risk_model.joblib")

def generate_synthetic_risk_data(num_samples: int = 500):
    """
    Generates synthetic risk features aggregated per manufacturer/region:
    Features:
    - hist_violation_rate (0.0 to 1.0)
    - critical_violations_last_5 (0 to 5)
    - avg_ocr_confidence (0.3 to 0.99)
    - days_since_last_inspection (1 to 180)
    Target:
    - next_scan_critical_violation (0 or 1)
    """
    np.random.seed(42)
    
    hist_rate = np.random.uniform(0.0, 0.8, num_samples)
    crit_count = np.random.randint(0, 6, num_samples)
    ocr_conf = np.random.uniform(0.4, 0.98, num_samples)
    days_since = np.random.randint(1, 180, num_samples)

    # Risk logit
    logit = 2.5 * hist_rate + 0.6 * crit_count - 1.8 * ocr_conf + 0.01 * days_since - 0.5
    prob = 1.0 / (1.0 + np.exp(-logit))
    target = (prob > 0.45).astype(int)

    df = pd.DataFrame({
        "hist_violation_rate": hist_rate,
        "critical_violations_last_5": crit_count,
        "avg_ocr_confidence": ocr_conf,
        "days_since_last_inspection": days_since
    })
    return df, target

def train_risk_model():
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
    X, y = generate_synthetic_risk_data(num_samples=600)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        eval_metric='logloss'
    )

    print("Training Model 3 XGBoost Priority Risk Scorer...")
    model.fit(X_train, y_train)

    y_probs = model.predict_proba(X_test)[:, 1]
    y_preds = (y_probs > 0.5).astype(int)

    auc = roc_auc_score(y_test, y_probs)
    prec = precision_score(y_test, y_preds)

    print(f"Model 3 Risk Scorer ROC-AUC: {auc:.4f}")
    print(f"Model 3 Precision@0.5: {prec:.4f}")

    joblib.dump(model, MODEL_PATH)
    print(f"Saved risk model to {MODEL_PATH}")
    return model

if __name__ == "__main__":
    train_risk_model()
