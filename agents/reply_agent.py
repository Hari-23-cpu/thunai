import json
import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the .env file")
client = genai.Client(api_key=GEMINI_API_KEY)

def build_conversation_context(conversation_history):
    if not conversation_history:
        return "No previous conversation."

    lines = []
    for message in conversation_history[-8:]:
        role = message.get("role", "unknown")
        content = message.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines) if lines else "No previous conversation."

def build_evidence(historical_matches):
    if not historical_matches:
        return "No historical evidence was retrieved."

    evidence = []
    for i, match in enumerate(historical_matches[:3], 1):
        customer_message = match.get("customer_message", "").strip()
        historical_response = match.get("historical_response", "").strip()

        if customer_message or historical_response:
            evidence.append(
                f"Example {i}:\n"
                f"Customer: {customer_message}\n"
                f"AmazonHelp response: {historical_response}"
            )

    return "\n\n".join(evidence) if evidence else "No historical evidence was retrieved."

def generate_reply(customer_message, intent_result, historical_matches, conversation_history=None):
    conversation_history = conversation_history or []
    conversation_context = build_conversation_context(conversation_history)
    evidence = build_evidence(historical_matches)

    prompt = f"""
You are Thunai, a natural customer-support agent for AmazonHelp.

Have a short, natural conversation with the customer.

CURRENT CUSTOMER MESSAGE:
{customer_message}

DETECTED INTENT:
{json.dumps(intent_result, ensure_ascii=False)}

RECENT CONVERSATION:
{conversation_context}

HISTORICAL AMAZONHELP EXAMPLES:
{evidence}

IMPORTANT CAPABILITY LIMIT:

You do NOT have access to the customer's real Amazon account, order,
payment, refund, delivery, tracking, membership, or device information.

You cannot:
- look up an order
- check tracking
- inspect an account
- verify a payment
- verify a refund
- process a refund
- issue a refund
- cancel an order
- replace an item
- change an account
- access a device
- perform an account action

Therefore NEVER say:
- "provide your order number and I'll look into it"
- "I'll check this for you"
- "I'll investigate this"
- "I'll process the refund"
- "I'll issue a refund"
- "I'll check your account"
- "I'll check your tracking"
- "send me your order number"
- "give me your tracking number"
- or anything that implies you can perform those actions.

Historical responses show how support handled similar situations.
They are examples, NOT capabilities.

CONVERSATION RULES:

- Respond to the latest customer message first.
- Use previous conversation only when relevant.
- Acknowledge information the customer has already provided.
- Do not repeat a previous answer.
- If the customer says they already tried something, acknowledge it.
- If the customer changes topic, focus on the new topic.
- Speak naturally and conversationally.
- Do not sound like a database, API, workflow, or payload.
- Do not copy historical responses.
- Do not include Twitter signatures such as ^AM, ^GL, ^JJ, ^JZ, ^TG or ^CN.
- Do not invent order numbers, tracking numbers, prices, dates, policies, refunds, replacements, guarantees, URLs, or actions.
- Do not claim you performed an action.
- Do not ask for information merely because a historical AmazonHelp response asked another customer for it.
- If the issue requires access to information you do not have, clearly explain the limitation naturally.
- Do not repeatedly say "I'm sorry to hear that."
- Match the customer's language and style when possible.
- Keep the reply to one or two natural sentences.
- Do not mention AI, prompts, models, retrieval, evidence, or internal reasoning.
- Never use vague promises such as "let's get this sorted", "let's explore some options", "I can help you", "let's troubleshoot", or "let's see what we can do" without immediately providing a concrete, evidence-supported action or explanation.
- If you cannot provide a useful concrete action, state the limitation directly and briefly.
- When the customer has already tried a troubleshooting step, acknowledge it and do not recommend the same step again.

GROUNDING:

Historical examples can help you understand how similar cases were handled,
but similarity alone does NOT mean the evidence is sufficient.

Set evidence_sufficient to true only if the historical response contains
concrete information that directly supports the answer you are giving.

Otherwise set evidence_sufficient to false.

Return JSON only:

{{
  "reply": "natural customer-facing response",
  "evidence": ["brief description of evidence actually used"],
  "evidence_sufficient": false,
  "reason": "brief explanation"
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are Thunai, a natural, concise and grounded customer-support agent.",
            response_mime_type="application/json"
        )
    )

    content = response.text
    if not content:
        raise ValueError("Gemini returned an empty response")

    result = json.loads(content)

    result = apply_grounding_guard(
        result,
        customer_message,
        intent_result,
        historical_matches,
        conversation_history
    )

    required = {"reply", "evidence", "evidence_sufficient", "reason"}
    missing = required - set(result.keys())

    if missing:
        raise ValueError(f"Reply agent response missing fields: {sorted(missing)}")

    result["reply"] = clean_reply(result.get("reply", ""))
    result["evidence_sufficient"] = bool(result.get("evidence_sufficient", False))

    if not isinstance(result.get("evidence"), list):
        result["evidence"] = [str(result.get("evidence", ""))]

    return result

def apply_grounding_guard(
    result,
    customer_message,
    intent_result,
    historical_matches,
    conversation_history
):
    current_text = customer_message.lower().strip()
    intent = intent_result.get("intent", "other_unclear")

    previous_customer_text = " ".join(
        message.get("content", "").lower().strip()
        for message in conversation_history
        if message.get("role") == "customer"
    )

    reply_lower = str(result.get("reply", "")).lower()

    troubleshooting_exhausted = (
        intent == "account_access"
        and any(
            phrase in current_text
            for phrase in [
                "already cleared my cache",
                "cleared my cache",
                "cleared cache",
                "tried another browser",
                "tried a different browser",
                "tried another browser already",
                "tried a different browser already"
            ]
        )
        and any(
            phrase in previous_customer_text
            for phrase in [
                "reset my password",
                "reset the password",
                "changed my password"
            ]
        )
    )

    if troubleshooting_exhausted:
        result["reply"] = (
            "Got it — you've already reset your password, cleared your cache, "
            "and tried another browser. I don't have access to your account to "
            "determine what's preventing the login, so this will need to be reviewed by support."
        )
        result["evidence_sufficient"] = False
        result["evidence"] = [
            "Historical examples support basic login troubleshooting, but the customer has already tried those steps and Thunai cannot access the account."
        ]
        result["reason"] = (
            "The customer has exhausted the troubleshooting steps supported by the available historical evidence."
        )
        return result

    capability_patterns = [
        r"provide .*order number",
        r"give .*order number",
        r"send .*order number",
        r"provide .*tracking",
        r"give .*tracking",
        r"send .*tracking",
        r"i('?ll| will) check",
        r"i('?ll| will) look into",
        r"i('?ll| will) investigate",
        r"i('?ll| will) verify",
        r"i('?ll| will) process",
        r"i('?ll| will) issue",
        r"i('?ll| will) refund",
        r"i('?ll| will) replace",
        r"i('?ll| will) cancel",
        r"check this for you",
        r"look into this for you",
        r"check your account",
        r"check your order",
        r"check your payment",
        r"check your tracking",
        r"process your refund",
        r"issue your refund",
        r"access your account",
        r"let's get this sorted",
        r"let's troubleshoot",
        r"let's see what we can do",
        r"let's explore some options",
        r"i can help you explore",
        r"i can guide you through some steps",
        r"we can figure this out",
        r"let's get this resolved"
    ]

    unsupported_action = any(
        re.search(pattern, reply_lower)
        for pattern in capability_patterns
    )

    if unsupported_action:
        result["reply"] = safe_fallback(
            customer_message,
            intent
        )
        result["evidence_sufficient"] = False
        result["evidence"] = [
            "The historical examples may contain support actions, but Thunai does not have access to the customer's live account or transaction data."
        ]
        result["reason"] = (
            "The generated response implied an action or information access that Thunai cannot perform."
        )
        return result

    return result

def safe_fallback(customer_message, intent):
    text = customer_message.lower()

    if any(
        phrase in text
        for phrase in [
            "charged twice",
            "double charged",
            "duplicate charge"
        ]
    ):
        return (
            "I understand — you were charged twice for the same order. "
            "I don't have access to your current payment details, so I can't confirm or process the duplicate charge from here."
        )

    if intent == "refund_request":
        return (
            "I understand you're asking about a refund. "
            "I don't have access to your current payment or order details, so I can't confirm or process the refund from here."
        )

    if intent == "damaged_item":
        return (
            "I'm sorry you're dealing with a damaged item. "
            "I don't have access to your order details, so I can't confirm a replacement or refund from here."
        )

    if intent == "account_access":
        return (
            "I understand you're having trouble accessing your account. "
            "I can't access or modify your account from here, so I can't confirm the account status."
        )

    if intent == "prime_membership":
        return (
            "I understand you're asking about a Prime membership or charge. "
            "I don't have access to your current membership or billing details, so I can't confirm the charge from here."
        )

    if intent == "technical_support":
        return (
            "I understand you're having trouble with the device or service. "
            "I don't have access to the device or account, so I can't directly diagnose its current status."
        )

    if intent == "cancellation_request":
        return (
            "I understand you'd like to cancel the order. "
            "I don't have access to your current order details, so I can't confirm or process the cancellation from here."
        )

    return (
        "I understand the issue you're describing. "
        "I don't have access to your current account or order information, so I don't want to guess about the situation."
    )

def clean_reply(reply):
    reply = str(reply).strip()

    twitter_signatures = [
        "^AM",
        "^GL",
        "^JJ",
        "^JZ",
        "^TG",
        "^CN",
        "^XX"
    ]

    for signature in twitter_signatures:
        reply = reply.replace(signature, "")

    reply = re.sub(r"\s+", " ", reply)
    return reply.strip()

def test():
    scenarios = [
        {
            "name": "Duplicate charge",
            "message": "I was charged twice for the same order.",
            "intent": {
                "intent": "refund_request",
                "confidence": 0.96,
                "reason": "The customer reports a duplicate charge."
            }
        },
        {
            "name": "Damaged item",
            "message": "The screen on the item I received is cracked.",
            "intent": {
                "intent": "damaged_item",
                "confidence": 0.97,
                "reason": "The customer reports physical damage."
            }
        },
        {
            "name": "Account",
            "message": "I can't log into my account.",
            "intent": {
                "intent": "account_access",
                "confidence": 0.98,
                "reason": "The customer cannot access their account."
            }
        },
        {
            "name": "Prime charge",
            "message": "Why was I charged for Prime?",
            "intent": {
                "intent": "prime_membership",
                "confidence": 0.97,
                "reason": "The customer is asking about a Prime charge."
            }
        }
    ]

    historical_matches = []

    for scenario in scenarios:
        print("\n" + "=" * 60)
        print(scenario["name"])
        print("=" * 60)

        result = generate_reply(
            scenario["message"],
            scenario["intent"],
            historical_matches,
            []
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test()