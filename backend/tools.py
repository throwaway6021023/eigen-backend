import json
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .store import ChatStore


class LookupContextTool(BaseModel):
    query: str = Field(description="The search query to find relevant context.")

    @staticmethod
    async def run(query: str, store: "ChatStore") -> str:
        relevant_contexts = await store.search_contexts(query)
        return json.dumps(relevant_contexts)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_context",
            "description": "Look up relevant context based on a search query. The context includes Eigen's capabilities, case studies, and other relevant information related to prior clients and projects.",
            "parameters": LookupContextTool.model_json_schema(),
        },
    }
]

TOOLS_FNS = {
    "lookup_context": LookupContextTool,
}
