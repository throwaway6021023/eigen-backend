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
    component: Literal["contact_form", "open_roles", "team_members", "case_study_quote"]
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


class RenderOpenRolesTool(BaseModel):
    @staticmethod
    def run() -> str:
        return RenderComponentPayload(
            component="open_roles",
            props={
                "roles": {
                    "Engineering": ["Senior Engineer", "Engineering Manager"],
                    "Product": ["Product Manager"],
                }
            },
        ).model_dump_json()


class RenderTeamMembersTool(BaseModel):
    @staticmethod
    def run() -> str:
        return RenderComponentPayload(
            component="team_members",
            props={
                "managing_partners": ["Cameron", "Josh"],
                "advisors": ["John", "Jane"],
            },
        ).model_dump_json()


class RenderCaseStudyQuoteTool(BaseModel):
    @staticmethod
    def run() -> str:
        return RenderComponentPayload(
            component="case_study_quote",
            props={
                "quote": "Eigen is our go-to partner for building AI solutions!",
                "url": "https://eigen.net",
            },
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
            "description": "Render a contact form that allows users to get in touch with Eigen. The form can be prefilled with user information if available.",
            "parameters": RenderContactFormTool.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_open_roles",
            "description": "Display current job openings at Eigen. Shows a curated list of open positions across different departments, helping potential candidates find relevant opportunities.",
            "parameters": RenderOpenRolesTool.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_team_members",
            "description": "Show Eigen's leadership team, including managing partners Cameron and Josh, and optionally display the advisory board. Helps users understand the expertise and experience of Eigen's leadership.",
            "parameters": RenderTeamMembersTool.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_case_study_quote",
            "description": "Display a relevant customer quote and link to a case study, filtered by industry or focus area. Helps demonstrate Eigen's impact and expertise through real client success stories.",
            "parameters": RenderCaseStudyQuoteTool.model_json_schema(),
        },
    },
]

TOOL_FNS = {
    "lookup_context": LookupContextTool,
}

COMPONENT_FNS = {
    "render_contact_form": RenderContactFormTool,
    "render_open_roles": RenderOpenRolesTool,
    "render_team_members": RenderTeamMembersTool,
    "render_case_study_quote": RenderCaseStudyQuoteTool,
}
