class ConversationMemory:
    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.conversations = {}

    def create_conversation(self, conversation_id):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

    def add_message(self, conversation_id, role, content):
        self.create_conversation(conversation_id)
        self.conversations[conversation_id].append({
            "role": role,
            "content": content
        })
        self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_messages:]

    def get_history(self, conversation_id):
        return self.conversations.get(conversation_id, [])

    def get_context(self, conversation_id):
        history = self.get_history(conversation_id)
        return "\n".join(
            f"{message['role']}: {message['content']}"
            for message in history
        )

    def clear_conversation(self, conversation_id):
        self.conversations.pop(conversation_id, None)