from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path("data/raw/twcs.csv")
OUT_PATH = Path("data/processed/support_tweets.csv")

# Fixed by the earlier brand analysis -- do not pick another brand here.
BRAND = "AmazonHelp"

MAX_CONVERSATIONS = 5000  # most conversation threads to keep, not most tweets
CHUNK_SIZE = 200_000

# Columns needed downstream. created_at is skipped: timestamps are unused.
USE_COLS = [
    "tweet_id",
    "author_id",
    "inbound",
    "text",
    "response_tweet_id",
    "in_response_to_tweet_id",
]
OUT_COLS = USE_COLS + ["thread_id"]
ID_COLS = ["tweet_id", "author_id", "response_tweet_id", "in_response_to_tweet_id"]
INDEX_COLS = ["tweet_id", "author_id", "in_response_to_tweet_id"]


def iter_chunks(path, columns):
    """Read the wanted columns of the dataset in memory-friendly chunks."""
    return pd.read_csv(
        path,
        usecols=columns,
        dtype={col: str for col in columns if col in ID_COLS},
        chunksize=CHUNK_SIZE,
    )


def collect_brand_ids_and_parents(path):
    """Pass 1: AmazonHelp tweet ids plus the tweet id -> parent id index.

    in_response_to_tweet_id already names, for every tweet, the tweet it
    answers, so this one column is enough to rebuild the reply graph; ids are
    converted to int64 and missing ids become -1.
    """
    brand_ids = set()
    id_parts = []
    parent_parts = []
    for chunk in iter_chunks(path, INDEX_COLS):
        own = pd.to_numeric(
            chunk.loc[chunk["author_id"] == BRAND, "tweet_id"], errors="coerce"
        )
        brand_ids.update(own.dropna().astype("int64").tolist())

        ids = pd.to_numeric(chunk["tweet_id"], errors="coerce")
        parents = pd.to_numeric(chunk["in_response_to_tweet_id"], errors="coerce")
        keep = ids.notna()
        id_parts.append(ids[keep].astype("int64").to_numpy())
        parent_parts.append(parents[keep].fillna(-1).astype("int64").to_numpy())
    return brand_ids, np.concatenate(id_parts), np.concatenate(parent_parts)


def build_parent_index(tweet_ids, parent_ids):
    """Sort the id and parent arrays so a parent can be found by tweet id."""
    order = np.argsort(tweet_ids, kind="stable")
    return tweet_ids[order], parent_ids[order]


def make_root_finder(sorted_ids, sorted_parents):
    """Return a function that follows in_response_to up to the true root.

    The walk uses the index, so it crosses chunk boundaries and reaches the
    real first tweet of the conversation instead of stopping at the next
    reply. It returns None when the chain points at a tweet the dataset does
    not contain, which marks the thread as not reconstructable.
    """
    size = sorted_ids.size

    def find_root(tweet_id):
        seen = set()
        while tweet_id not in seen:
            seen.add(tweet_id)
            position = int(np.searchsorted(sorted_ids, tweet_id))
            if position >= size or int(sorted_ids[position]) != tweet_id:
                return None  # a parent tweet is missing from the dataset
            parent = int(sorted_parents[position])
            if parent < 0:
                return tweet_id  # answers nothing: first tweet of the thread
            tweet_id = parent
        return None  # reply chain loops back on itself

    return find_root


def find_brand_roots(brand_ids, find_root):
    """The conversation roots of all AmazonHelp tweets."""
    roots = set()
    for tweet_id in brand_ids:
        root = find_root(tweet_id)
        if root is not None:
            roots.add(root)
    return roots


def extract_tweets(path, find_root, brand_roots):
    """Pass 2: keep every tweet whose conversation root is an AmazonHelp root."""
    parts = []
    for chunk in iter_chunks(path, USE_COLS):
        chunk = chunk.dropna(subset=["tweet_id"])
        cache = {}

        def root_of(tweet_id_text):
            tweet_id = int(tweet_id_text)
            if tweet_id not in cache:
                cache[tweet_id] = find_root(tweet_id)
            return cache[tweet_id]

        thread_ids = chunk["tweet_id"].map(root_of)
        mask = thread_ids.isin(brand_roots)
        kept = chunk[mask].copy()
        kept["thread_id"] = thread_ids[mask].astype("int64").astype(str)
        parts.append(kept)
    return pd.concat(parts, ignore_index=True)


def clean(tweets):
    """Minimal cleaning: drop unusable rows, strip links, ids stay strings."""
    tweets = tweets.dropna(subset=["tweet_id", "text"])
    tweets["text"] = (
        tweets["text"].str.replace(r"https?:\S*", "", regex=True).str.strip()
    )
    for col in ["response_tweet_id", "in_response_to_tweet_id"]:
        tweets[col] = tweets[col].fillna("")
    return tweets


def select_conversations(tweets, max_conversations):
    """Keep all tweets of up to max_conversations complete threads."""
    thread_ids = sorted(tweets["thread_id"].unique())[:max_conversations]
    return tweets[tweets["thread_id"].isin(thread_ids)]


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_PATH}")

    size_mb = RAW_PATH.stat().st_size / (1024 * 1024)
    if size_mb == 0:
        raise ValueError(f"Raw dataset is empty: {RAW_PATH}")

    print("Brand analysis (scripts/brand_analysis.py) picked the brand with")
    print("the most customer messages that got an explicit brand response.")
    print(f"Selected brand: {BRAND}")
    print(f"Reading {RAW_PATH} ({size_mb:.2f} MB) in chunks of {CHUNK_SIZE:,} rows.")

    brand_ids, tweet_ids, parent_ids = collect_brand_ids_and_parents(RAW_PATH)
    sorted_ids, sorted_parents = build_parent_index(tweet_ids, parent_ids)
    find_root = make_root_finder(sorted_ids, sorted_parents)
    brand_roots = find_brand_roots(brand_ids, find_root)
    print(f"AmazonHelp tweets: {len(brand_ids):,}")
    print(f"AmazonHelp conversation threads: {len(brand_roots):,}")

    tweets = extract_tweets(RAW_PATH, find_root, brand_roots)
    tweets = clean(tweets)
    print(f"Tweets in those threads: {len(tweets):,}")

    tweets = select_conversations(tweets, MAX_CONVERSATIONS)
    tweets = tweets[OUT_COLS]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tweets.to_csv(OUT_PATH, index=False)

    customer_messages = int((tweets["inbound"] == True).sum())
    brand_messages = int((tweets["author_id"] == BRAND).sum())

    print()
    print("Dataset")
    print("-------")
    print(f"Filename: {RAW_PATH.name}")
    print(f"File size: {size_mb:.2f} MB")
    print(f"Selected brand: {BRAND}")
    print(f"Tweets written: {len(tweets):,}")
    print(f"Conversation threads: {tweets['thread_id'].nunique():,}")
    print(f"Customer messages: {customer_messages:,}")
    print(f"{BRAND} messages: {brand_messages:,}")
    print(f"Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
