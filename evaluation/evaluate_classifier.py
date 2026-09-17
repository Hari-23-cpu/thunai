from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden" / "golden_set.csv"
TRAIN_PATH = ROOT / "data" / "processed" / "intent_training.csv"

def load_golden_set():
    df = pd.read_csv(GOLDEN_PATH)
    required = {"tweet_id", "customer_text", "gold_intent"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Golden set is missing columns: {sorted(missing)}")
    df = df.dropna(subset=["customer_text", "gold_intent"]).copy()
    df["customer_text"] = df["customer_text"].astype(str).str.strip()
    df["gold_intent"] = df["gold_intent"].astype(str).str.strip()
    df = df[(df["customer_text"] != "") & (df["gold_intent"] != "")]
    return df

def evaluate_majority_baseline(golden):
    majority_intent = golden["gold_intent"].value_counts().idxmax()
    predictions = [majority_intent] * len(golden)
    accuracy = accuracy_score(golden["gold_intent"], predictions)
    macro_f1 = f1_score(golden["gold_intent"], predictions, average="macro", zero_division=0)
    print("\nMAJORITY CLASS BASELINE")
    print("-----------------------")
    print(f"Majority intent: {majority_intent}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro-F1: {macro_f1:.4f}")
    print("\nClassification report:")
    print(classification_report(golden["gold_intent"], predictions, zero_division=0))

def evaluate_tfidf_baseline(golden):
    if not TRAIN_PATH.exists():
        print("\nTF-IDF + LOGISTIC REGRESSION")
        print("----------------------------")
        print(f"Training file not found: {TRAIN_PATH}")
        print("Create a separate labeled training dataset before running this baseline.")
        return
    train = pd.read_csv(TRAIN_PATH)
    required = {"customer_text", "gold_intent"}
    missing = required - set(train.columns)
    if missing:
        raise ValueError(f"Training set is missing columns: {sorted(missing)}")
    overlap = set(train["customer_text"].astype(str)) & set(golden["customer_text"].astype(str))
    if overlap:
        raise ValueError(f"Training/evaluation leakage detected: {len(overlap)} overlapping messages.")
    train = train.dropna(subset=["customer_text", "gold_intent"]).copy()
    train["customer_text"] = train["customer_text"].astype(str).str.strip()
    train["gold_intent"] = train["gold_intent"].astype(str).str.strip()
    train = train[(train["customer_text"] != "") & (train["gold_intent"] != "")]
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced"
        ))
    ])
    model.fit(train["customer_text"], train["gold_intent"])
    predictions = model.predict(golden["customer_text"])
    accuracy = accuracy_score(golden["gold_intent"], predictions)
    macro_f1 = f1_score(golden["gold_intent"], predictions, average="macro", zero_division=0)
    print("\nTF-IDF + LOGISTIC REGRESSION")
    print("---------------------------")
    print(f"Training examples: {len(train)}")
    print(f"Evaluation examples: {len(golden)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro-F1: {macro_f1:.4f}")
    print("\nClassification report:")
    print(classification_report(golden["gold_intent"], predictions, zero_division=0))
    labels = sorted(golden["gold_intent"].unique())
    matrix = confusion_matrix(golden["gold_intent"], predictions, labels=labels)
    confusion = pd.DataFrame(matrix, index=labels, columns=labels)
    print("\nConfusion matrix:")
    print(confusion.to_string())

def main():
    print("Loading golden evaluation set...")
    golden = load_golden_set()
    print(f"Golden examples: {len(golden)}")
    print("\nIntent distribution:")
    print(golden["gold_intent"].value_counts().to_string())
    evaluate_majority_baseline(golden)
    evaluate_tfidf_baseline(golden)

if __name__ == "__main__":
    main()