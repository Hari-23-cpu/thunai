import json
from agents.intent_agent import classify_intent
from memory.retrieval_memory import HistoricalRetriever
from memory.conversation_memory import ConversationMemory
from agents.reply_agent import generate_reply
from agents.escalation_agent import decide_escalation

retriever = HistoricalRetriever()
memory = ConversationMemory(max_messages=10)

def run_support_agent(conversation_id, customer_message, top_k=3):
    history = memory.get_history(conversation_id)

    memory.add_message(
        conversation_id,
        "customer",
        customer_message
    )

    intent_input = customer_message

    if history:
        intent_input = (
            "PREVIOUS CONVERSATION:\n"
            + memory.get_context(conversation_id)
            + "\n\nCURRENT CUSTOMER MESSAGE:\n"
            + customer_message
        )

    intent_result = classify_intent(intent_input)

    historical_matches = retriever.retrieve(
        customer_message,
        top_k=top_k
    )

    reply_result = generate_reply(
        customer_message,
        intent_result,
        historical_matches
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
        "customer_message": customer_message,
        "intent": intent_result,
        "historical_matches": historical_matches,
        "reply": reply_result,
        "escalation": escalation_result
    }

def run_conversation():
    conversation_id = "conversation_001"

    print("AmazonHelp AI Support Agent")
    print("Type 'exit' to end the conversation.")
    print()

    while True:
        customer_message = input("Customer: ").strip()

        if customer_message.lower() == "exit":
            break

        if not customer_message:
            continue

        try:
            result = run_support_agent(
                conversation_id,
                customer_message
            )

            print()
            print("Agent:", result["reply"]["reply"])
            print("Decision:", result["escalation"]["decision"])
            print()

        except Exception as e:
            print()
            print("Agent error:", e)
            print()

if __name__ == "__main__":
    run_conversation()