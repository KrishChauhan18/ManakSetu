import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from ml.features import CustomFieldFeatureExtractor
from ml.data.generate_sample_data import generate_field_blocks_csv

SAVED_MODEL_DIR = os.path.join(os.getcwd(), "ml", "saved_models")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "field_classifier.joblib")

def train_field_classifier():
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
    csv_path = os.path.join(os.getcwd(), "ml", "data", "prepared", "field_blocks.csv")
    
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating sample data...")
        generate_field_blocks_csv() 

    df = pd.read_csv(csv_path)
    X = df["text"].astype(str)
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Feature Union combining character TF-IDF n-grams (2-4) and CustomFieldFeatureExtractor from ml.features
    union = FeatureUnion([
        ('char_tfidf', TfidfVectorizer(analyzer='char', ngram_range=(2, 4), min_df=2)),
        ('custom_features', CustomFieldFeatureExtractor())
    ])

    pipeline = Pipeline([
        ('features', union),
        ('classifier', LogisticRegression(solver='lbfgs', C=10.0, max_iter=500, random_state=42))
    ])

    print("Training Model 2 Field Type Classifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\n--- Model 2 Classification Report ---")
    print(classification_report(y_test, y_pred))

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved field classifier model pipeline to {MODEL_PATH}")
    return pipeline

if __name__ == "__main__":
    train_field_classifier()
