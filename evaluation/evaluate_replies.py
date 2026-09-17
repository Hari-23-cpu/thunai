import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.intent_agent import classify_intent
from memory.retrieval_memory import HistoricalRetriever
from agents.reply_agent import generate_reply

GOLDEN_PATH = ROOT / "data" / "golden" / "golden_set.csv"
OUTPUT_PATH = ROOT / "evaluation" / "reply_evaluation_results.json"

def load_golden_set():
    with open(GOLDEN_PATH, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_results(results):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    golden = load_golden_set()
    print(f"Golden examples: {len(golden)}")

    retriever = HistoricalRetriever()
    results = []

    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                results = json.load(f)
            print(f"Resuming from saved results: {len(results)}")
        except Exception:
            results = []

    completed_ids = {
        str(r.get("tweet_id"))
        for r in results
        if "error" not in r
    }

    historical_cache = {}

    for index, row in enumerate(golden, 1):
        tweet_id = str(row["tweet_id"])

        if tweet_id in completed_ids:
            print(f"[{index}/{len(golden)}] SKIP {row['customer_text'][:60]}")
            continue

        message = row["customer_text"]
        expected_intent = row["gold_intent"]

        print(f"[{index}/{len(golden)}] {message[:80]}")

        try:
            intent_result = classify_intent(message)

            if message not in historical_cache:
                historical_cache[message] = retriever.retrieve(
                    message,
                    top_k=3
                )

            historical_matches = historical_cache[message]

            reply_result = generate_reply(
                message,
                intent_result,
                historical_matches,
                conversation_history=[]
            )

            results.append({
                "tweet_id": tweet_id,
                "customer_message": message,
                "expected_intent": expected_intent,
                "predicted_intent": intent_result.get("intent"),
                "intent_confidence": intent_result.get("confidence"),
                "intent_reason": intent_result.get("reason"),
                "historical_matches": historical_matches,
                "reply": reply_result.get("reply"),
                "evidence": reply_result.get("evidence"),
                "evidence_sufficient": reply_result.get("evidence_sufficient"),
                "reply_reason": reply_result.get("reason")
            })

        except Exception as e:
            results.append({
                "tweet_id": tweet_id,
                "customer_message": message,
                "expected_intent": expected_intent,
                "error": str(e)
            })

        save_results(results)

    successful = [r for r in results if "error" not in r]

    intent_correct = sum(
        r.get("expected_intent") == r.get("predicted_intent")
        for r in successful
    )

    accuracy = intent_correct / len(successful) if successful else 0

    print("\nREPLY EVALUATION")
    print("----------------")
    print(f"Examples: {len(golden)}")
    print(f"Successful: {len(successful)}")
    print(f"Intent accuracy: {accuracy:.4f}")
    print(f"Results: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
