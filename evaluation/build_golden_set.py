from pathlib import Path
import re
import unicodedata
import numpy as np
import pandas as pd

SEED = 42
TARGET_SIZE = 200
PROCESSED_PATH = Path("data/processed/support_tweets.csv")
DISCOVERY_PATH = Path("data/golden/intent_discovery_sample.csv")
TAXONOMY_PATH = Path("data/golden/intent_taxonomy.json")
OUTPUT_PATH = Path("data/golden/golden_set.csv")
RNG = np.random.default_rng(SEED)

def normalize_text(text):
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def is_multilingual(text):
    if not text:
        return False
    return any(ord(char) > 127 for char in text)

def is_short_or_noisy(text):
    if not text:
        return True
    normalized = normalize_text(text)
    word_count = len(normalized.split())
    char_count = len(normalized)
    punctuation_count = sum(not char.isalnum() and not char.isspace() for char in normalized)
    return word_count <= 6 or char_count <= 35 or punctuation_count >= max(3, char_count * 0.15)

def load_prepared_dataset():
    df = pd.read_csv(PROCESSED_PATH)
    required = {"tweet_id", "text", "inbound"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Prepared dataset is missing columns: {sorted(missing)}")
    df = df[df["inbound"].astype(str).str.strip() == "1"].copy()
    df = df.dropna(subset=["tweet_id", "text"])
    df["tweet_id"] = df["tweet_id"].astype(str).str.strip()
    df["text"] = df["text"].astype(str)
    df = df[df["tweet_id"] != ""]
    df = df[df["text"].str.strip() != ""]
    df = df.drop_duplicates(subset=["tweet_id"])
    df = df.drop_duplicates(subset=["text"])
    df["_normalized_text"] = df["text"].map(normalize_text)
    df = df[df["_normalized_text"] != ""]
    df = df.drop_duplicates(subset=["_normalized_text"])
    return df

def load_discovery_ids():
    if not DISCOVERY_PATH.exists():
        return set()
    discovery = pd.read_csv(DISCOVERY_PATH)
    if "tweet_id" not in discovery.columns:
        return set()
    return set(discovery["tweet_id"].dropna().astype(str).str.strip())

def sample_from_pool(pool, count):
    if count <= 0 or pool.empty:
        return pool.iloc[0:0].copy()
    count = min(count, len(pool))
    indices = RNG.choice(len(pool), size=count, replace=False)
    return pool.iloc[indices].copy()

def build_candidate_set(customers):
    selected_ids = set()
    selected_parts = []
    discovery_ids = load_discovery_ids()
    discovery_pool = customers[customers["tweet_id"].isin(discovery_ids)].copy()
    discovery_sample = sample_from_pool(discovery_pool, min(80, len(discovery_pool)))
    if not discovery_sample.empty:
        selected_parts.append(discovery_sample)
        selected_ids.update(discovery_sample["tweet_id"])
    multilingual_pool = customers[customers["text"].map(is_multilingual) & ~customers["tweet_id"].isin(selected_ids)]
    multilingual_sample = sample_from_pool(multilingual_pool, min(35, len(multilingual_pool)))
    if not multilingual_sample.empty:
        selected_parts.append(multilingual_sample)
        selected_ids.update(multilingual_sample["tweet_id"])
    noisy_pool = customers[customers["text"].map(is_short_or_noisy) & ~customers["tweet_id"].isin(selected_ids)]
    noisy_sample = sample_from_pool(noisy_pool, min(30, len(noisy_pool)))
    if not noisy_sample.empty:
        selected_parts.append(noisy_sample)
        selected_ids.update(noisy_sample["tweet_id"])
    delivery_pattern = re.compile(r"\b(delivery|delivered|package|parcel|shipment|shipping|tracking|arrive|arrived|late|lost|missing|order)\b", re.IGNORECASE)
    delivery_pool = customers[customers["text"].str.contains(delivery_pattern, na=False) & ~customers["tweet_id"].isin(selected_ids)]
    delivery_sample = sample_from_pool(delivery_pool, min(20, len(delivery_pool)))
    if not delivery_sample.empty:
        selected_parts.append(delivery_sample)
        selected_ids.update(delivery_sample["tweet_id"])
    billing_pattern = re.compile(r"\b(refund|refunded|refunds|charge|charged|payment|billing|bill|money|credit|debit|price|cost|cancel|cancellation)\b", re.IGNORECASE)
    billing_pool = customers[customers["text"].str.contains(billing_pattern, na=False) & ~customers["tweet_id"].isin(selected_ids)]
    billing_sample = sample_from_pool(billing_pool, min(15, len(billing_pool)))
    if not billing_sample.empty:
        selected_parts.append(billing_sample)
        selected_ids.update(billing_sample["tweet_id"])
    account_pattern = re.compile(r"\b(account|login|log in|password|prime|membership|kindle|app|website|error|device|technical|broken|damaged|defective)\b", re.IGNORECASE)
    account_pool = customers[customers["text"].str.contains(account_pattern, na=False) & ~customers["tweet_id"].isin(selected_ids)]
    account_sample = sample_from_pool(account_pool, min(15, len(account_pool)))
    if not account_sample.empty:
        selected_parts.append(account_sample)
        selected_ids.update(account_sample["tweet_id"])
    selected = pd.concat(selected_parts, ignore_index=True) if selected_parts else customers.iloc[0:0].copy()
    selected = selected.drop_duplicates(subset=["tweet_id"])
    remaining = customers[~customers["tweet_id"].isin(selected["tweet_id"])].copy()
    remaining_sample = sample_from_pool(remaining, TARGET_SIZE - len(selected))
    selected = pd.concat([selected, remaining_sample], ignore_index=True)
    selected = selected.drop_duplicates(subset=["tweet_id"])
    if len(selected) > TARGET_SIZE:
        selected = selected.iloc[RNG.choice(len(selected), size=TARGET_SIZE, replace=False)]
    return selected.reset_index(drop=True)

def validate_golden_set(golden, customers):
    errors = []
    if len(golden) != TARGET_SIZE:
        errors.append(f"Expected {TARGET_SIZE} rows, found {len(golden)}.")
    if not golden["tweet_id"].is_unique:
        errors.append("Duplicate tweet IDs found.")
    customer_ids = set(customers["tweet_id"])
    invalid_ids = set(golden["tweet_id"]) - customer_ids
    if invalid_ids:
        errors.append(f"{len(invalid_ids)} tweet IDs do not exist in source.")
    source_text = customers.set_index("tweet_id")["text"]
    for _, row in golden.iterrows():
        tweet_id = row["tweet_id"]
        if tweet_id not in source_text:
            continue
        if row["customer_text"] != source_text.loc[tweet_id]:
            errors.append(f"Text mismatch for tweet_id={tweet_id}")
    if not golden["tweet_id"].isin(customer_ids).all():
        errors.append("Golden set contains non-customer messages.")
    nonblank_gold = golden["gold_intent"].fillna("").astype(str).str.strip()
    if (nonblank_gold != "").any():
        errors.append("gold_intent contains labels. Candidate set must remain unlabeled.")
    required_output = {"tweet_id", "customer_text", "gold_intent", "notes", "source"}
    missing = required_output - set(golden.columns)
    if missing:
        errors.append(f"Missing output columns: {sorted(missing)}")
    if errors:
        raise AssertionError("\n".join(f"- {error}" for error in errors))

def print_report(golden):
    texts = golden["customer_text"]
    multilingual_count = texts.map(is_multilingual).sum()
    noisy_count = texts.map(is_short_or_noisy).sum()
    print("=" * 60)
    print("GOLDEN CANDIDATE SET")
    print("=" * 60)
    print(f"Rows: {len(golden)}")
    print(f"Unique tweet IDs: {golden['tweet_id'].nunique()}")
    print(f"Multilingual/non-ASCII: {multilingual_count}")
    print(f"Short/noisy: {noisy_count}")
    print()
    print("Text length statistics")
    print(f"Minimum: {texts.str.len().min()}")
    print(f"Median: {texts.str.len().median():.0f}")
    print(f"Maximum: {texts.str.len().max()}")
    print()
    print("Source distribution")
    print(golden["source"].value_counts().to_string())
    print()
    print("gold_intent status")
    print("All labels intentionally blank.")
    print("Human verification is required before final evaluation.")

def main():
    print("Loading prepared AmazonHelp customer dataset...")
    customers = load_prepared_dataset()
    print(f"Customer messages available: {len(customers):,}")
    print("Building deterministic diverse candidate set...")
    selected = build_candidate_set(customers)
    if len(selected) < TARGET_SIZE:
        raise RuntimeError(f"Only {len(selected)} valid examples could be selected; {TARGET_SIZE} required.")
    golden = pd.DataFrame({
        "tweet_id": selected["tweet_id"].astype(str),
        "customer_text": selected["text"],
        "gold_intent": "",
        "notes": "",
        "source": "prepared_amazonhelp_dataset",
    })
    validate_golden_set(golden, customers)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    golden.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print_report(golden)
    print()
    print("=" * 60)
    print("VALIDATION PASSED")
    print("=" * 60)
    print(f"Output: {OUTPUT_PATH}")
    print(f"Seed: {SEED}")
    print("Taxonomy was not modified.")
    print("No gold labels were fabricated.")
    print("All messages originate from the prepared dataset.")

if __name__ == "__main__":
    main()