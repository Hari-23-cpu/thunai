from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "processed" / "support_tweets.csv"
GOLDEN_PATH = ROOT / "data" / "golden" / "golden_set.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "intent_training.csv"

MAX_PER_INTENT = 500
OTHER_UNCLEAR_MAX = 300
MIN_TEXT_LENGTH = 15

INTENTS = [
    "delivery_delay",
    "missing_delivered",
    "damaged_item",
    "refund_request",
    "cancellation_request",
    "account_access",
    "prime_membership",
    "technical_support",
    "other_unclear"
]

PATTERNS = {
    "missing_delivered": [
        r"\bdelivered\b.*\b(not|never|didn.?t|haven.?t|missing|receive|got)\b",
        r"\b(not|never|didn.?t|haven.?t)\b.*\b(receive|received|get|got)\b.*\b(deliver|package|parcel|order)\b",
        r"\bpackage\b.*\bmarked\b.*\bdelivered\b",
        r"\border\b.*\bmarked\b.*\bdelivered\b"
    ],
    "damaged_item": [
        r"\bdamag(ed|e)?\b",
        r"\bbroken\b",
        r"\bcracked\b",
        r"\bdefect(ive)?\b",
        r"\bnot working\b.*\b(item|product|device)\b",
        r"\barrived\b.*\b(broken|damaged|defective)\b"
    ],
    "refund_request": [
        r"\brefund\b",
        r"\breimburse\b",
        r"\breimbursement\b",
        r"\bcharged\b.*\b(double|twice|again)\b",
        r"\bdouble charged\b",
        r"\bcharged\b.*\bwrong\b",
        r"\bunauthori[sz]ed\b.*\bcharge\b",
        r"\bmoney\b.*\bback\b",
        r"\bpayment\b.*\b(refund|charge)\b"
    ],
    "cancellation_request": [
        r"\bcancel\b",
        r"\bcancellation\b",
        r"\bcanceling\b",
        r"\bcancelling\b",
        r"\bwant\b.*\bcancel\b",
        r"\bplease\b.*\bcancel\b",
        r"\bcan\b.*\bcancel\b"
    ],
    "account_access": [
        r"\blog.?in\b",
        r"\bsign.?in\b",
        r"\bpassword\b",
        r"\baccount\b.*\b(access|locked|hold|email)\b",
        r"\bcan.?t\b.*\baccess\b.*\baccount\b",
        r"\bemail\b.*\baccount\b"
    ],
    "prime_membership": [
        r"\bprime membership\b",
        r"\bprime trial\b",
        r"\bprime benefits\b",
        r"\bprime account\b",
        r"\bprime\b.*\bmembership\b",
        r"\bmembership\b.*\bprime\b",
        r"\bmembership\b.*\bcharge\b",
        r"\bmembership\b.*\bcancel\b",
        r"\bprime\b.*\bcharge\b"
    ],
    "technical_support": [
        r"\bapp\b.*\b(crash|freeze|freezing|error|bug|not working)\b",
        r"\bwebsite\b.*\b(error|not working|broken|issue)\b",
        r"\bsite\b.*\b(error|not working|issue)\b",
        r"\bdevice\b.*\b(not working|error|issue)\b",
        r"\bkindle\b.*\b(error|issue|not working)\b",
        r"\balexa\b.*\b(error|issue|not working|configure)\b",
        r"\bsetting(s)?\b.*\b(error|issue|not working)\b",
        r"\btechnical\b",
        r"\bcrash(es|ed|ing)?\b",
        r"\bfreez(e|es|ing|ed)\b"
    ],
    "delivery_delay": [
        r"\bdelivery\b.*\b(delay|late|delayed|slow)\b",
        r"\bdelayed\b",
        r"\blate\b.*\b(delivery|order|package|parcel)\b",
        r"\bwaiting\b.*\b(order|package|parcel|delivery)\b",
        r"\bhasn.?t\b.*\barriv(ed|e)\b",
        r"\bnot\b.*\barriv(ed|e)\b",
        r"\bwhere\b.*\b(my|the)\b.*\b(order|package|parcel)\b",
        r"\btracking\b.*\b(stuck|not|update|updated)\b",
        r"\bexpected\b.*\b(delivery|date)\b",
        r"\boverdue\b"
    ]
}

def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"&\w+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def label_text(text):
    text = normalize_text(text)
    scores = {intent: 0 for intent in INTENTS if intent != "other_unclear"}

    for intent, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                scores[intent] += 1

    priority = [
        "missing_delivered",
        "damaged_item",
        "refund_request",
        "cancellation_request",
        "account_access",
        "technical_support",
        "delivery_delay",
        "prime_membership"
    ]

    ranked = sorted(
        scores.items(),
        key=lambda x: (-x[1], priority.index(x[0]))
    )

    best_intent, best_score = ranked[0]
    second_score = ranked[1][1]

    if best_score == 0:
        return "other_unclear", 0

    if best_score == second_score:
        return "other_unclear", 0

    return best_intent, best_score

def load_customer_messages():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Source dataset not found: {SOURCE_PATH}")

    df = pd.read_csv(SOURCE_PATH)

    required = {"tweet_id", "text", "inbound"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Source dataset is missing columns: {sorted(missing)}"
        )

    inbound = df["inbound"].astype(str).str.strip().str.lower()

    df = df[inbound.isin(["1", "true", "yes"])].copy()
    df = df.dropna(subset=["tweet_id", "text"])

    df["tweet_id"] = df["tweet_id"].astype(str).str.strip()
    df["text"] = df["text"].astype(str).str.strip()

    df = df[
        (df["tweet_id"] != "") &
        (df["text"] != "")
    ]

    df = df[
        df["text"].str.len() >= MIN_TEXT_LENGTH
    ]

    df = df.drop_duplicates(subset=["tweet_id"])

    df["_normalized_text"] = df["text"].map(normalize_text)
    df = df[df["_normalized_text"] != ""]
    df = df.drop_duplicates(subset=["_normalized_text"])

    return df

def load_golden_ids():
    if not GOLDEN_PATH.exists():
        raise FileNotFoundError(
            f"Golden set not found: {GOLDEN_PATH}"
        )

    golden = pd.read_csv(GOLDEN_PATH)

    if "tweet_id" not in golden.columns:
        raise ValueError("Golden set must contain tweet_id")

    return set(
        golden["tweet_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

def build_training_set():
    print("Loading prepared AmazonHelp customer dataset...")

    df = load_customer_messages()

    print(f"Customer messages available: {len(df)}")

    golden_ids = load_golden_ids()

    print(
        f"Golden evaluation examples protected: {len(golden_ids)}"
    )

    original_count = len(df)

    df = df[
        ~df["tweet_id"].isin(golden_ids)
    ].copy()

    print(
        f"Messages remaining after golden-set exclusion: {len(df)}"
    )

    labels = df["text"].map(label_text)

    df["gold_intent"] = labels.map(lambda x: x[0])
    df["label_score"] = labels.map(lambda x: x[1])

    selected = []

    for intent in INTENTS:
        if intent == "other_unclear":
            subset = df[
                df["gold_intent"] == "other_unclear"
            ].copy()

            subset = subset.sort_values(
                ["tweet_id"]
            )

            subset = subset.head(OTHER_UNCLEAR_MAX)
        else:
            subset = df[
                df["gold_intent"] == intent
            ].copy()

            subset = subset.sort_values(
                ["label_score", "tweet_id"],
                ascending=[False, True]
            )

            subset = subset.head(MAX_PER_INTENT)

        selected.append(subset)

    result = pd.concat(
        selected,
        ignore_index=True
    )

    if result.empty:
        raise RuntimeError(
            "No labeled training examples were created."
        )

    result = result[
        ["tweet_id", "text", "gold_intent"]
    ].rename(
        columns={"text": "customer_text"}
    )

    result = result.drop_duplicates(
        subset=["tweet_id"]
    )

    result = result.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\nINTENT TRAINING DATASET")
    print("-----------------------")
    print(
        f"Original customer messages: {original_count}"
    )
    print(
        f"Training examples: {len(result)}"
    )
    print(
        f"Intents: {result['gold_intent'].nunique()}"
    )

    print("\nIntent distribution:")
    print(
        result["gold_intent"]
        .value_counts()
        .to_string()
    )

    print(
        f"\nOutput: {OUTPUT_PATH}"
    )

    print(
        "\nGolden-set leakage check: PASSED"
    )

    print(
        "Labels are silver labels generated by deterministic rules."
    )

if __name__ == "__main__":
    build_training_set()