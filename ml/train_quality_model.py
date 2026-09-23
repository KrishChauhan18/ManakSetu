import os
import cv2
import glob
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from app.pipeline.preprocess import extract_cv_features

SAVED_MODEL_DIR = os.path.join(os.getcwd(), "ml", "saved_models")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "quality_model.joblib")

def generate_synthetic_quality_data(num_samples: int = 400):
    """
    Generates realistic CV feature distributions for 4 quality classes:
    0: good, 1: blurry, 2: glare, 3: skewed
    """
    np.random.seed(42)
    n = num_samples // 4
    
    # Good: High laplacian var (>150), normal brightness (100-180), low glare (<0.05), balanced symmetry
    good_lap = np.random.uniform(150, 500, n)
    good_bright = np.random.uniform(100, 180, n)
    good_std = np.random.uniform(40, 70, n)
    good_glare = np.random.uniform(0.0, 0.04, n)
    good_edge = np.random.uniform(0.05, 0.15, n)
    good_sym = np.random.uniform(0.0, 0.05, n)
    
    # Blurry: Low laplacian var (<60), normal brightness
    blur_lap = np.random.uniform(5, 55, n)
    blur_bright = np.random.uniform(80, 180, n)
    blur_std = np.random.uniform(15, 35, n)
    blur_glare = np.random.uniform(0.0, 0.04, n)
    blur_edge = np.random.uniform(0.01, 0.04, n)
    blur_sym = np.random.uniform(0.0, 0.05, n)

    # Glare: High brightness (>200), high glare ratio (>0.15)
    glare_lap = np.random.uniform(100, 400, n)
    glare_bright = np.random.uniform(200, 250, n)
    glare_std = np.random.uniform(10, 40, n)
    glare_glare = np.random.uniform(0.15, 0.50, n)
    glare_edge = np.random.uniform(0.02, 0.08, n)
    glare_sym = np.random.uniform(0.0, 0.08, n)

    # Skewed: High symmetry difference (>0.12), medium laplacian
    skew_lap = np.random.uniform(100, 350, n)
    skew_bright = np.random.uniform(100, 170, n)
    skew_std = np.random.uniform(40, 65, n)
    skew_glare = np.random.uniform(0.0, 0.05, n)
    skew_edge = np.random.uniform(0.06, 0.18, n)
    skew_sym = np.random.uniform(0.12, 0.35, n)

    lap = np.concatenate([good_lap, blur_lap, glare_lap, skew_lap])
    bright = np.concatenate([good_bright, blur_bright, glare_bright, skew_bright])
    std_b = np.concatenate([good_std, blur_std, glare_std, skew_std])
    glare = np.concatenate([good_glare, blur_glare, glare_glare, skew_glare])
    edge = np.concatenate([good_edge, blur_edge, glare_edge, skew_edge])
    sym = np.concatenate([good_sym, blur_sym, glare_sym, skew_sym])
    
    labels = np.array([0]*n + [1]*n + [2]*n + [3]*n)

    df = pd.DataFrame({
        "laplacian_var": lap,
        "mean_brightness": bright,
        "std_brightness": std_b,
        "glare_ratio": glare,
        "edge_density": edge,
        "symmetry_diff": sym
    })
    return df, labels

def train_quality_classifier():
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
    raw_images_dir = os.path.join(os.getcwd(), "ml", "data", "raw_images")
    image_paths = glob.glob(os.path.join(raw_images_dir, "*.jpg")) + glob.glob(os.path.join(raw_images_dir, "*.png"))

    if len(image_paths) >= 20:
        print(f"Extracting CV features from {len(image_paths)} local images...")
        features_list = []
        labels_list = []
        for p in image_paths:
            img = cv2.imread(p)
            if img is not None:
                feats = extract_cv_features(img)
                features_list.append(feats)
                # Infer label from filename convention if present
                if "blur" in p.lower():
                    labels_list.append(1)
                elif "glare" in p.lower():
                    labels_list.append(2)
                elif "skew" in p.lower():
                    labels_list.append(3)
                else:
                    labels_list.append(0)
        X = pd.DataFrame(features_list)
        y = np.array(labels_list)
    else:
        print("Using synthetic CV feature dataset for Model 1 quality classifier...")
        X, y = generate_synthetic_quality_data(num_samples=800)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model 1 Quality Classifier Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=["good", "blurry", "glare", "skewed"]))

    joblib.dump(clf, MODEL_PATH)
    print(f"Saved quality classifier to {MODEL_PATH}")
    return clf

if __name__ == "__main__":
    train_quality_classifier()
