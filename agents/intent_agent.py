import json
import os
from pathlib import Path
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "data" / "golden" / "intent_taxonomy.json"

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

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY is not set in the environment.")

client = genai.Client(api_key=API_KEY)

def load_taxonomy():
    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(f"Intent taxonomy not found: {TAXONOMY_PATH}")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def classify_intent(customer_message):
    if not customer_message or not str(customer_message).strip():
        return {
            "intent": "other_unclear",
            "confidence": 0.0,
            "reason": "Customer message is empty."
        }

    taxonomy = load_taxonomy()

    prompt = f"""
You are an intent classification agent for Amazon customer support.

Allowed intent IDs:
{json.dumps(INTENTS, ensure_ascii=False)}

Intent taxonomy:
{json.dumps(taxonomy, ensure_ascii=False)}

Customer message:
{customer_message}

Rules:
- Choose exactly ONE intent from the allowed intent IDs.
- Choose the customer's primary problem.
- Use the taxonomy definitions.
- Do not invent a new intent.
- Do not classify based only on one keyword.
- If the message is ambiguous, unclear, or does not confidently match an intent, choose other_unclear.
- Return valid JSON only.

Required JSON:
{{
  "intent": "one_allowed_intent",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    result = json.loads(response.text)

    intent = result.get("intent", "other_unclear")
    if intent not in INTENTS:
        intent = "other_unclear"

    try:
        confidence = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

    return {
        "intent": intent,
        "confidence": confidence,
        "reason": str(result.get("reason", "")).strip()
    }

if __name__ == "__main__":
    message = input("Customer message: ").strip()
    result = classify_intent(message)
    print(json.dumps(result, indent=2, ensure_ascii=False))