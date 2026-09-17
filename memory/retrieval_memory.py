from pathlib import Path
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "support_tweets.csv"

class HistoricalRetriever:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = Path(data_path)
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2
        )
        self.customer_messages = None
        self.customer_vectors = None
        self.load_data()

    def normalize_text(self, text):
        text = str(text).lower()
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"@\w+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def load_data(self):
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Prepared dataset not found: {self.data_path}"
            )

        df = pd.read_csv(self.data_path)

        required = {
            "tweet_id",
            "author_id",
            "inbound",
            "text",
            "response_tweet_id",
            "in_response_to_tweet_id",
            "thread_id"
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"Dataset is missing columns: {sorted(missing)}"
            )

        df = df.dropna(subset=["tweet_id", "text"])
        df["tweet_id"] = df["tweet_id"].astype(str).str.strip()
        df["text"] = df["text"].astype(str).str.strip()
        df["inbound"] = df["inbound"].astype(str).str.lower()

        df = df[
            (df["tweet_id"] != "") &
            (df["text"] != "")
        ].copy()

        tweet_lookup = {}

        for _, row in df.iterrows():
            tweet_lookup[row["tweet_id"]] = {
                "text": row["text"],
                "author_id": row["author_id"],
                "inbound": row["inbound"],
                "thread_id": row["thread_id"]
            }

        records = []

        for _, row in df.iterrows():
            if row["inbound"] not in {"true", "1", "yes"}:
                continue

            response_ids = str(row["response_tweet_id"])

            if response_ids == "nan":
                response_ids = ""

            response_ids = [
                x.strip()
                for x in response_ids.split(",")
                if x.strip()
            ]

            responses = []

            for response_id in response_ids:
                response = tweet_lookup.get(response_id)

                if response and response["author_id"] == "AmazonHelp":
                    responses.append(response["text"])

            if not responses:
                continue

            customer_text = row["text"]

            records.append({
                "tweet_id": row["tweet_id"],
                "thread_id": row["thread_id"],
                "customer_text": customer_text,
                "response_text": " ".join(responses)
            })

        self.customer_messages = pd.DataFrame(records)

        if self.customer_messages.empty:
            raise RuntimeError(
                "No customer messages with AmazonHelp responses were found."
            )

        normalized = self.customer_messages[
            "customer_text"
        ].map(self.normalize_text)

        self.customer_vectors = self.vectorizer.fit_transform(
            normalized
        )

        print(
            f"Historical examples indexed: {len(self.customer_messages)}"
        )

    def retrieve(self, customer_message, top_k=3, min_similarity=0.10):
        if not customer_message or not str(customer_message).strip():
            return []

        query = self.normalize_text(customer_message)

        query_vector = self.vectorizer.transform([query])

        similarities = cosine_similarity(
            query_vector,
            self.customer_vectors
        )[0]

        ranked_indices = similarities.argsort()[::-1]

        results = []

        for index in ranked_indices:
            score = float(similarities[index])

            if score < min_similarity:
                break

            row = self.customer_messages.iloc[index]

            results.append({
                "tweet_id": str(row["tweet_id"]),
                "thread_id": int(row["thread_id"]),
                "customer_message": row["customer_text"],
                "historical_response": row["response_text"],
                "similarity": round(score, 4)
            })

            if len(results) >= top_k:
                break

        return results

if __name__ == "__main__":
    retriever = HistoricalRetriever()

    message = input("Customer message: ").strip()

    results = retriever.retrieve(message)

    print("\nHISTORICAL MATCHES")
    print("------------------")

    if not results:
        print("No sufficiently similar historical examples found.")
    else:
        for i, result in enumerate(results, 1):
            print(f"\nMatch {i}")
            print(f"Similarity: {result['similarity']}")
            print(f"Customer: {result['customer_message']}")
            print(f"AmazonHelp: {result['historical_response']}")