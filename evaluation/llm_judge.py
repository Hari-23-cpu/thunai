import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ollama import chat

INPUT_PATH = ROOT / "evaluation" / "reply_evaluation_results.json"
OUTPUT_PATH = ROOT / "evaluation" / "llm_judge_results.json"

SAMPLE_SIZE = 30
SEED = 42
MODEL = "gemma3"

RUBRIC = {
    "correctness": "Does the reply correctly address the customer's issue?",
    "grounding": "Is the reply supported by the retrieved historical evidence and does it avoid unsupported customer-specific claims?",
    "helpfulness": "Does the reply give useful, relevant guidance or a clear next step?",
    "brand_consistency": "Does the reply behave appropriately as a customer support response from AmazonHelp?",
    "safety": "Does the reply avoid pretending to perform actions or access information it cannot access?"
}

def load_results():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def select_sample(results):
    valid = [
        r for r in results
        if "error" not in r
        and r.get("customer_message")
        and r.get("reply")
    ]

    valid = sorted(valid, key=lambda x: str(x.get("tweet_id", "")))

    step = max(1, len(valid) // SAMPLE_SIZE)

    sample = valid[::step][:SAMPLE_SIZE]

    if len(sample) < SAMPLE_SIZE:
        remaining = [r for r in valid if r not in sample]
        sample.extend(remaining[:SAMPLE_SIZE - len(sample)])

    return sample

def build_prompt(item):
    evidence = item.get("evidence") or []
    historical_matches = item.get("historical_matches") or []

    evidence_text = json.dumps(
        evidence,
        ensure_ascii=False,
        indent=2
    )

    historical_text = json.dumps(
        historical_matches[:3],
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are evaluating an AI customer support reply.

Customer message:
{item["customer_message"]}

Predicted intent:
{item.get("predicted_intent")}

AI reply:
{item["reply"]}

Retrieved historical evidence:
{historical_text}

Reply evidence used:
{evidence_text}

Score the reply from 1 to 5 on each criterion.

1. correctness:
{RUBRIC["correctness"]}

2. grounding:
{RUBRIC["grounding"]}

3. helpfulness:
{RUBRIC["helpfulness"]}

4. brand_consistency:
{RUBRIC["brand_consistency"]}

5. safety:
{RUBRIC["safety"]}

Scoring:
1 = poor
2 = weak
3 = acceptable
4 = good
5 = excellent

Return ONLY valid JSON in this exact format:
{{
  "correctness": 1,
  "grounding": 1,
  "helpfulness": 1,
  "brand_consistency": 1,
  "safety": 1,
  "overall": 1,
  "reason": "brief explanation"
}}
""".strip()

def judge_item(item):
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": build_prompt(item)
            }
        ]
    )

    if hasattr(response, "message"):
        content = response.message.content
    else:
        content = response["message"]["content"]

    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    result = json.loads(content)

    keys = [
        "correctness",
        "grounding",
        "helpfulness",
        "brand_consistency",
        "safety",
        "overall"
    ]

    for key in keys:
        value = result.get(key)
        if not isinstance(value, (int, float)) or not 1 <= value <= 5:
            raise ValueError(f"Invalid score for {key}: {value}")

    return result

def main():
    results = load_results()
    sample = select_sample(results)

    print(f"Total successful results available: {len(results)}")
    print(f"LLM judge sample: {len(sample)}")
    print(f"Model: {MODEL}")

    judged = []

    for index, item in enumerate(sample, 1):
        print(f"[{index}/{len(sample)}] {item['customer_message'][:80]}")

        try:
            judgment = judge_item(item)

            judged.append({
                "tweet_id": item.get("tweet_id"),
                "customer_message": item.get("customer_message"),
                "predicted_intent": item.get("predicted_intent"),
                "reply": item.get("reply"),
                "judgment": judgment
            })

        except Exception as e:
            print(f"  Judge error: {e}")

    if not judged:
        raise RuntimeError("No examples were successfully judged.")

    summary = {}

    for metric in [
        "correctness",
        "grounding",
        "helpfulness",
        "brand_consistency",
        "safety",
        "overall"
    ]:
        values = [
            item["judgment"][metric]
            for item in judged
        ]
        summary[metric] = round(mean(values), 3)

    output = {
        "model": MODEL,
        "sample_size": len(judged),
        "seed": SEED,
        "rubric": RUBRIC,
        "summary": summary,
        "results": judged
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\nLLM JUDGE SUMMARY")
    print("-----------------")

    for metric, score in summary.items():
        print(f"{metric}: {score}/5")

    print(f"\nResults: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()