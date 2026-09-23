from typing import Dict, Any
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score, precision_score

def evaluate_classifier(model: Any, X_test: Any, y_test: Any) -> Dict[str, Any]:
    """
    Evaluates multi-class or binary classifier: returns accuracy, per-class P/R/F1, and confusion matrix.
    """
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n================ EVALUATION METRICS ================")
    print(f"Accuracy: {acc * 100.0:.2f}%")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(cm)
    print("====================================================\n")

    return {
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": cm
    }

def evaluate_ranking(model: Any, X_test: Any, y_test: Any, top_k: int = 10) -> Dict[str, Any]:
    """
    Evaluates ranking / risk prioritization model: returns ROC-AUC and Precision@k.
    """
    y_probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
    
    auc = roc_auc_score(y_test, y_probs)
    
    # Sort by predicted risk probability descending
    top_k_indices = np.argsort(y_probs)[::-1][:top_k]
    prec_at_k = np.mean(y_test.iloc[top_k_indices] if hasattr(y_test, 'iloc') else y_test[top_k_indices])

    print("\n================ RANKING METRICS ================")
    print(f"ROC-AUC Score: {auc:.4f}")
    print(f"Precision@{top_k}: {prec_at_k * 100.0:.2f}%")
    print("=================================================\n")

    return {
        "roc_auc": auc,
        "precision_at_k": float(prec_at_k)
    }
