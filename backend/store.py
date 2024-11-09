import json
from typing import List

import redis.asyncio as redis

from .llm_provider import CompletionMessage
from .settings import settings


class ChatStore:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    async def add_message(self, session_id: str, message: CompletionMessage) -> None:
        """Add a message to the chat history."""
        key = f"chat:{session_id}"
        message_data = {"role": message.role, "content": message.content}
        await self.redis.rpush(key, json.dumps(message_data))
        # Optional: Set expiry time (e.g., 24 hours)
        await self.redis.expire(key, 24 * 60 * 60)

    async def get_messages(self, session_id: str) -> List[CompletionMessage]:
        """Retrieve all messages for a session."""
        key = f"chat:{session_id}"
        messages_raw = await self.redis.lrange(key, 0, -1)
        messages = []
        for msg_raw in messages_raw:
            msg_data = json.loads(msg_raw)
            messages.append(
                CompletionMessage(role=msg_data["role"], content=msg_data["content"])
            )
        return messages

    async def close(self):
        """Close the Redis connection."""
        await self.redis.close()
