from memory.conversation_memory import ConversationMemory

memory = ConversationMemory()

conversation_id = "test_001"

memory.add_message(
    conversation_id,
    "customer",
    "My order says delivered but I never received it"
)

memory.add_message(
    conversation_id,
    "agent",
    "I'm sorry to hear that your order is marked as delivered but you haven't received it."
)

memory.add_message(
    conversation_id,
    "customer",
    "Okay give me the support email."
)

print("CONVERSATION HISTORY")
print("--------------------")
print(memory.get_context(conversation_id))