"""
Aswani Hospital - AI Department Recommendation System
Machine Learning Model Training Script

Uses TF-IDF Vectorization and Logistic Regression (or Multinomial Naive Bayes)
to train a multi-class department classifier on patient symptoms.
Saves the serialized model pipeline for high-performance inference in Django.
"""

import os
import re
import string
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import classification_report, accuracy_score


def clean_text(text: str) -> str:
    """
    Standardize text input: lowercase, remove punctuation, normalize whitespace.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def build_pipeline():
    """
    Build a Scikit-learn Pipeline with TF-IDF Vectorizer and Logistic Regression.
    Sublinear TF scaling dampens the effect of repetitive words.
    N-gram range (1, 2) captures both individual keywords and 2-word phrases
    (e.g., 'chest pain', 'knee joint', 'skin rash', 'ear ache', 'missed period').
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True,
            min_df=1,
            strip_accents='unicode'
        )),
        ('classifier', LogisticRegression(
            C=2.0,
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        ))
    ])
    return pipeline


def train():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "data", "symptoms_dataset.csv")
    model_dir = os.path.join(current_dir, "saved_models")
    os.makedirs(model_dir, exist_ok=True)
    model_save_path = os.path.join(model_dir, "department_recommender.joblib")

    print("=" * 60)
    print(" Aswani Hospital - Department Recommendation Model Training")
    print("=" * 60)

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please run build_dataset.py first.")

    print(f"[1/5] Loading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"      Total samples: {len(df)}")
    print(f"      Target classes ({df['department'].nunique()}): {sorted(df['department'].unique())}")

    # Clean text
    df['cleaned_symptoms'] = df['symptoms'].apply(clean_text)
    X = df['cleaned_symptoms']
    y = df['department']

    # 5-Fold Stratified Cross-Validation
    print("\n[2/5] Running 5-Fold Stratified Cross-Validation...")
    pipeline = build_pipeline()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy')
    print(f"      Fold Accuracies: {[round(s, 4) for s in cv_scores]}")
    print(f"      Mean CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")

    # Train / Test split evaluation
    print("\n[3/5] Evaluating on 80/20 Train-Test Split...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"      Test Set Accuracy: {test_acc:.4f}\n")
    print(classification_report(y_test, y_pred, digits=4))

    # Retrain pipeline on 100% of data for production deployment
    print("[4/5] Retraining pipeline on full dataset for production...")
    final_pipeline = build_pipeline()
    final_pipeline.fit(X, y)

    # Bundle model, vectorizer, and metadata
    artifact = {
        'pipeline': final_pipeline,
        'vectorizer': final_pipeline.named_steps['tfidf'],
        'model': final_pipeline.named_steps['classifier'],
        'classes': list(final_pipeline.classes_),
        'metadata': {
            'model_name': 'TF-IDF Logistic Regression Recommender',
            'version': '1.0.0',
            'mean_cv_accuracy': float(np.mean(cv_scores)),
            'test_accuracy': float(test_acc),
            'num_samples': len(df),
            'supported_departments': list(sorted(df['department'].unique())),
        }
    }

    print(f"\n[5/5] Saving model artifact to: {model_save_path}")
    joblib.dump(artifact, model_save_path)
    print(f"      Saved successfully! File size: {os.path.getsize(model_save_path) / 1024:.2f} KB")

    # Sample inference demonstration
    print("\n" + "=" * 60)
    print(" Verification Tests with Clinical Sample Queries:")
    print("=" * 60)
    test_queries = [
        "Doctor, I have severe knee pain and swelling after playing football, cannot walk",
        "Experiencing heavy chest pressure, racing pulse, and left arm numbness",
        "My 6-month-old infant has high fever, crying continuously and refusing milk",
        "Red circular itchy patches spreading all over my arms and neck",
        "Sudden intense throbbing migraine with flashing lights and dizziness",
        "Persistent sore throat, ear blockage, and difficulty swallowing food",
        "Irregular menstrual cycles, severe pelvic cramps, and heavy bleeding",
        "Feeling general fatigue, mild fever, body aches and loss of appetite"
    ]

    for query in test_queries:
        cleaned = clean_text(query)
        pred = final_pipeline.predict([cleaned])[0]
        probs = final_pipeline.predict_proba([cleaned])[0]
        max_prob = np.max(probs) * 100
        print(f"Query: \"{query}\"")
        print(f"  --> Predicted Department: {pred} ({max_prob:.1f}% confidence)\n")


if __name__ == "__main__":
    train()
