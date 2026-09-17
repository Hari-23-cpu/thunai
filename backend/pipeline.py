from agents.intent_agent import classify_intent
from memory.retrieval_memory import HistoricalRetriever
from memory.conversation_memory import ConversationMemory
from agents.reply_agent import generate_reply
from agents.escalation_agent import decide_escalation

retriever = HistoricalRetriever()
memory = ConversationMemory(max_messages=10)

def run_support_pipeline(conversation_id, customer_message, top_k=3):
    history = memory.get_history(conversation_id)
    memory.add_message(conversation_id, "customer", customer_message)

    intent_input = customer_message
    if history:
        intent_input = (
            "PREVIOUS CONVERSATION:\n"
            + "\n".join(
                f"{message['role']}: {message['content']}"
                for message in history
            )
            + "\n\nCURRENT CUSTOMER MESSAGE:\n"
            + customer_message
        )

    intent_result = classify_intent(intent_input)

    retrieval_query = customer_message
    if history:
        recent_customer_messages = [
            message["content"]
            for message in history
            if message["role"] == "customer"
        ][-3:]
        retrieval_query = " ".join(
            recent_customer_messages + [customer_message]
        )

    historical_matches = retriever.retrieve(
        retrieval_query,
        top_k=top_k
    )

    reply_result = generate_reply(
        customer_message,
        intent_result,
        historical_matches,
        conversation_history=history
    )

    escalation_result = decide_escalation(
        customer_message,
        intent_result,
        reply_result,
        historical_matches
    )

    memory.add_message(
        conversation_id,
        "agent",
        reply_result["reply"]
    )

    return {
        "conversation_id": conversation_id,
        "customer_message": customer_message,
        "intent": intent_result,
        "historical_matches": historical_matches,
        "reply": reply_result,
        "escalation": escalation_result
    }