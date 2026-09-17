import json
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden" / "golden_set.csv"
TRAINING_PATH = ROOT / "data" / "processed" / "intent_training.csv"
OUTPUT_PATH = ROOT / "data" / "golden" / "baseline_results.json"

def load_data():
    golden = pd.read_csv(GOLDEN_PATH)
    training = pd.read_csv(TRAINING_PATH)

    required_golden = {"customer_text", "gold_intent"}
    required_training = {"customer_text", "gold_intent"}

    missing_golden = required_golden - set(golden.columns)
    missing_training = required_training - set(training.columns)

    if missing_golden:
        raise ValueError(f"Golden set is missing columns: {sorted(missing_golden)}")
    if missing_training:
        raise ValueError(f"Training set is missing columns: {sorted(missing_training)}")

    golden = golden.dropna(subset=["customer_text", "gold_intent"]).copy()
    training = training.dropna(subset=["customer_text", "gold_intent"]).copy()

    golden["customer_text"] = golden["customer_text"].astype(str).str.strip()
    training["customer_text"] = training["customer_text"].astype(str).str.strip()

    golden["gold_intent"] = golden["gold_intent"].astype(str).str.strip()
    training["gold_intent"] = training["gold_intent"].astype(str).str.strip()

    golden = golden[golden["customer_text"] != ""]
    training = training[training["customer_text"] != ""]

    return training, golden

def evaluate():
    training, golden = load_data()

    X_train = training["customer_text"]
    y_train = training["gold_intent"]
    X_test = golden["customer_text"]
    y_test = golden["gold_intent"]

    majority_intent = y_test.value_counts().idxmax()
    majority_predictions = [majority_intent] * len(y_test)

    majority_accuracy = accuracy_score(y_test, majority_predictions)
    majority_macro_f1 = f1_score(
        y_test,
        majority_predictions,
        average="macro",
        zero_division=0
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=30000
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    )

    classifier.fit(X_train_tfidf, y_train)
    predictions = classifier.predict(X_test_tfidf)

    tfidf_accuracy = accuracy_score(y_test, predictions)
    tfidf_macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    report = classification_report(
        y_test,
        predictions,
        output_dict=True,
        zero_division=0
    )

    labels = sorted(set(y_test) | set(predictions))
    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels
    )

    per_intent = {}

    for intent in labels:
        metrics = report.get(intent, {})
        per_intent[intent] = {
            "precision": round(float(metrics.get("precision", 0)), 4),
            "recall": round(float(metrics.get("recall", 0)), 4),
            "f1": round(float(metrics.get("f1-score", 0)), 4),
            "support": int(metrics.get("support", 0))
        }

    results = {
        "evaluation": {
            "golden_examples": len(golden),
            "training_examples": len(training),
            "training_labels_are_silver": True,
            "golden_labels_are_human_verified": False
        },
        "majority_baseline": {
            "majority_intent": majority_intent,
            "accuracy": round(float(majority_accuracy), 4),
            "macro_f1": round(float(majority_macro_f1), 4)
        },
        "tfidf_logistic_regression": {
            "accuracy": round(float(tfidf_accuracy), 4),
            "macro_f1": round(float(tfidf_macro_f1), 4),
            "per_intent": per_intent,
            "confusion_matrix_labels": labels,
            "confusion_matrix": matrix.tolist()
        }
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("CLASSIFIER EVALUATION")
    print("---------------------")
    print(f"Training examples: {len(training)}")
    print(f"Evaluation examples: {len(golden)}")
    print()
    print("MAJORITY BASELINE")
    print(f"Majority intent: {majority_intent}")
    print(f"Accuracy: {majority_accuracy:.4f}")
    print(f"Macro-F1: {majority_macro_f1:.4f}")
    print()
    print("TF-IDF + LOGISTIC REGRESSION")
    print(f"Accuracy: {tfidf_accuracy:.4f}")
    print(f"Macro-F1: {tfidf_macro_f1:.4f}")
    print()
    print("PER-INTENT RESULTS")
    for intent, metrics in per_intent.items():
        print(
            f"{intent}: "
            f"precision={metrics['precision']:.4f}, "
            f"recall={metrics['recall']:.4f}, "
            f"f1={metrics['f1']:.4f}, "
            f"support={metrics['support']}"
        )
    print()
    print("Results saved to:")
    print(OUTPUT_PATH)

if __name__ == "__main__":
    evaluate()