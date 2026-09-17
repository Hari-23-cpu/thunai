def decide_escalation(customer_message, intent_result, reply_result, historical_matches):
    intent = intent_result.get("intent", "other_unclear")
    intent_confidence = float(intent_result.get("confidence", 0))
    evidence_sufficient = bool(reply_result.get("evidence_sufficient", False))

    similarities = [
        float(match.get("similarity", 0))
        for match in historical_matches
        if match.get("similarity") is not None
    ]
    best_similarity = max(similarities, default=0)

    if intent == "other_unclear":
        return {
            "decision": "ESCALATE",
            "reason": "The customer request is unclear or does not map confidently to a supported intent.",
            "confidence": round(intent_confidence, 2)
        }

    if intent_confidence < 0.70:
        return {
            "decision": "ESCALATE",
            "reason": "Intent confidence is below the auto-handling threshold.",
            "confidence": round(intent_confidence, 2)
        }

    if not historical_matches:
        return {
            "decision": "ESCALATE",
            "reason": "No relevant historical AmazonHelp resolution was retrieved.",
            "confidence": round(best_similarity, 2)
        }

    if best_similarity < 0.30:
        return {
            "decision": "ESCALATE",
            "reason": "Retrieved historical evidence is not sufficiently similar to the customer's request.",
            "confidence": round(best_similarity, 2)
        }

    if not evidence_sufficient:
        return {
            "decision": "ESCALATE",
            "reason": "The reply agent could not establish that the historical evidence was sufficient to safely answer the customer.",
            "confidence": round(best_similarity, 2)
        }

    return {
        "decision": "AUTO_HANDLE",
        "reason": "The intent is clear and confident, relevant historical evidence was retrieved, and the reply is supported by that evidence.",
        "confidence": round(min(intent_confidence, best_similarity), 2)
    }