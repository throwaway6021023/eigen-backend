import json
import uuid
from datetime import datetime
from typing import List

import redis.asyncio as redis
from redis.commands.search.field import TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from .llm_provider import CompletionMessage
from .settings import settings


class ChatStore:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    async def create_search_index(self):
        # Create a search index for contexts if it doesn't exist
        try:
            schema = (
                TextField("$.title", as_name="title"),
                TextField("$.content", as_name="content"),
            )

            await self.redis.ft("context-idx").create_index(
                schema,
                definition=IndexDefinition(
                    prefix=["context:"], index_type=IndexType.JSON
                ),
            )
        except Exception:
            # Index might already exist
            pass

    async def add_context(self, title: str, content: str) -> str:
        """Store a new context entry"""
        context_id = f"context:{uuid.uuid4()}"
        context_data = {
            "title": title,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.redis.json().set(context_id, "$", context_data)
        return context_id

    async def search_contexts(self, query: str) -> List[dict]:
        """Search through stored contexts"""
        formatted_query = f"(@title:{query}) | (@content:{query})"
        results = await self.redis.ft("context-idx").search(formatted_query)
        contexts = []
        for doc in results.docs:
            context_data = json.loads(doc.json)
            contexts.append(context_data)
        return contexts

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
