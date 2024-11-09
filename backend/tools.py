import json
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .store import ChatStore


class LookupContextTool(BaseModel):
    query: str = Field(description="The search query to find relevant context.")

    @staticmethod
    async def run(query: str, store: "ChatStore") -> str:
        relevant_contexts = await store.search_contexts(query)
        return json.dumps(relevant_contexts)


class RenderComponentPayload(BaseModel):
    component: Literal["contact_form"]
    props: dict


class RenderContactFormTool(BaseModel):
    name: str | None = Field(description="The name to prefill in the contact form.")
    email: str | None = Field(description="The email to prefill in the contact form.")
    message: str | None = Field(
        description="The message to prefill in the contact form."
    )

    @staticmethod
    def run(name: str, email: str, message: str) -> str:
        return RenderComponentPayload(
            component="contact_form",
            props={"name": name, "email": email, "message": message},
        ).model_dump_json()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_context",
            "description": "Look up relevant context based on a search query. The context includes Eigen's capabilities, case studies, and other relevant information related to prior clients and projects.",
            "parameters": LookupContextTool.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_contact_form",
            "description": "Render an empty contact form. It may be prefilled with information if the user provided it sometime during the chat.",
            "parameters": RenderContactFormTool.model_json_schema(),
        },
    },
]

TOOL_FNS = {
    "lookup_context": LookupContextTool,
}
COMPONENT_FNS = {
    "render_contact_form": RenderContactFormTool,
}
